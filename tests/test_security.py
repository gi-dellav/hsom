"""Security regressions: option injection, read-tier audit, anti-repeat."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from hsom.config import (
    Command, EnvConfig, PathSlot, effective_threshold, load_config, node_risk,
)
from hsom.discovery import discover
from hsom.dispatcher import PlannedAction
from hsom.executor import ExecutionError, execute

ROOT = Path(__file__).resolve().parents[1]


def test_option_shaped_filename_is_not_a_candidate(tmp_path):
    (tmp_path / "main.py").write_text("ORIGINAL")
    (tmp_path / "--output-file=main.py").write_text("attacker")
    slot = PathSlot(name="target", kind="files", optional=True)
    assert discover(slot, str(tmp_path)) == ["main.py"]


def test_option_shaped_path_is_rejected_before_execution(tmp_path, monkeypatch):
    main = tmp_path / "main.py"
    main.write_text("ORIGINAL")
    (tmp_path / "--output-file=main.py").write_text("attacker")

    cfg = EnvConfig(commands=(
        Command(name="lint", description="lint",
                argv=("ruff", "check", "{path:target}"),
                paths=(PathSlot(name="target", kind="files", optional=True),)),
    ))
    action = PlannedAction(command="lint", subcommand=None, paths={
        "target": "--output-file=main.py"}, confidence=0.99, risk="read")

    def boom(*a, **k):
        raise AssertionError("refused action must not reach subprocess")

    monkeypatch.setattr("subprocess.run", boom)
    with pytest.raises(ExecutionError, match="may not start with '-'"):
        execute(cfg, action, str(tmp_path))
    assert main.read_text() == "ORIGINAL"


def test_code_execution_commands_are_not_read_tier():
    for rel in ("environment.toml.example",
                "examples/python-qa/environment.toml"):
        cfg = load_config(str(ROOT / rel))
        for name in ("python", "pytest"):
            cmd = cfg.get_command(name)
            if cmd is not None:
                assert node_risk(cfg, cmd, None) != "read", (rel, name)


def test_benchmark_configs_set_temperature_explicitly():
    for rel in ("examples/git-workflow/environment.toml",
                "examples/python-qa/environment.toml"):
        cfg = load_config(str(ROOT / rel))
        assert cfg.temperature == 0.0, rel


def test_example_configs_preserve_stake_nesting():
    for rel in ("environment.toml.example",
                "examples/git-workflow/environment.toml",
                "examples/python-qa/environment.toml"):
        cfg = load_config(str(ROOT / rel))
        for cmd in cfg.commands:
            for sub in (None, *cmd.subcommands):
                risk = node_risk(cfg, cmd, sub)
                bar, _ = effective_threshold(cfg, cmd, sub, risk)
                tier = cfg.risk_thresholds.get(risk, cfg.min_confidence)
                assert bar >= tier, (rel, cmd.name,
                                     getattr(sub, "name", None))


def test_read_tier_audit_exists():
    audit = (ROOT / "READ_TIER_AUDIT.md").read_text()
    for name in ("git status", "git log", "git diff", "git branch",
                 "ls", "ruff check", "ruff format --check", "pytest", "python"):
        assert name in audit


def _cli_args():
    return SimpleNamespace(
        request="run tests", cwd=".", min_confidence=None, max_history=None,
        temperature=None, continue_threshold=None, show_probs=False,
        dry_run=False, stop_on_error=True,
    )


def test_cli_anti_repeat_blocks_duplicate_before_execution(config, monkeypatch):
    from hsom import cli
    from conftest import FakeNoul

    action = PlannedAction(command="pytest", subcommand=None, confidence=0.99,
                           risk="read")
    outcome = SimpleNamespace(ok=True, action=action, reason="ok",
                              confidence=0.99)
    response = SimpleNamespace(answers={"__continue__": FakeNoul(0.99)})

    monkeypatch.setattr(cli, "dispatch",
                        lambda *a, **k: (outcome, None, {}, response))
    monkeypatch.setattr(cli, "_retry_after_repeat", lambda *a, **k: None)

    calls = {"exec": 0}

    def fake_execute(cfg, act, cwd):
        calls["exec"] += 1
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli, "execute", fake_execute)

    rc = cli.run_sequence(config, _cli_args(), budget=3)
    assert rc == cli.EXIT_ABSTAIN
    assert calls["exec"] == 1  # duplicate was blocked before executing
