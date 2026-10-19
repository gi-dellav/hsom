"""Opt-in structured JSONL run logging.

One JSON object per line. Two event kinds per executed step:

- ``plan``: the request/state summary, the planned action (node, flags, paths,
  confidence, risk, threshold, per-layer decisions) and whether Jev was asked
  to continue.
- ``result``: the resolved argv plus how it ended (dry-run, declined, refused,
  or executed with returncode/stdout/stderr) and an optional ``error_kind``.

Eval mode emits one ``eval`` event per case instead. Logging is entirely
opt-in (``--log PATH``): nothing is written unless a path is given.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, TextIO


def _layer_obj(layer) -> dict:
    return {
        "question_id": layer.question_id,
        "choice": layer.choice,
        "probability": layer.probability,
        "confidence": layer.confidence,
        "probabilities": dict(layer.probabilities or {}),
    }


def _action_fields(action) -> dict:
    if action is None:
        return {
            "command": None, "subcommand": None, "flags": [], "flag_values": {},
            "paths": {}, "risk": None, "threshold": None, "threshold_source": None,
            "layers": [],
        }
    return {
        "command": action.command,
        "subcommand": action.subcommand,
        "flags": list(action.flags),
        "flag_values": dict(action.flag_values),
        "paths": dict(action.paths),
        "risk": action.risk,
        "threshold": action.threshold,
        "threshold_source": action.threshold_source,
        "layers": [_layer_obj(x) for x in action.layers],
    }


def plan_event(step: int, request: str, cwd: str, outcome, context=None, *,
               continue_asked: bool = False, continue_value: float | None = None,
               continue_threshold: float | None = None,
               continue_threshold_source: str | None = None,
               max_steps: int | None = None, max_history: int | None = None,
               history_len: int = 0, repeat_retry: bool = False,
               temperature: float | None = None) -> dict:
    """Build a ``plan`` event from a PlanOutcome."""
    ev = {
        "type": "plan",
        "ts": time.time(),
        "step": step,
        "request": request,
        "cwd": cwd,
        "ok": outcome.ok,
        "reason": outcome.reason,
        "confidence": outcome.confidence,
        "temperature": temperature,
        "continue_asked": continue_asked,
        "continue": continue_value,
        "continue_threshold": continue_threshold,
        "continue_threshold_source": continue_threshold_source,
        "max_steps": max_steps,
        "max_history": max_history,
        "history_len": history_len,
        "repeat_retry": repeat_retry,
    }
    ev.update(_action_fields(outcome.action))
    if context:
        ev["cwd_files"] = context.get("cwd_files")
        ev["cwd_dirs"] = context.get("cwd_dirs")
    return ev


def result_event(step: int, argv: list[str] | None = None, *,
                 dry_run: bool = False, declined: bool = False,
                 returncode: int | None = None, stdout: str = "",
                 stderr: str = "", error: str | None = None,
                 stop_reason: str | None = None,
                 error_kind: str | None = None) -> dict:
    """Build a ``result`` event for an attempted/executed step."""
    return {
        "type": "result",
        "ts": time.time(),
        "step": step,
        "argv": list(argv) if argv is not None else None,
        "dry_run": dry_run,
        "declined": declined,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "error": error,
        "error_kind": error_kind,
        "stop_reason": stop_reason,
    }


def eval_event(case, result, *, temperature: float | None = None,
               run_index: int = 1, repeats: int = 1, system: str = "jev",
               suite: str | None = None, model: str | None = None,
               input_tokens: int | None = None,
               output_tokens: int | None = None,
               latency_ms: float | None = None,
               excluded: bool | None = None,
               wrong_plan: bool | None = None,
               logprob_fallbacks: int | None = None) -> dict:
    """Build an ``eval`` event from an EvalTestResult."""
    from hsom.eval import _join

    def fmt(steps):
        if steps is None:
            return None
        return " ; ".join(_join(a) for a in steps)

    if excluded is None:
        excluded = bool(getattr(case, "excluded", False))
    if wrong_plan is None:
        wrong_plan = bool(getattr(case, "wrong_plan", False))
    return {
        "type": "eval",
        "ts": time.time(),
        "system": system,
        "suite": suite,
        "run_index": run_index,
        "repeats": repeats,
        "name": case.name,
        "input": case.input,
        "expected": fmt(case.expected),
        "actual": fmt(result.actual),
        "passed": result.passed,
        "reason": result.reason,
        "error_kind": result.error_kind,
        "confidence": result.confidence,
        "risk": result.risk,
        "steps": len(result.actual) if result.actual is not None else 0,
        "temperature": temperature,
        "model": model if model is not None else getattr(result, "model", None),
        "input_tokens": (input_tokens if input_tokens is not None
                         else getattr(result, "input_tokens", None)),
        "output_tokens": (output_tokens if output_tokens is not None
                          else getattr(result, "output_tokens", None)),
        "latency_ms": (latency_ms if latency_ms is not None
                       else getattr(result, "latency_ms", None)),
        "excluded": excluded,
        "wrong_plan": wrong_plan,
        "exclude_reason": getattr(case, "exclude_reason", None),
        "logprob_fallbacks": (logprob_fallbacks if logprob_fallbacks is not None
                              else getattr(result, "logprob_fallbacks", 0)),
    }


def run_event(*, suite: str, label: str = "regression",
              eval_file: str | None = None, eval_sha256: str | None = None,
              env_file: str | None = None, env_sha256: str | None = None,
              model: str | None = None, provider: str | None = None,
              temperature: float | None = None, repeats: int = 1,
              system: str = "jev", hsom_version: str | None = None,
              git_commit: str | None = None, frozen: bool = False,
              frozen_ref: str | None = None) -> dict:
    """Build a ``run`` event describing one benchmark execution."""
    return {
        "type": "run",
        "ts": time.time(),
        "system": system,
        "suite": suite,
        "label": label,
        "eval_file": eval_file,
        "eval_sha256": eval_sha256,
        "env_file": env_file,
        "env_sha256": env_sha256,
        "model": model,
        "provider": provider,
        "temperature": temperature,
        "repeats": repeats,
        "hsom_version": hsom_version,
        "git_commit": git_commit,
        "frozen": frozen,
        "frozen_ref": frozen_ref,
    }


class JsonlLogger:
    """Append-only JSONL writer. Use as a context manager or call close().

    Log files are created and kept at mode 0600 (owner read/write only).
    """

    def __init__(self, path: str):
        self.path = path
        self._f: TextIO | None = None

    def log(self, event: dict) -> None:
        if self._f is None:
            fd = os.open(
                self.path,
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o600,
            )
            try:
                os.fchmod(fd, 0o600)
            except (AttributeError, OSError):
                # Windows and unusual filesystems may not support fchmod.
                pass
            self._f = os.fdopen(fd, "a", encoding="utf-8")
        self._f.write(json.dumps(event, default=str) + "\n")
        self._f.flush()

    def close(self) -> None:
        if self._f is not None:
            self._f.close()
            self._f = None

    def __enter__(self) -> "JsonlLogger":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
