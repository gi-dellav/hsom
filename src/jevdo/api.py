"""High-level Python library API for jevdo.

The :class:`Harness` class wraps config loading, Jev dispatch, argv
resolution, execution (with confirmation hook), multi-step chaining and
eval — the same machinery the ``jevdo`` CLI uses — in an importable,
programmatic form.

Example:
    from jevdo import Harness

    h = Harness(env="environment.toml")
    outcome = h.plan("brief git history")
    if outcome.ok:
        print(h.resolve(outcome.action))

    result = h.run("run tests", max_steps=2, dry_run=True)
    print(result.stop_reason, [s.argv for s in result.steps])

    # Write-risk commands never prompt on stdin here. Pass ``on_confirm``
    # to approve them programmatically; the default is fail-closed
    # (auto-decline), mirroring the CLI's non-tty behaviour.
    result = h.run("stage readme", on_confirm=lambda action, argv: True)

``get_cwd()`` is a method so users can override the working directory
dynamically — subclass ``Harness`` or assign ``h.get_cwd = lambda: ...``,
or pass ``get_cwd=...`` at construction. Per-call ``cwd=...`` always wins
over it.
"""

from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from jevdo.config import ConfigError, EnvConfig, PROVIDERS, load_config

#: Confirmation hook: receives the planned action + resolved argv,
#: returns True to approve execution, False to decline.
OnConfirm = Callable[..., bool]


@dataclass(frozen=True)
class RunResult:
    """Outcome of :meth:`Harness.run`."""

    steps: tuple = field(default_factory=tuple)
    stop_reason: str = ""
    ok: bool = False
    declined: bool = False
    reason: str = ""
    confidence: float = 0.0

    @property
    def argv_list(self) -> list[list[str]]:
        return [list(s.argv) for s in self.steps]

    @property
    def returncode(self) -> int:
        if not self.steps:
            return 0
        return self.steps[-1].returncode


def apply_provider_overrides(config: EnvConfig, provider=None,
                             base_url=None) -> EnvConfig:
    """Fold provider/base_url overrides into a config. Returns new config."""
    if provider is None and base_url is None:
        return config
    if provider is not None and provider not in PROVIDERS:
        raise ConfigError(f"--provider must be one of {PROVIDERS}")
    if base_url is not None:
        base_url = base_url.strip().rstrip("/")
        if not base_url or not (base_url.startswith("http://")
                                or base_url.startswith("https://")):
            raise ConfigError("--base-url must start with http:// or https://")
    return dataclasses.replace(
        config,
        provider=provider if provider is not None else config.provider,
        base_url=base_url if base_url is not None else config.base_url,
    )


def _coerce_config(env) -> EnvConfig:
    """Accept a path, dict, EnvConfig (or None -> default path)."""
    if isinstance(env, EnvConfig):
        return env
    if isinstance(env, dict):
        return EnvConfig.from_dict(env)
    if env is None:
        return load_config("environment.toml")
    # str | PathLike
    return load_config(str(env))


class Harness:
    """Stateful library entry point holding config + run defaults.

    Parameters mirror the CLI flags plus library hooks:

    - ``env``: ``environment.toml`` path, :class:`EnvConfig`, TOML-shaped
      ``dict``, or ``None`` (loads ``"environment.toml"``).
    - ``cwd``: default working directory for discovery + execution.
    - ``get_cwd``: optional ``Callable[[], str]`` consulted by
      :meth:`get_cwd`. Assign ``h.get_cwd = ...`` later or subclass to
      change it dynamically.
    - ``min_confidence``, ``max_steps``, ``max_history``,
      ``continue_threshold``, ``temperature``, ``provider``, ``base_url``:
      instance defaults; every per-call argument wins over these.
    - ``api_key``: explicit key forwarded to the client factory.
    - ``client``: persistent Jev client (e.g. a fake in tests). When
      ``None`` a client is created per call and closed afterwards.
    """

    def __init__(
        self,
        env: str | os.PathLike | EnvConfig | dict | None = "environment.toml",
        *,
        cwd: str | os.PathLike = ".",
        min_confidence: float | None = None,
        max_steps: int | None = None,
        max_history: int | None = None,
        continue_threshold: float | None = None,
        temperature: float | None = None,
        provider: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        client=None,
        get_cwd: Callable[[], str] | None = None,
    ):
        config = _coerce_config(env)
        config = apply_provider_overrides(config, provider, base_url)
        self.config = config
        self._cwd = str(cwd or ".")
        self._cwd_fn = get_cwd
        self._min_confidence = min_confidence
        self._max_steps = max_steps
        self._max_history = max_history
        self._continue_threshold = continue_threshold
        self._temperature = temperature
        self._api_key = api_key
        self._timeout = timeout
        self._client = client
        self._owned_client = None

    # -- cwd ---------------------------------------------------------
    def get_cwd(self) -> str:
        """Return the working directory for the next call.

        Override dynamically by passing ``get_cwd=...`` at construction,
        calling :meth:`set_cwd_fn`, assigning ``h.get_cwd = lambda: ...``,
        or subclassing. A per-call ``cwd=...`` argument always wins over
        this.
        """
        fn = self.__dict__.get("_cwd_fn")
        if callable(fn):
            return str(fn())
        return self._cwd

    def set_cwd(self, cwd: str | os.PathLike) -> None:
        """Update the default working directory."""
        self._cwd = str(cwd or ".")

    def set_cwd_fn(self, fn: Callable[[], str] | None) -> None:
        """Install/replace the dynamic cwd provider (None clears it)."""
        self._cwd_fn = fn

    def _resolve_cwd(self, cwd: str | os.PathLike | None) -> str:
        if cwd is not None:
            return str(cwd)
        override = self.__dict__.get("get_cwd")
        if override is not None:
            # User replaced the method: h.get_cwd = lambda: ... (or a string).
            if callable(override):
                return str(override())
            return str(override)
        return str(self.get_cwd())

    # -- lifecycle ---------------------------------------------------
    def close(self) -> None:
        if self._owned_client is not None:
            try:
                self._owned_client.close()
            except Exception:
                pass
            self._owned_client = None

    def __enter__(self) -> "Harness":
        if self._client is None and self._owned_client is None:
            from jevdo.client import create_client
            try:
                self._owned_client = create_client(
                    self.config, api_key=self._api_key,
                    timeout=self._timeout)
            except Exception:
                self._owned_client = None
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _active_client(self, override=None):
        if override is not None:
            return override, False
        if self._client is not None:
            return self._client, False
        if self._owned_client is not None:
            return self._owned_client, False
        return None, True  # dispatcher creates + closes per call

    def _ensure_api_key(self, client, execute_fn) -> None:
        if client is not None or execute_fn is not None:
            return
        if self._api_key is not None and self._api_key.strip():
            return
        from jevdo.client import has_api_key
        if not has_api_key(self.config):
            raise ConfigError(
                "no API key found: set TYPESAFE_API_KEY or OPENROUTER_API_KEY")

    # -- single-shot -------------------------------------------------
    def plan(self, request: str, *, cwd=None, min_confidence=None,
             temperature=None, client=None):
        """Plan one step. Returns :class:`PlanOutcome` (max_steps=1)."""
        outcome, _q, _c, _r = self.plan_full(
            request, cwd=cwd, min_confidence=min_confidence,
            temperature=temperature, client=client)
        return outcome

    def plan_full(self, request: str, *, cwd=None, min_confidence=None,
                  temperature=None, client=None):
        """Like :meth:`plan` but returns ``(outcome, questions, context,
        response)`` for inspection / logging."""
        from jevdo.dispatcher import dispatch
        cwd_s = self._resolve_cwd(cwd)
        eff_conf = min_confidence if min_confidence is not None else self._min_confidence
        eff_temp = temperature if temperature is not None else self._temperature
        eff_client, _ = self._active_client(client)
        self._ensure_api_key(eff_client, None)
        return dispatch(
            self.config, request, cwd_s, client=eff_client,
            min_confidence=eff_conf, max_steps=1, temperature=eff_temp)

    def resolve(self, action, *, cwd=None) -> list[str]:
        """Build argv for a planned action. Raises ExecutionError."""
        from jevdo.executor import resolve_argv
        return list(resolve_argv(self.config, action, self._resolve_cwd(cwd)))

    def execute(self, action, *, cwd=None, dry_run: bool = False,
                timeout: float | None = None):
        """Execute a planned action. Returns ExecutionResult."""
        from jevdo.executor import execute
        return execute(self.config, action, self._resolve_cwd(cwd),
                       dry_run=dry_run,
                       timeout=timeout if timeout is not None else self._timeout)

    # -- multi-step --------------------------------------------------
    def run(
        self,
        request: str,
        *,
        cwd=None,
        max_steps: int | None = None,
        max_history: int | None = None,
        continue_threshold: float | None = None,
        min_confidence: float | None = None,
        temperature: float | None = None,
        dry_run: bool = False,
        on_confirm: OnConfirm | None = None,
        execute_fn=None,
        stop_on_error: bool = True,
        repeat_guard: bool = True,
        logger=None,
        log_path: str | os.PathLike | None = None,
        client=None,
    ) -> RunResult:
        """Plan (+ optionally execute) up to ``max_steps`` chained steps.

        - ``dry_run``: resolve argv only, never execute, never prompt.
        - ``on_confirm``: ``(action, argv) -> bool`` gate for
          ``write``/``destructive`` steps. ``None`` (default) is
          fail-closed: those steps are declined without prompting.
        - ``execute_fn``: ``(action, cwd) -> (argv, rc, stdout, stderr)``
          injection for tests; defaults to real subprocess execution.
        - ``stop_on_error``: stop after the first non-zero exit (default).
        - ``repeat_guard``: re-plan once when a step repeats the previous
          argv verbatim instead of executing a duplicate.
        - ``logger`` / ``log_path``: opt-in JSONL run logging.
        """
        from jevdo import runlog
        from jevdo.config import effective_continue_threshold
        from jevdo.dispatcher import (
            REPEAT_HINT_STATE, continue_info, continue_requested, dispatch,
            history_entry,
        )
        from jevdo.executor import ExecutionError, resolve_argv

        cwd_s = self._resolve_cwd(cwd)
        budget = max_steps if max_steps is not None else self._max_steps
        if budget is None:
            budget = self.config.max_steps
        budget = max(1, min(10, budget))
        eff_conf = min_confidence if min_confidence is not None else self._min_confidence
        eff_temp = temperature if temperature is not None else self._temperature
        eff_hist = max_history if max_history is not None else self._max_history
        eff_cont = (continue_threshold if continue_threshold is not None
                    else self._continue_threshold)
        bar, bar_source = effective_continue_threshold(
            self.config, cli_override=eff_cont)
        eff_client, _ = self._active_client(client)
        self._ensure_api_key(eff_client, execute_fn)
        if dry_run and execute_fn is None:
            # dry-run never needs a live client for execution, but planning
            # still does (unless a fake client is injected).
            pass

        own_logger = None
        if log_path is not None and logger is None:
            logger = own_logger = runlog.JsonlLogger(str(log_path))
        try:
            from jevdo import executor as _executor

            steps: list = []
            history: list[dict] = []
            for i in range(budget):
                ask_continue = budget > 1 and i + 1 < budget
                outcome, _q, context, response = dispatch(
                    self.config, request, cwd_s, client=eff_client,
                    min_confidence=eff_conf, history=history or None,
                    max_steps=budget, max_history=eff_hist,
                    allow_continue=ask_continue, temperature=eff_temp,
                    step_index=i)
                if logger is not None:
                    logger.log(runlog.plan_event(
                        i + 1, request, cwd_s, outcome, context,
                        continue_asked=ask_continue,
                        continue_value=continue_info(response),
                        continue_threshold=bar,
                        continue_threshold_source=bar_source,
                        max_steps=budget, max_history=eff_hist,
                        history_len=len(history)))
                if not outcome.ok or outcome.action is None:
                    if logger is not None:
                        logger.log(runlog.result_event(
                            i + 1, error=outcome.reason,
                            stop_reason=outcome.reason))
                    if i == 0:
                        return RunResult(steps=(), stop_reason=(
                            f"abstained: {outcome.reason}"), ok=False)
                    ok = all(s.returncode == 0 for s in steps)
                    return RunResult(steps=tuple(steps), stop_reason=(
                        f"stop: {outcome.reason}"), ok=ok)
                action = outcome.action
                try:
                    preview = list(resolve_argv(self.config, action, cwd_s))
                except ExecutionError as e:
                    if logger is not None:
                        logger.log(runlog.result_event(i + 1, error=str(e)))
                    return RunResult(steps=tuple(steps), stop_reason=str(e),
                                     ok=False)

                if repeat_guard and history and preview == list(
                        history[-1].get("argv") or []):
                    retried = self._retry_after_repeat(
                        request, cwd_s, history=history, max_steps=budget,
                        max_history=eff_hist, min_confidence=eff_conf,
                        temperature=eff_temp, step_index=i,
                        ask_continue=ask_continue, prev_argv=preview,
                        logger=logger, client=eff_client)
                    if retried is None:
                        if logger is not None:
                            logger.log(runlog.result_event(
                                i + 1, preview,
                                stop_reason=(f"stop: step {i+1} repeats step "
                                             f"{i} ({' '.join(preview)}); not "
                                             "executing a duplicate")))
                        ok = all(s.returncode == 0 for s in steps)
                        # Record the repeated step as not-executed: keep prior
                        # steps only, matching dispatch_sequence honesty.
                        return RunResult(
                            steps=tuple(steps),
                            stop_reason=(f"stop: step {i+1} repeats step {i} "
                                         f"({' '.join(preview)}); not executing "
                                         "a duplicate"),
                            ok=ok)
                    outcome, context, response, preview, action = retried

                if dry_run:
                    from jevdo.dispatcher import StepOutcome
                    steps.append(StepOutcome(action, preview, 0, "", "",
                                             dry_run=True))
                    history.append(history_entry(i + 1, action, preview, 0,
                                                 "", ""))
                    if logger is not None:
                        logger.log(runlog.result_event(i + 1, preview,
                                                       dry_run=True))
                    if ask_continue and not continue_requested(response, bar):
                        return RunResult(steps=tuple(steps), ok=True,
                                         stop_reason=(
                                             f"done after step {i+1} (dry-run)"))
                    continue

                if action.risk in ("write", "destructive"):
                    approved = (False if on_confirm is None
                                else bool(on_confirm(action, preview)))
                    if not approved:
                        if logger is not None:
                            logger.log(runlog.result_event(
                                i + 1, preview, declined=True))
                        return RunResult(steps=tuple(steps), ok=False,
                                         declined=True,
                                         stop_reason="declined by user")

                if execute_fn is not None:
                    argv, rc, out, err = execute_fn(action, cwd_s)
                    argv = list(argv)
                else:
                    try:
                        res = _executor.execute(
                            self.config, action, cwd_s,
                            timeout=self._timeout)
                    except ExecutionError as e:
                        if logger is not None:
                            logger.log(runlog.result_event(
                                i + 1, preview, error=str(e)))
                        return RunResult(steps=tuple(steps), ok=False,
                                         stop_reason=str(e))
                    argv, rc, out, err = (list(res.argv), res.returncode,
                                          res.stdout, res.stderr)
                from jevdo.dispatcher import StepOutcome
                steps.append(StepOutcome(action, argv, rc, out, err))
                history.append(history_entry(i + 1, action, argv, rc, out,
                                             err))
                if logger is not None:
                    logger.log(runlog.result_event(i + 1, argv, returncode=rc,
                                                   stdout=out, stderr=err))
                if rc != 0 and stop_on_error:
                    return RunResult(steps=tuple(steps), ok=False,
                                     stop_reason=f"stop: step {i+1} exited {rc}")
                if ask_continue and not continue_requested(response, bar):
                    ok = all(s.returncode == 0 for s in steps)
                    return RunResult(steps=tuple(steps), ok=ok,
                                     stop_reason=f"done after step {i+1}")
            ok = all(s.returncode == 0 for s in steps) if steps else False
            if dry_run and steps:
                ok = True
            return RunResult(steps=tuple(steps), ok=ok,
                             stop_reason="max_steps reached")
        finally:
            if own_logger is not None:
                own_logger.close()

    def _retry_after_repeat(self, request, cwd_s, *, history, max_steps,
                            max_history, min_confidence, temperature,
                            step_index, ask_continue, prev_argv, logger,
                            client):
        """Re-plan once with an anti-repeat nudge. Returns
        ``(outcome, context, response, argv, action)`` or None."""
        from jevdo import runlog
        from jevdo.dispatcher import REPEAT_HINT_STATE, dispatch
        from jevdo.executor import resolve_argv

        outcome, _q, context, response = dispatch(
            self.config, request, cwd_s, client=client,
            min_confidence=min_confidence, history=history or None,
            max_steps=max_steps, max_history=max_history,
            allow_continue=ask_continue, temperature=temperature,
            step_index=step_index, repeat_hint=True,
            hint=REPEAT_HINT_STATE)
        if logger is not None:
            from jevdo.dispatcher import continue_info
            logger.log(runlog.plan_event(
                step_index + 1, request, cwd_s, outcome, context,
                continue_asked=ask_continue,
                continue_value=continue_info(response),
                max_steps=max_steps, max_history=max_history,
                history_len=len(history), repeat_retry=True))
        if not outcome.ok or outcome.action is None:
            return None
        action = outcome.action
        try:
            argv = list(resolve_argv(self.config, action, cwd_s))
        except Exception:
            return None
        if argv == list(prev_argv):
            return None
        return outcome, context, response, argv, action

    # -- eval --------------------------------------------------------
    def eval(self, eval_file_or_cases, *, cwd=None, min_confidence=None,
             temperature=None, continue_threshold=None, client=None):
        """Run eval cases (plans only, never executes). Returns EvalSummary.

        Accepts an eval TOML path or a pre-loaded ``list[EvalCase]``.
        """
        from jevdo.eval import load_eval, run_eval
        if isinstance(eval_file_or_cases, (str, os.PathLike)):
            cases = load_eval(str(eval_file_or_cases))
        else:
            cases = list(eval_file_or_cases)
        base_cwd = self._resolve_cwd(cwd)
        eff_conf = (min_confidence if min_confidence is not None
                    else self._min_confidence)
        eff_temp = (temperature if temperature is not None
                    else self._temperature)
        eff_cont = (continue_threshold if continue_threshold is not None
                    else self._continue_threshold)
        eff_client, _ = self._active_client(client)
        self._ensure_api_key(eff_client, None)
        return run_eval(self.config, cases, base_cwd, client=eff_client,
                        min_confidence=eff_conf, temperature=eff_temp,
                        continue_threshold=eff_cont)

    # -- misc --------------------------------------------------------
    @property
    def cwd(self) -> str:
        return self._resolve_cwd(None)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (f"Harness(model={self.config.model!r}, "
                f"cwd={self._cwd!r}, commands={len(self.config.commands)})")


__all__ = ["Harness", "RunResult", "OnConfirm", "apply_provider_overrides"]
