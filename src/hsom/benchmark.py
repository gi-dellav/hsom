"""Benchmark runner for the suites under ``examples/``.

Usage::

    python benchmark.py check
    python benchmark.py freeze --suite container-ops --ref heldout-v1
    python benchmark.py run --suite git-workflow --repeats 5
    python benchmark.py run --systems jev,structured,logprobs

Jev runs through the normal hsom eval harness (plans only, never executes).
The two LiteLLM baselines use OpenRouter; set ``OPENROUTER_API_KEY``.
Raw JSONL logs and the generated report go to ``examples/benchmark-results/``
unless ``--output`` is given.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

from hsom.config import ConfigError, load_config
from hsom.eval import EvalCase, EvalTestResult, load_eval, run_eval
from hsom.executor import ExecutionError, resolve_argv
from hsom.runlog import JsonlLogger, eval_event, run_event
from hsom.stats import clopper_pearson, percentile

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples"
BENCHMARK_CONFIG = EXAMPLES_DIR / "benchmark.toml"
DEFAULT_RESULTS_DIR = EXAMPLES_DIR / "benchmark-results"
SYSTEMS = ("jev", "structured", "logprobs")


class BenchmarkError(Exception):
    pass


@dataclass(frozen=True)
class Suite:
    name: str
    label: str
    env: Path
    eval: Path
    cwd: Path
    excluded: Path | None = None
    manifest: Path | None = None


@dataclass(frozen=True)
class BenchmarkConfig:
    suites: tuple[Suite, ...]
    repeats: int = 5
    alpha: float = 0.05
    structured_model: str = "openrouter/openai/gpt-6-luna"
    logprob_model: str = "openrouter/openai/gpt-6-luna"
    pricing: Path | None = None
    results_dir: Path = DEFAULT_RESULTS_DIR
    include_excluded: bool = True


@dataclass(frozen=True)
class LeakHit:
    suite: str
    case: str
    field: str
    text: str


@dataclass(frozen=True)
class CaseRecord:
    suite: str
    system: str
    run_index: int
    repeats: int
    result: EvalTestResult
    excluded: bool = False

    @property
    def case(self) -> EvalCase:
        return self.result.case


@dataclass(frozen=True)
class Pricing:
    as_of: str
    currency: str
    per_mtok: dict[str, tuple[float, float]]
    source: str | None = None

    def cost(self, model: str | None, input_tokens: int | None,
             output_tokens: int | None) -> float | None:
        if model is None:
            return None
        key = _pricing_key(model)
        prices = (self.per_mtok.get(key) or self.per_mtok.get(model)
                  or self.per_mtok.get(f"openrouter/{key}"))
        if prices is None:
            return None
        in_tok = input_tokens or 0
        out_tok = output_tokens or 0
        return (in_tok * prices[0] + out_tok * prices[1]) / 1_000_000.0


@dataclass
class CaseAggregate:
    name: str
    runs: int
    passes: int
    pattern: str
    wrong_plan: bool
    excluded: bool
    last_reason: str
    last_actual: str | None
    error_kind: str | None

    @property
    def rate(self) -> float:
        return self.passes / self.runs if self.runs else 0.0

    @property
    def strict_pass(self) -> bool:
        return self.runs > 0 and self.passes == self.runs


@dataclass
class SuiteAggregate:
    suite: str
    label: str
    system: str
    repeats: int
    cases: list[CaseAggregate] = field(default_factory=list)
    skipped: int = 0
    provider_errors: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: list[float] = field(default_factory=list)
    models: set[str] = field(default_factory=set)
    logprob_fallbacks: int = 0

    def _cases(self, *, include_excluded: bool) -> list[CaseAggregate]:
        return [c for c in self.cases if include_excluded or not c.excluded]

    def headline_cases(self) -> list[CaseAggregate]:
        return self._cases(include_excluded=False)

    def all_cases(self) -> list[CaseAggregate]:
        return self._cases(include_excluded=True)

    def strict_counts(self, cases: list[CaseAggregate]) -> tuple[int, int]:
        total = len(cases)
        passed = sum(1 for c in cases if c.strict_pass)
        return passed, total

    def per_run_rates(self) -> list[float]:
        by_run: dict[int, list[bool]] = {}
        for case in self.headline_cases():
            for idx, bit in enumerate(case.pattern):
                by_run.setdefault(idx + 1, []).append(bit == "1")
        return [sum(v) / len(v) for _, v in sorted(by_run.items()) if v]


# ---------------------------------------------------------------- config

def _load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except FileNotFoundError as e:
        raise BenchmarkError(f"file not found: {path}") from e
    except Exception as e:
        raise BenchmarkError(f"failed to parse {path}: {e}") from e


def load_benchmark_config(path: Path = BENCHMARK_CONFIG) -> BenchmarkConfig:
    data = _load_toml(path)
    root = path.parent
    meta = data.get("benchmark", {})
    if not isinstance(meta, dict):
        raise BenchmarkError(f"{path}: [benchmark] must be a table")
    raw_suites = data.get("suite", {})
    if not isinstance(raw_suites, dict) or not raw_suites:
        raise BenchmarkError(f"{path}: need at least one [suite.*] table")
    suites: list[Suite] = []
    for name, raw in raw_suites.items():
        if not isinstance(raw, dict):
            raise BenchmarkError(f"{path}: suite '{name}' must be a table")
        env = root / _req(raw, "env", name)
        ev = root / _req(raw, "eval", name)
        cwd = root / _req(raw, "cwd", name)
        excluded = raw.get("excluded")
        manifest = raw.get("manifest")
        suites.append(Suite(
            name=name,
            label=str(raw.get("label", "regression")),
            env=env,
            eval=ev,
            cwd=cwd,
            excluded=(root / excluded) if excluded else None,
            manifest=(root / manifest) if manifest else None,
        ))
    pricing = meta.get("pricing")
    return BenchmarkConfig(
        suites=tuple(suites),
        repeats=int(meta.get("repeats", 5)),
        alpha=float(meta.get("alpha", 0.05)),
        structured_model=str(meta.get(
            "structured_model", "openrouter/openai/gpt-6-luna")),
        logprob_model=str(meta.get(
            "logprob_model", "openrouter/openai/gpt-6-luna")),
        pricing=(root / pricing) if pricing else None,
        results_dir=root / str(meta.get("results_dir", "benchmark-results")),
        include_excluded=bool(meta.get("include_excluded", True)),
    )


def _req(d: dict, key: str, ctx: str) -> str:
    value = d.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"suite '{ctx}': '{key}' must be a non-empty string")
    return value.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
            check=False)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def suite_paths(suite: Suite) -> list[Path]:
    paths = [suite.env, suite.eval]
    if suite.excluded is not None and suite.excluded.exists():
        paths.append(suite.excluded)
    if suite.cwd.exists():
        paths.extend(p for p in sorted(suite.cwd.rglob("*")) if p.is_file())
    return paths


def compute_manifest(suite: Suite, ref: str) -> dict:
    files: dict[str, str] = {}
    for path in suite_paths(suite):
        try:
            rel = path.resolve().relative_to(EXAMPLES_DIR.resolve())
        except ValueError:
            rel = Path(path.name)
        files[str(rel).replace(os.sep, "/")] = _sha256(path)
    return {
        "suite": suite.name,
        "ref": ref,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "examples")),
        "files": files,
    }


def freeze_suite(suite: Suite, ref: str, output: Path | None = None) -> Path:
    manifest = compute_manifest(suite, ref)
    out = output or suite.manifest
    if out is None:
        raise BenchmarkError(f"suite '{suite.name}' has no manifest path")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return out


def verify_manifest(suite: Suite) -> list[str]:
    if suite.manifest is None:
        return []
    if not suite.manifest.exists():
        return [f"{suite.name}: manifest missing: {suite.manifest}"]
    try:
        manifest = json.loads(suite.manifest.read_text())
    except Exception as e:
        return [f"{suite.name}: invalid manifest: {e}"]
    errors: list[str] = []
    if manifest.get("suite") != suite.name:
        errors.append(f"{suite.name}: manifest suite mismatch")
    files = manifest.get("files", {})
    if not isinstance(files, dict) or not files:
        return [f"{suite.name}: manifest has no file hashes"]
    for rel, expected in files.items():
        path = EXAMPLES_DIR / rel
        if not path.exists():
            errors.append(f"{suite.name}: missing frozen file {rel}")
        elif _sha256(path) != expected:
            errors.append(f"{suite.name}: frozen file changed: {rel}")
    return errors


# ---------------------------------------------------------------- leakage

def _walk_strings(node, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            out.extend(_walk_strings(value, f"{prefix}/{key}"))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            out.extend(_walk_strings(value, f"{prefix}[{idx}]"))
    elif isinstance(node, str):
        out.append((prefix, node))
    return out


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def check_suite_leakage(suite: Suite) -> list[LeakHit]:
    env = _load_toml(suite.env)
    strings = [(field, _normalize(text)) for field, text in _walk_strings(env)]
    eval_paths = [suite.eval]
    if suite.excluded is not None and suite.excluded.exists():
        eval_paths.append(suite.excluded)
    hits: list[LeakHit] = []
    for eval_path in eval_paths:
        for case in load_eval(str(eval_path)):
            needle = _normalize(case.input)
            if not needle:
                continue
            for path_field, text in strings:
                if needle in text:
                    hits.append(LeakHit(suite.name, case.name, path_field,
                                        text[:160]))
    return hits


def check_suite_pins(suite: Suite) -> list[str]:
    try:
        env = load_config(str(suite.env))
    except ConfigError as e:
        return [f"{suite.name}: config error: {e}"]
    errors: list[str] = []
    if env.model.endswith("-latest"):
        errors.append(f"{suite.name}: model is not pinned: {env.model}")
    if env.temperature is None:
        errors.append(f"{suite.name}: temperature is not set explicitly")
    return errors


def check_all(config: BenchmarkConfig) -> tuple[list[LeakHit], list[str]]:
    hits: list[LeakHit] = []
    errors: list[str] = []
    for suite in config.suites:
        hits.extend(check_suite_leakage(suite))
        errors.extend(verify_manifest(suite))
        errors.extend(check_suite_pins(suite))
    for label, model in (("structured_model", config.structured_model),
                         ("logprob_model", config.logprob_model)):
        if model.endswith("-latest"):
            errors.append(f"benchmark.toml: {label} is not pinned: {model}")
    return hits, errors


# ---------------------------------------------------------------- pricing

def _pricing_key(model: str) -> str:
    return model.removeprefix("openrouter/")


def load_pricing(path: Path | None) -> Pricing | None:
    if path is None or not path.exists():
        return None
    data = _load_toml(path)
    models = data.get("model", {})
    if not isinstance(models, dict):
        raise BenchmarkError(f"{path}: [model] must be a table")
    per_mtok: dict[str, tuple[float, float]] = {}
    for name, raw in models.items():
        if not isinstance(raw, dict):
            continue
        inp = raw.get("input_per_mtok")
        out = raw.get("output_per_mtok")
        if isinstance(inp, (int, float)) and isinstance(out, (int, float)):
            per_mtok[name] = (float(inp), float(out))
    return Pricing(
        as_of=str(data.get("as_of", "unknown")),
        currency=str(data.get("currency", "USD")),
        per_mtok=per_mtok,
        source=data.get("source"),
    )


# ---------------------------------------------------------------- runs

def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in name)


def _run_meta(suite: Suite, system: str, *, config, repeats: int,
              temperature: float | None, logger: JsonlLogger | None,
              model: str | None = None) -> None:
    if logger is None:
        return
    from hsom import __version__

    frozen = suite.manifest.exists() if suite.manifest is not None else False
    logger.log(run_event(
        suite=suite.name,
        label=suite.label,
        eval_file=str(suite.eval),
        eval_sha256=_sha256(suite.eval),
        env_file=str(suite.env),
        env_sha256=_sha256(suite.env),
        model=model or (config.model if system == "jev" else None),
        provider=(config.provider if system == "jev" else "openrouter"),
        temperature=temperature,
        repeats=repeats,
        system=system,
        hsom_version=__version__,
        git_commit=_git("rev-parse", "HEAD"),
        frozen=frozen,
        frozen_ref=(json.loads(suite.manifest.read_text()).get("ref")
                    if frozen and suite.manifest is not None else None),
    ))


def run_jev_suite(suite: Suite, config: BenchmarkConfig, *, repeats: int,
                  include_excluded: bool, logger: JsonlLogger | None = None,
                  delay: float = 0.0,
                  limit: int | None = None) -> list[CaseRecord]:
    from hsom.client import create_client

    env_config = load_config(str(suite.env))
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise BenchmarkError("OPENROUTER_API_KEY is not set")
    client = create_client(env_config, api_key=api_key)
    cases = load_eval(str(suite.eval))
    if limit:
        cases = cases[:limit]
    records: list[CaseRecord] = []
    _run_meta(suite, "jev", config=env_config, repeats=repeats,
              temperature=env_config.temperature, logger=logger)
    work = [(cases, False)]
    if include_excluded and suite.excluded is not None and suite.excluded.exists():
        extra = load_eval(str(suite.excluded))
        work.append((extra[:limit] if limit else extra, True))
    try:
        for run_index in range(1, repeats + 1):
            for batch, excluded in work:
                summary = run_eval(env_config, batch, str(suite.cwd),
                                   client=client,
                                   temperature=env_config.temperature)
                for result in summary.results:
                    records.append(CaseRecord(
                        suite.name, "jev", run_index, repeats, result, excluded))
                    if logger is not None:
                        logger.log(eval_event(
                            result.case, result,
                            temperature=env_config.temperature,
                            run_index=run_index,
                            repeats=repeats,
                            system="jev",
                            suite=suite.name,
                            model=result.model or env_config.model,
                            excluded=excluded,
                        ))
                    if delay:
                        time.sleep(delay)
    finally:
        try:
            client.close()
        except Exception:
            pass
    return records


def _ensure_litellm() -> None:
    if importlib.util.find_spec("litellm") is None:
        raise BenchmarkError(
            "LiteLLM is not installed; install with "
            "pip install -e '.[benchmark]'")


def _eval_baseline_outcome(env_config, case: EvalCase, cwd: str,
                           outcome, usage, planner_name: str) -> EvalTestResult:
    actual: tuple[tuple[str, ...], ...] | None = None
    risk = None
    confidence = 0.0
    if outcome.ok and outcome.action is not None:
        risk = outcome.action.risk
        confidence = outcome.action.confidence
        try:
            actual = (tuple(resolve_argv(env_config, outcome.action, cwd)),)
        except ExecutionError as e:
            return EvalTestResult(
                case, False, None, f"refused: {e}", error_kind="refused",
                model=usage.model, input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                latency_ms=usage.latency_ms,
                logprob_fallbacks=usage.fallbacks)
        if case.expect_abstain:
            return EvalTestResult(
                case, False, actual,
                f"expected abstention but planned '{_fmt(actual)}'",
                confidence=confidence, risk=risk, model=usage.model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                latency_ms=usage.latency_ms,
                logprob_fallbacks=usage.fallbacks)
        if case.expected is not None and actual == case.expected:
            return EvalTestResult(
                case, True, actual, "ok", confidence=confidence, risk=risk,
                model=usage.model, input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                latency_ms=usage.latency_ms,
                logprob_fallbacks=usage.fallbacks)
        return EvalTestResult(
            case, False, actual,
            f"expected '{_fmt(case.expected)}' got '{_fmt(actual)}'",
            confidence=confidence, risk=risk, model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=usage.latency_ms,
            logprob_fallbacks=usage.fallbacks)
    reason = outcome.reason or f"{planner_name} abstained"
    return EvalTestResult(
        case, case.expect_abstain, None, f"abstained: {reason}",
        confidence=confidence, model=usage.model,
        input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
        latency_ms=usage.latency_ms,
        logprob_fallbacks=usage.fallbacks)


def run_baseline_suite(suite: Suite, config: BenchmarkConfig, system: str,
                       *, repeats: int, include_excluded: bool,
                       logger: JsonlLogger | None = None,
                       delay: float = 0.0,
                       limit: int | None = None) -> list[CaseRecord]:
    from hsom.baselines import BaselineError, make_planner

    _ensure_litellm()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise BenchmarkError("OPENROUTER_API_KEY is not set")
    env_config = load_config(str(suite.env))
    model = (config.structured_model if system == "structured"
             else config.logprob_model)
    planner = make_planner(system, model=model, api_key=api_key,
                           temperature=0.0, timeout=env_config.timeout)
    _run_meta(suite, system, config=env_config, repeats=repeats,
              temperature=0.0, logger=logger, model=model)
    main_cases = load_eval(str(suite.eval))
    work: list[tuple[list[EvalCase], bool]] = [
        (main_cases[:limit] if limit else main_cases, False)]
    if include_excluded and suite.excluded is not None and suite.excluded.exists():
        extra = load_eval(str(suite.excluded))
        work.append((extra[:limit] if limit else extra, True))
    records: list[CaseRecord] = []
    for run_index in range(1, repeats + 1):
        for batch, excluded in work:
            for case in batch:
                if case.steps > 1 and not case.expect_abstain:
                    result = EvalTestResult(
                        case, False, None,
                        "not evaluated: multi-step/loop is out of scope",
                        error_kind="skipped", model=model)
                else:
                    try:
                        outcome, usage = planner.plan(
                            env_config, case.input, str(suite.cwd))
                        result = _eval_baseline_outcome(
                            env_config, case, str(suite.cwd), outcome,
                            usage, system)
                    except BaselineError as e:
                        result = EvalTestResult(
                            case, False, None, f"baseline error: {e}",
                            error_kind="baseline", model=model)
                records.append(CaseRecord(
                    suite.name, system, run_index, repeats, result, excluded))
                if logger is not None:
                    logger.log(eval_event(
                        result.case, result, temperature=0.0,
                        run_index=run_index, repeats=repeats,
                        system=system, suite=suite.name,
                        model=result.model or model, excluded=excluded))
                if delay:
                    time.sleep(delay)
    return records


def _fmt(steps: tuple[tuple[str, ...], ...] | None) -> str:
    from hsom.eval import _fmt as eval_fmt
    return eval_fmt(steps)


# ---------------------------------------------------------------- aggregation

def aggregate(suite: Suite, system: str, records: list[CaseRecord],
              repeats: int) -> SuiteAggregate:
    agg = SuiteAggregate(suite=suite.name, label=suite.label, system=system,
                         repeats=repeats)
    by_case: dict[str, list[CaseRecord]] = {}
    for rec in records:
        by_case.setdefault(rec.case.name, []).append(rec)
        if rec.result.input_tokens:
            agg.input_tokens += rec.result.input_tokens
        if rec.result.output_tokens:
            agg.output_tokens += rec.result.output_tokens
        if rec.result.latency_ms is not None:
            agg.latency_ms.append(rec.result.latency_ms)
        agg.logprob_fallbacks += rec.result.logprob_fallbacks
        if rec.result.model:
            agg.models.add(rec.result.model.removeprefix("openrouter/"))
    for name, recs in by_case.items():
        skipped = [r for r in recs if r.result.error_kind == "skipped"]
        recs = [r for r in recs if r.result.error_kind != "skipped"]
        agg.skipped += len(skipped)
        if not recs:
            continue
        ordered = sorted(recs, key=lambda r: r.run_index)
        runs = len(ordered)
        passes = sum(1 for r in ordered if r.result.passed)
        errors = [r.result.error_kind for r in ordered if r.result.error_kind]
        if any(e == "provider" for e in errors):
            agg.provider_errors += 1
        agg.cases.append(CaseAggregate(
            name=name,
            runs=runs,
            passes=passes,
            pattern="".join("1" if r.result.passed else "0" for r in ordered),
            wrong_plan=bool(ordered[0].case.wrong_plan),
            excluded=bool(ordered[0].excluded or ordered[0].case.excluded),
            last_reason=ordered[-1].result.reason,
            last_actual=_fmt(ordered[-1].result.actual),
            error_kind=errors[-1] if errors else None,
        ))
    agg.cases.sort(key=lambda c: c.name)
    return agg


def _parse_steps(text: str | None) -> tuple[tuple[str, ...], ...] | None:
    if text is None:
        return None
    parts = [p for p in text.split(" ; ") if p]
    if not parts:
        return None
    return tuple(tuple(shlex.split(p)) for p in parts)


def records_from_logs(paths: list[Path]) -> dict[tuple[str, str, int],
                                                  list[CaseRecord]]:
    """Reconstruct aggregate inputs from JSONL ``run``/``eval`` events."""
    grouped: dict[tuple[str, str, int], list[CaseRecord]] = {}
    for path in sorted(paths):
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = json.loads(line)
                if event.get("type") != "eval":
                    continue
                suite = str(event.get("suite") or path.stem.split(".")[0])
                system = str(event.get("system") or "jev")
                repeats = int(event.get("repeats") or 1)
                run_index = int(event.get("run_index") or 1)
                expected = _parse_steps(event.get("expected"))
                actual = _parse_steps(event.get("actual"))
                expected_str = (tuple(event["expected"].split(" ; "))
                                if event.get("expected") else None)
                case = EvalCase(
                    name=str(event.get("name") or "unnamed"),
                    input=str(event.get("input") or ""),
                    expected=expected,
                    expected_str=expected_str,
                    expect_abstain=event.get("expected") is None,
                    exclude_reason=event.get("exclude_reason"),
                    wrong_plan=bool(event.get("wrong_plan", False)),
                )
                result = EvalTestResult(
                    case=case,
                    passed=bool(event.get("passed")),
                    actual=actual,
                    reason=str(event.get("reason") or ""),
                    confidence=float(event.get("confidence") or 0.0),
                    risk=event.get("risk"),
                    error_kind=event.get("error_kind"),
                    model=event.get("model"),
                    input_tokens=event.get("input_tokens"),
                    output_tokens=event.get("output_tokens"),
                    latency_ms=event.get("latency_ms"),
                    logprob_fallbacks=int(event.get("logprob_fallbacks") or 0),
                )
                grouped.setdefault((suite, system, repeats), []).append(
                    CaseRecord(suite, system, run_index, repeats, result,
                               bool(event.get("excluded", False))))
    return grouped


def build_aggregates_from_logs(config: BenchmarkConfig, paths: list[Path]
                               ) -> list[SuiteAggregate]:
    by_name = {s.name: s for s in config.suites}
    aggregates: list[SuiteAggregate] = []
    for (suite_name, system, repeats), records in sorted(
            records_from_logs(paths).items()):
        suite = by_name.get(suite_name)
        if suite is None:
            continue
        aggregates.append(aggregate(suite, system, records, repeats))
    return aggregates


def _interval(k: int, n: int, alpha: float) -> tuple[float, float, str]:
    if n <= 0:
        return 0.0, 1.0, "n/a"
    ci = clopper_pearson(k, n, alpha=alpha)
    return ci.low, ci.high, ci.method


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _ci_text(k: int, n: int, alpha: float) -> str:
    lo, hi, _ = _interval(k, n, alpha)
    return f"{_pct(lo)}–{_pct(hi)}"


def _latency(agg: SuiteAggregate) -> tuple[float | None, float | None]:
    return percentile(agg.latency_ms, 0.5), percentile(agg.latency_ms, 0.95)


# ---------------------------------------------------------------- report

def render_report(config: BenchmarkConfig, aggregates: list[SuiteAggregate],
                  pricing: Pricing | None, *, output_dir: Path,
                  frozen: dict[str, dict] | None = None) -> str:
    lines: list[str] = []
    lines.append("# hsom benchmark report")
    lines.append("")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}")
    lines.append("")
    lines.append(
        "Suites under `examples/`. `regression` suites were used during "
        "development; `heldout` suites are frozen before execution. Headline "
        "numbers should come from held-out suites only.")
    lines.append("")

    by_suite: dict[str, list[SuiteAggregate]] = {}
    for agg in aggregates:
        by_suite.setdefault(agg.suite, []).append(agg)

    lines.append("## Aggregate accuracy")
    lines.append("")
    lines.append(
        "`strict` means every repeat passed. Intervals are exact "
        f"Clopper–Pearson at {(1 - config.alpha) * 100:.0f}% over cases; "
        "pooled intervals treat runs as trials and are labelled separately "
        "because repeated runs of one case are correlated.")
    lines.append("")
    lines.append("| Suite | Label | System | Cases | Strict pass | Strict rate | 95% CI | Pooled runs | Pooled CI | Provider-error cases | Skipped |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for suite in config.suites:
        for agg in sorted(by_suite.get(suite.name, []), key=lambda a: a.system):
            cases = agg.headline_cases()
            strict_k, strict_n = agg.strict_counts(cases)
            total_runs = sum(c.runs for c in cases)
            total_passes = sum(c.passes for c in cases)
            lines.append(
                f"| {agg.suite} | {agg.label} | {agg.system} | {strict_n} | "
                f"{strict_k} | {_pct(strict_k / strict_n if strict_n else None)} | "
                f"{_ci_text(strict_k, strict_n, config.alpha)} | "
                f"{total_passes}/{total_runs} | "
                f"{_ci_text(total_passes, total_runs, config.alpha)} | "
                f"{agg.provider_errors} | {agg.skipped} |")
    lines.append("")

    lines.append("## With and without exclusions")
    lines.append("")
    lines.append(
        "`applied` is the headline denominator (excluded probes omitted). "
        "`removed` includes the excluded probes and is only available when "
        "they were run with `--include-excluded`.")
    lines.append("")
    lines.append("| Suite | System | Exclusions | Cases | Strict pass | Strict rate | 95% CI |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for suite in config.suites:
        for agg in sorted(by_suite.get(suite.name, []), key=lambda a: a.system):
            for label, cases in (
                    ("applied", agg.headline_cases()),
                    ("removed", agg.all_cases())):
                if label == "removed" and not any(c.excluded for c in cases):
                    continue
                k, n = agg.strict_counts(cases)
                lines.append(
                    f"| {agg.suite} | {agg.system} | {label} | {n} | {k} | "
                    f"{_pct(k / n if n else None)} | "
                    f"{_ci_text(k, n, config.alpha)} |")
    lines.append("")

    lines.append("## Stability across repeats")
    lines.append("")
    lines.append("| Suite | System | Per-run pass rates | Range | All-repeat cases |")
    lines.append("| --- | --- | --- | --- | --- |")
    for suite in config.suites:
        for agg in sorted(by_suite.get(suite.name, []), key=lambda a: a.system):
            rates = agg.per_run_rates()
            rng = (f"{_pct(min(rates))}–{_pct(max(rates))}" if rates else "n/a")
            shown = ", ".join(_pct(r) for r in rates) if rates else "n/a"
            cases = agg.headline_cases()
            stable = sum(1 for c in cases if c.strict_pass)
            lines.append(
                f"| {agg.suite} | {agg.system} | {shown} | {rng} | "
                f"{stable}/{len(cases)} |")
    lines.append("")

    lines.append("## Cost and latency")
    lines.append("")
    if pricing is not None:
        lines.append(f"Pricing: {pricing.currency}, as of {pricing.as_of}"
                     + (f" ({pricing.source})" if pricing.source else "") + ".")
    else:
        lines.append("Pricing: not configured (cost reported as n/a).")
    lines.append("")
    lines.append("| Suite | System | Models | Input tokens | Output tokens | p50 ms | p95 ms | Cost | Logprob fallbacks |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for suite in config.suites:
        for agg in sorted(by_suite.get(suite.name, []), key=lambda a: a.system):
            p50, p95 = _latency(agg)
            cost = None
            if pricing is not None:
                if agg.models:
                    costs = [pricing.cost(m, agg.input_tokens, agg.output_tokens)
                             for m in agg.models]
                else:
                    costs = [pricing.cost(None, agg.input_tokens,
                                          agg.output_tokens)]
                known = [c for c in costs if c is not None]
                cost = sum(known) if known else None
            cost_text = (f"{cost:.4f} {pricing.currency}"
                         if cost is not None and pricing is not None else "n/a")
            models = ", ".join(sorted(agg.models)) or "n/a"
            lines.append(
                f"| {agg.suite} | {agg.system} | {models} | "
                f"{agg.input_tokens} | {agg.output_tokens} | "
                f"{_ms(p50)} | {_ms(p95)} | {cost_text} | "
                f"{agg.logprob_fallbacks} |")
    lines.append("")

    lines.append("## Per-case results")
    lines.append("")
    for suite in config.suites:
        for agg in sorted(by_suite.get(suite.name, []), key=lambda a: a.system):
            lines.append(f"### {agg.suite} / {agg.system}")
            lines.append("")
            lines.append("| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
            for case in agg.cases:
                lines.append(
                    f"| {case.name} | {case.runs} | {case.passes} | "
                    f"{_pct(case.rate)} | "
                    f"{_ci_text(case.passes, case.runs, config.alpha)} | "
                    f"`{case.pattern}` | {'yes' if case.excluded else 'no'} | "
                    f"{_clean(case.last_reason)} |")
            lines.append("")

    lines.append("## Exclusions")
    lines.append("")
    lines.append(
        "Every declared exclusion is listed with its reason. `wrong plan` "
        "marks probes where the selected operation is not the intended one.")
    lines.append("")
    declared_total = 0
    wrong_total = 0
    for suite in config.suites:
        if suite.excluded is not None and suite.excluded.exists():
            for case in load_eval(str(suite.excluded)):
                declared_total += 1
                wrong_total += int(case.wrong_plan)
    lines.append(f"Declared exclusions: {declared_total} "
                 f"(wrong plan: {wrong_total}).")
    lines.append("")
    lines.append("| Suite | Case | Input | Expected | Actual | Reason | Wrong plan | Runs | Pass |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for suite in config.suites:
        if suite.excluded is None or not suite.excluded.exists():
            continue
        declared = load_eval(str(suite.excluded))
        jev_agg = next((a for a in by_suite.get(suite.name, [])
                        if a.system == "jev"), None)
        by_name = {c.name: c for c in (jev_agg.cases if jev_agg else [])}
        for case in declared:
            result = by_name.get(case.name)
            expected = "abstain" if case.expect_abstain else " ; ".join(
                case.expected_str or ())
            if result is None:
                actual_text = "not run"
            elif result.last_actual is None:
                actual_text = "abstain"
            else:
                actual_text = result.last_actual
            lines.append(
                f"| {suite.name} | {case.name} | {_clean(case.input)} | "
                f"{_clean(expected)} | {_clean(actual_text)} | "
                f"{_clean(case.exclude_reason or '')} | "
                f"{'yes' if case.wrong_plan else 'no'} | "
                f"{result.runs if result else 0} | "
                f"{result.passes if result else 0} |")
    lines.append("")

    lines.append("## Provenance")
    lines.append("")
    for suite in config.suites:
        lines.append(f"- **{suite.name}** ({suite.label}): "
                     f"`{_rel(suite.env)}` sha256 `{_sha256(suite.env)[:16]}`, "
                     f"`{_rel(suite.eval)}` sha256 `{_sha256(suite.eval)[:16]}`")
        try:
            env_cfg = load_config(str(suite.env))
            lines.append(
                f"  requested model `{env_cfg.model}`, temperature "
                f"`{env_cfg.temperature}`, provider `{env_cfg.provider}`")
        except ConfigError:
            pass
        if suite.manifest is not None and suite.manifest.exists():
            manifest = json.loads(suite.manifest.read_text())
            lines.append(
                f"  frozen ref `{manifest.get('ref')}`, "
                f"git `{manifest.get('git_commit')}`, "
                f"dirty={manifest.get('git_dirty')}")
        elif suite.manifest is not None:
            lines.append("  manifest missing (unfrozen)")
    lines.append("")
    if config.pricing is not None and config.pricing.exists():
        lines.append(f"Pricing file: `{_rel(config.pricing)}`")
    lines.append("")

    text = "\n".join(lines) + "\n"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.md").write_text(text)
    (output_dir / "report.json").write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "alpha": config.alpha,
        "aggregates": [dataclasses.asdict(a) for a in aggregates],
        "frozen": frozen or {},
    }, indent=2, default=list) + "\n")
    return text


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(EXAMPLES_DIR.resolve()))
    except ValueError:
        return str(path)


def _clean(text: str | None) -> str:
    if text is None:
        return ""
    return text.replace("|", "\\|").replace("\n", " ")


def _ms(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}"


# ---------------------------------------------------------------- CLI

def _select_suites(config: BenchmarkConfig, names: list[str] | None) -> list[Suite]:
    if not names:
        return list(config.suites)
    known = {s.name: s for s in config.suites}
    missing = [n for n in names if n not in known]
    if missing:
        raise BenchmarkError(f"unknown suite(s): {', '.join(missing)}")
    return [known[n] for n in names]


def _parse_systems(value: str | None) -> list[str]:
    if not value:
        return list(SYSTEMS)
    systems = [x.strip() for x in value.split(",") if x.strip()]
    unknown = [x for x in systems if x not in SYSTEMS]
    if unknown:
        raise BenchmarkError(f"unknown system(s): {', '.join(unknown)}")
    return systems


def command_check(args) -> int:
    config = load_benchmark_config()
    hits, errors = check_all(config)
    for hit in hits:
        print(f"LEAK {hit.suite} / {hit.case} in {hit.field}: {hit.text!r}")
    for error in errors:
        print(f"MANIFEST {error}")
    if hits or errors:
        print(f"check failed: {len(hits)} leak(s), {len(errors)} manifest error(s)")
        return 1
    print(f"check ok: {len(config.suites)} suites, no leaks, manifests valid")
    return 0


def command_freeze(args) -> int:
    config = load_benchmark_config()
    suite = _select_suites(config, [args.suite])[0]
    output = Path(args.output) if args.output else None
    path = freeze_suite(suite, args.ref, output)
    print(f"froze {suite.name} at {path}")
    return 0


def command_run(args) -> int:
    config = load_benchmark_config()
    suites = _select_suites(config, args.suite)
    systems = _parse_systems(args.systems)
    repeats = args.repeats or config.repeats
    include_excluded = (config.include_excluded if args.include_excluded is None
                        else args.include_excluded)
    if repeats < 1:
        raise BenchmarkError("--repeats must be >= 1")

    hits: list[LeakHit] = []
    errors: list[str] = []
    for suite in suites:
        hits.extend(check_suite_leakage(suite))
        errors.extend(verify_manifest(suite))
        errors.extend(check_suite_pins(suite))
    hard_errors = [e for e in errors]
    if hard_errors and not args.allow_unfrozen:
        raise BenchmarkError(
            "manifest verification failed; re-freeze or pass --allow-unfrozen:\n"
            + "\n".join(hard_errors))
    if hits:
        raise BenchmarkError(
            "leakage check failed; remove matching inputs from tree descriptions:\n"
            + "\n".join(f"{h.suite}/{h.case} in {h.field}" for h in hits))

    if "jev" in systems or "structured" in systems or "logprobs" in systems:
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise BenchmarkError("OPENROUTER_API_KEY is not set")
    if any(s in systems for s in ("structured", "logprobs")):
        _ensure_litellm()

    output_dir = Path(args.output) if args.output else (
        config.results_dir / time.strftime("%Y%m%d-%H%M%S"))
    output_dir.mkdir(parents=True, exist_ok=True)
    pricing = load_pricing(config.pricing)
    aggregates: list[SuiteAggregate] = []
    log_paths: list[Path] = []
    frozen: dict[str, dict] = {}

    for suite in suites:
        if suite.manifest is not None and suite.manifest.exists():
            frozen[suite.name] = json.loads(suite.manifest.read_text())
        for system in systems:
            print(f"running {suite.name} / {system} ({repeats} repeats)...",
                  file=sys.stderr)
            log_path = output_dir / f"{_safe_name(suite.name)}.{system}.jsonl"
            log_paths.append(log_path)
            with JsonlLogger(str(log_path)) as logger:
                if system == "jev":
                    records = run_jev_suite(
                        suite, config, repeats=repeats,
                        include_excluded=include_excluded, logger=logger,
                        delay=args.delay, limit=args.limit)
                else:
                    if args.structured_model and system == "structured":
                        config = dataclasses.replace(
                            config, structured_model=args.structured_model)
                    if args.logprob_model and system == "logprobs":
                        config = dataclasses.replace(
                            config, logprob_model=args.logprob_model)
                    records = run_baseline_suite(
                        suite, config, system, repeats=repeats,
                        include_excluded=include_excluded, logger=logger,
                        delay=args.delay, limit=args.limit)
            aggregates.append(aggregate(suite, system, records, repeats))
            agg = aggregates[-1]
            k, n = agg.strict_counts(agg.headline_cases())
            print(f"  {suite.name}/{system}: {k}/{n} cases passed on all "
                  f"{repeats} repeat(s)", file=sys.stderr)

    aggregates = build_aggregates_from_logs(config, log_paths)
    text = render_report(config, aggregates, pricing, output_dir=output_dir,
                         frozen=frozen)
    print(text)
    print(f"report written to {output_dir / 'report.md'}", file=sys.stderr)
    return 0


def _latest_results_dir(root: Path) -> Path:
    if not root.exists():
        raise BenchmarkError(f"results directory not found: {root}")
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        raise BenchmarkError(f"no result directories under {root}")
    return max(dirs, key=lambda p: p.stat().st_mtime)


def _frozen_manifests(config: BenchmarkConfig) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for suite in config.suites:
        if suite.manifest is not None and suite.manifest.exists():
            out[suite.name] = json.loads(suite.manifest.read_text())
    return out


def command_report(args) -> int:
    config = load_benchmark_config()
    input_dir = (Path(args.input) if args.input
                 else _latest_results_dir(config.results_dir))
    paths = sorted(input_dir.glob("*.jsonl"))
    if not paths:
        raise BenchmarkError(f"no JSONL logs in {input_dir}")
    aggregates = build_aggregates_from_logs(config, paths)
    output_dir = Path(args.output) if args.output else input_dir
    pricing = load_pricing(config.pricing)
    text = render_report(config, aggregates, pricing, output_dir=output_dir,
                         frozen=_frozen_manifests(config))
    print(text)
    print(f"report written to {output_dir / 'report.md'}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="benchmark.py",
        description="Run the example benchmarks (Jev + LiteLLM baselines).")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run one or more benchmark suites")
    run.add_argument("--suite", action="append", default=None,
                     help="suite name from examples/benchmark.toml (repeatable)")
    run.add_argument("--repeats", type=int, default=None,
                     help="runs per case (default: benchmark.toml)")
    run.add_argument("--systems", default=None,
                     help="comma-separated: jev,structured,logprobs")
    run.add_argument("--include-excluded", dest="include_excluded",
                     action="store_true", default=None,
                     help="also run excluded probes")
    run.add_argument("--no-excluded", dest="include_excluded",
                     action="store_false",
                     help="do not run excluded probes")
    run.add_argument("--structured-model", default=None)
    run.add_argument("--logprob-model", default=None)
    run.add_argument("--output", default=None, help="results directory")
    run.add_argument("--delay", type=float, default=0.0,
                     help="seconds to sleep between baseline cases")
    run.add_argument("--limit", type=int, default=None,
                     help="only run the first N cases per suite (smoke tests)")
    run.add_argument("--allow-unfrozen", action="store_true",
                     help="run a suite even if its manifest is missing/stale")
    run.set_defaults(func=command_run)

    check = sub.add_parser("check", help="check leakage and frozen manifests")
    check.set_defaults(func=command_check)

    report = sub.add_parser("report", help="regenerate a report from JSONL logs")
    report.add_argument("--input", default=None,
                        help="directory containing JSONL logs (default: latest run)")
    report.add_argument("--output", default=None,
                        help="directory for report.md/report.json")
    report.set_defaults(func=command_report)

    freeze = sub.add_parser("freeze", help="write a suite manifest")
    freeze.add_argument("--suite", required=True)
    freeze.add_argument("--ref", default="v1")
    freeze.add_argument("--output", default=None)
    freeze.set_defaults(func=command_freeze)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except BenchmarkError as e:
        print(f"benchmark: {e}", file=sys.stderr)
        return 2
    except ConfigError as e:
        print(f"benchmark: config error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("benchmark: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
