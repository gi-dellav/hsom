"""hsom — Jev, Do. Connects Jev to your shell via a strict allowlist.

Python library entry point::

    from hsom import Harness

    h = Harness(env="environment.toml")
    result = h.run("brief git history", dry_run=True)

The ``hsom`` CLI (``hsom.cli:main``) uses the same machinery.
"""

from hsom.api import Harness, OnConfirm, RunResult
from hsom.config import (
    Command,
    ConfigError,
    EnvConfig,
    Flag,
    PathSlot,
    Subcommand,
    load_config,
)
from hsom.dispatcher import LayerDetail, PlannedAction, PlanOutcome, StepOutcome
from hsom.eval import EvalCase, EvalError, EvalSummary, EvalTestResult, load_eval
from hsom.executor import (
    CommandNotFound,
    ExecutionError,
    ExecutionResult,
    ExecutionTimeout,
    SpawnError,
)

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
    "ExecutionTimeout",
    "CommandNotFound",
    "SpawnError",
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
