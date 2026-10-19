"""LiteLLM/OpenRouter baselines for the hsom benchmark.

Two planners mirror the same level-by-level decision procedure as Jev:

- ``StructuredPlanner`` constrains each choice with a JSON Schema enum.
- ``LogprobPlanner`` scores numbered options by reading the model's
  log-probabilities and picks the highest-scoring option (ties go to the
  earliest option in tree order).

Both use LiteLLM with an OpenRouter model and ``OPENROUTER_API_KEY``.  They
never execute a command; callers compare the planned argv themselves.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field

from hsom.config import (
    EnvConfig,
    effective_threshold,
    node_risk,
    node_slots,
)
from hsom.discovery import discover
from hsom.dispatcher import PlanOutcome, PlannedAction

NONE_LABEL = "none_of_the_above"
OFF_LABEL = "off"
YES_NO = ("no", "yes")
MAX_LOGPROB_OPTIONS = 20


class BaselineError(Exception):
    """Raised when a baseline call fails or returns an unusable answer."""


@dataclass
class Usage:
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0.0
    calls: int = 0
    fallbacks: int = 0
    raw: list[dict] = field(default_factory=list)

    def add(self, response, latency_ms: float) -> None:
        if response is not None:
            usage = getattr(response, "usage", None)
            if usage is not None:
                in_tok = getattr(usage, "prompt_tokens", None)
                if in_tok is None:
                    in_tok = getattr(usage, "input_tokens", None)
                out_tok = getattr(usage, "completion_tokens", None)
                if out_tok is None:
                    out_tok = getattr(usage, "output_tokens", None)
                if in_tok is not None:
                    self.input_tokens = (self.input_tokens or 0) + int(in_tok)
                if out_tok is not None:
                    self.output_tokens = (self.output_tokens or 0) + int(out_tok)
            model = getattr(response, "model", None)
            if model:
                self.model = model
        self.latency_ms += latency_ms
        self.calls += 1


def _litellm():
    try:
        import litellm
    except ImportError as e:  # pragma: no cover - exercised via monkeypatch
        raise BaselineError(
            "LiteLLM is not installed; install the benchmark extra "
            "(pip install -e '.[benchmark]')") from e
    # LiteLLM is noisy by default; benchmark output should stay readable.
    litellm.suppress_debug_info = True
    return litellm


def _content(response) -> str:
    try:
        message = response.choices[0].message
    except (AttributeError, IndexError) as e:
        raise BaselineError("LiteLLM response has no message") from e
    parsed = getattr(message, "parsed", None)
    if parsed is not None:
        return parsed if isinstance(parsed, str) else json.dumps(parsed)
    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise BaselineError("LiteLLM returned an empty answer")
    return content.strip()


def _json_object(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Tolerate a fenced object, which some OpenRouter models still emit.
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise BaselineError(f"baseline did not return JSON: {text[:120]!r}")
        try:
            data = json.loads(text[start:end + 1])
        except json.JSONDecodeError as e:
            raise BaselineError(f"baseline returned invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise BaselineError("baseline JSON answer must be an object")
    return data


def _messages(instructions: str, options: list[str], *, numbered: bool) -> list[dict]:
    if numbered:
        listing = "\n".join(f"{i}. {opt}" for i, opt in enumerate(options))
        user = (
            f"{instructions}\n\nOptions:\n{listing}\n\n"
            "Answer with the number of the single best option only.")
        system = "You are a strict shell-command router. Answer with one number."
    else:
        user = instructions
        system = (
            "You are a strict shell-command router. Choose exactly one option "
            "from the provided enum and return only the requested JSON object.")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _option_list(lines: list[str]) -> list[str]:
    # Keep option order deterministic: tree order, then none/off.
    seen: set[str] = set()
    out: list[str] = []
    for item in lines:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _prompt_for(config: EnvConfig, request: str, cwd: str) -> str:
    return (
        "Route this user request to one allowlisted shell action.\n"
        f"Request: {request}\n"
        f"Working directory: {cwd}\n"
        "Choose only from the options presented for each level.")


class _BasePlanner:
    name = "baseline"

    def __init__(self, model: str, *, api_key: str | None = None,
                 temperature: float = 0.0, timeout: float = 60.0,
                 max_options: int = MAX_LOGPROB_OPTIONS):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout
        self.max_options = max_options

    def plan(self, config: EnvConfig, request: str, cwd: str) -> tuple[PlanOutcome, Usage]:
        usage = Usage()
        try:
            outcome = self._plan(config, request, cwd, usage)
        except BaselineError:
            raise
        except Exception as e:  # provider/network/parsing failures
            raise BaselineError(f"{type(e).__name__}: {e}") from e
        return outcome, usage

    def _plan(self, config: EnvConfig, request: str, cwd: str,
              usage: Usage) -> PlanOutcome:
        prompt = _prompt_for(config, request, cwd)

        cmd_names = [c.name for c in config.commands]
        choice = self._choose(
            f"{prompt}\n\nWhich command should handle the request?",
            cmd_names + [NONE_LABEL], usage)
        if choice == NONE_LABEL:
            return PlanOutcome(False, None, "none_of_the_above at command layer")
        cmd = config.get_command(choice)
        if cmd is None:
            return PlanOutcome(False, None, f"unknown command '{choice}'")

        sub = None
        if cmd.subcommands:
            sub_names = [s.name for s in cmd.subcommands]
            sub_choice = self._choose(
                f"{prompt}\n\nWhich '{cmd.name}' subcommand should handle the request?",
                sub_names + [NONE_LABEL], usage)
            if sub_choice == NONE_LABEL:
                if cmd.argv is None:
                    return PlanOutcome(False, None,
                                       f"'{cmd.name}' needs a subcommand")
            else:
                sub = next((s for s in cmd.subcommands if s.name == sub_choice),
                           None)
                if sub is None:
                    return PlanOutcome(False, None,
                                       f"unknown subcommand '{sub_choice}'")

        node = sub if sub is not None else cmd
        node_key = cmd.name if sub is None else f"{cmd.name}.{sub.name}"

        flags: list[str] = []
        values: dict[str, str] = {}
        for flag in node.flags:
            if flag.values:
                options = [OFF_LABEL, *flag.values]
                picked = self._choose(
                    f"{prompt}\n\n{flag.description}. "
                    f"Which value should the flag '{flag.name}' use?",
                    options, usage)
                if picked != OFF_LABEL:
                    flags.append(flag.name)
                    values[flag.name] = picked
            else:
                picked = self._choose(
                    f"{prompt}\n\n{flag.description}. "
                    f"Should the flag '{flag.name}' be enabled?",
                    list(YES_NO), usage)
                if picked == "yes":
                    flags.append(flag.name)

        paths: dict[str, str] = {}
        for slot in node_slots(node):
            try:
                candidates = discover(slot, cwd)
            except ValueError as e:
                return PlanOutcome(False, None, f"candidate discovery failed: {e}")
            if not candidates:
                if slot.optional:
                    continue
                return PlanOutcome(False, None,
                                   f"no {node_key}.{slot.name} candidates")
            optional = slot.optional
            options = candidates + ([NONE_LABEL] if optional else [])
            desc = slot.description or f"a value for {slot.name}"
            picked = self._choose(
                f"{prompt}\n\n{desc}. Which {slot.name} should be used?",
                options, usage)
            if picked == NONE_LABEL:
                if optional:
                    continue
                return PlanOutcome(False, None,
                                   f"none_of_the_above at {node_key}.{slot.name}")
            if picked not in candidates:
                return PlanOutcome(False, None,
                                   f"baseline selected {picked!r}, not a candidate")
            paths[slot.name] = picked

        risk = node_risk(config, cmd, sub)
        bar, source = effective_threshold(config, cmd, sub, risk)
        action = PlannedAction(
            command=cmd.name,
            subcommand=(sub.name if sub is not None else None),
            flags=tuple(flags),
            flag_values=dict(values),
            paths=dict(paths),
            path=next(iter(paths.values())) if len(paths) == 1 else None,
            confidence=1.0,
            risk=risk,
            threshold=bar,
            threshold_source=source,
        )
        return PlanOutcome(True, action, "ok", 1.0)

    def _choose(self, instructions: str, options: list[str],
                usage: Usage) -> str:
        raise NotImplementedError


class StructuredPlanner(_BasePlanner):
    """Ask a model for a JSON object constrained to an enum of options."""

    name = "structured"

    def _choose(self, instructions: str, options: list[str],
                usage: Usage) -> str:
        litellm = _litellm()
        schema = {
            "type": "object",
            "properties": {"choice": {"type": "string", "enum": options}},
            "required": ["choice"],
            "additionalProperties": False,
        }
        started = time.perf_counter()
        response = litellm.completion(
            model=self.model,
            messages=_messages(instructions, options, numbered=False),
            timeout=self.timeout,
            api_key=self.api_key,
            reasoning_effort="none",
            max_tokens=128,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "benchmark_choice",
                    "strict": True,
                    "schema": schema,
                },
            },
            extra_body={"provider": {"require_parameters": True}},
        )
        usage.add(response, (time.perf_counter() - started) * 1000.0)
        data = _json_object(_content(response))
        choice = data.get("choice")
        if choice not in options:
            raise BaselineError(f"structured answer {choice!r} is not an option")
        return choice


class LogprobPlanner(_BasePlanner):
    """Score numbered options from ``top_logprobs`` and pick the best."""

    name = "logprobs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logprobs_supported = True

    def _choose(self, instructions: str, options: list[str],
                usage: Usage) -> str:
        if len(options) == 1:
            return options[0]
        if len(options) <= self.max_options:
            return self._choose_chunk(instructions, options, usage)
        # More options than a single top_logprobs window: run a deterministic
        # tournament over chunks, then choose among the chunk winners.
        winners: list[str] = []
        for start in range(0, len(options), self.max_options):
            chunk = options[start:start + self.max_options]
            winners.append(self._choose_chunk(instructions, chunk, usage))
        return self._choose(instructions, _option_list(winners), usage)

    def _choose_chunk(self, instructions: str, options: list[str],
                      usage: Usage) -> str:
        litellm = _litellm()
        messages = _messages(instructions, options, numbered=True)
        if not self._logprobs_supported:
            return self._greedy(litellm, messages, options, usage)
        started = time.perf_counter()
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                max_tokens=1,
                timeout=self.timeout,
                api_key=self.api_key,
                reasoning_effort="none",
                logprobs=True,
                top_logprobs=min(MAX_LOGPROB_OPTIONS, max(1, len(options))),
                extra_body={"provider": {"require_parameters": True}},
            )
        except Exception as e:
            if _unsupported_logprobs(e):
                self._logprobs_supported = False
                return self._greedy(litellm, messages, options, usage)
            raise
        usage.add(response, (time.perf_counter() - started) * 1000.0)
        scores = self._label_scores(response, len(options))
        if not scores:
            # Some OpenRouter routes omit logprobs.  Fall back to the greedy
            # answer rather than losing the whole baseline case.
            content = getattr(response.choices[0].message, "content", "") or ""
            content = content.strip()
            if content.isdigit() and 0 <= int(content) < len(options):
                usage.fallbacks += 1
                return options[int(content)]
            raise BaselineError("model returned no usable label logprobs")
        best = max(scores, key=lambda kv: (kv[1], -kv[0]))
        return options[best[0]]

    def _greedy(self, litellm, messages: list[dict], options: list[str],
                usage: Usage) -> str:
        started = time.perf_counter()
        response = litellm.completion(
            model=self.model,
            messages=messages,
            max_tokens=32,
            timeout=self.timeout,
            api_key=self.api_key,
            reasoning_effort="none",
        )
        usage.add(response, (time.perf_counter() - started) * 1000.0)
        usage.fallbacks += 1
        content = getattr(response.choices[0].message, "content", "") or ""
        content = content.strip().rstrip(".")
        if content.isdigit() and 0 <= int(content) < len(options):
            return options[int(content)]
        raise BaselineError(f"model returned no usable option number: {content!r}")

    @staticmethod
    def _label_scores(response, n_options: int) -> list[tuple[int, float]]:
        try:
            content = response.choices[0].logprobs.content
        except (AttributeError, IndexError):
            return []
        if not content:
            return []
        first = content[0]
        top = getattr(first, "top_logprobs", None)
        if top is None and isinstance(first, dict):
            top = first.get("top_logprobs")
        top = top or []
        scores: dict[int, float] = {}
        for entry in top:
            if isinstance(entry, dict):
                token = entry.get("token")
                logprob = entry.get("logprob")
            else:
                token = getattr(entry, "token", None)
                logprob = getattr(entry, "logprob", None)
            if token is None or logprob is None:
                continue
            token = str(token).strip()
            if not token.isdigit():
                continue
            idx = int(token)
            if 0 <= idx < n_options:
                scores[idx] = max(scores.get(idx, -math.inf), float(logprob))
        return sorted(scores.items(), key=lambda kv: -kv[1])


def _unsupported_logprobs(error: Exception) -> bool:
    text = str(error).lower()
    return ("logprob" in text or "no endpoints" in text
            or "not supported" in text)


def make_planner(system: str, **kwargs) -> _BasePlanner:
    if system == "structured":
        return StructuredPlanner(**kwargs)
    if system == "logprobs":
        return LogprobPlanner(**kwargs)
    raise BaselineError(f"unknown baseline system {system!r}")
