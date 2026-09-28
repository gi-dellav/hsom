"""jevdo — Jev, Do. Connects Jev to your shell via a strict allowlist.

Python library entry point::

    from jevdo import Harness

    h = Harness(env="environment.toml")
    result = h.run("brief git history", dry_run=True)

The ``jevdo`` CLI (``jevdo.cli:main``) uses the same machinery.
"""

from jevdo.api import Harness, OnConfirm, RunResult
from jevdo.config import (
    Command,
    ConfigError,
    EnvConfig,
    Flag,
    PathSlot,
    Subcommand,
    load_config,
)
from jevdo.dispatcher import LayerDetail, PlannedAction, PlanOutcome, StepOutcome
from jevdo.eval import EvalCase, EvalError, EvalSummary, EvalTestResult, load_eval
from jevdo.executor import ExecutionError, ExecutionResult

__all__ = [
    "Harness",
    "OnConfirm",
    "RunResult",
    "PlannedAction",
    "PlanOutcome",
    "StepOutcome",
    "LayerDetail",
    "ExecutionResult",
    "ExecutionError",
    "EnvConfig",
    "Command",
    "Subcommand",
    "Flag",
    "PathSlot",
    "ConfigError",
    "EvalCase",
    "EvalError",
    "EvalSummary",
    "EvalTestResult",
    "load_config",
    "load_eval",
]

__version__ = "0.1.0"
