"""CLI exit-code taxonomy and structured error kinds."""

import json
from types import SimpleNamespace

from typesafe_sdk import TypeSafeAPIConnectionError

from hsom import cli
from hsom.dispatcher import PlannedAction
from hsom.executor import CommandNotFound, ExecutionTimeout
from hsom.runlog import JsonlLogger


def _args(tmp_path, **over):
    base = dict(cwd=str(tmp_path), dry_run=False)
    base.update(over)
    return SimpleNamespace(**base)


def _write(path, text):
    path.write_text(text)
    return str(path)


def _env_file(tmp_path):
    return _write(tmp_path / "environment.toml", """\
[meta]
model = "jev-latest"
[[command]]
name = "pytest"
description = "tests"
argv = ["pytest", "-q"]
""")


def test_declined_write_exits_declined(monkeypatch, config, tmp_path):
    monkeypatch.setattr(cli, "confirm", lambda action, argv: False)
    monkeypatch.setattr(
        cli, "execute",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not run")))
    action = PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                           risk="write")
    assert cli.run_action(config, _args(tmp_path), action) == cli.EXIT_DECLINED


def test_pre_execution_refusal_exits_refused(config, tmp_path):
    action = PlannedAction(command="git", subcommand="log",
                           flags=("--evil",), confidence=0.9, risk="read")
    assert cli.run_action(config, _args(tmp_path), action) == cli.EXIT_REFUSED


def test_timeout_exits_timeout(monkeypatch, config, tmp_path):
    def boom(*a, **k):
        raise ExecutionTimeout("timed out")

    monkeypatch.setattr(cli, "execute", boom)
    action = PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                           risk="read")
    assert cli.run_action(config, _args(tmp_path), action) == cli.EXIT_TIMEOUT


def test_spawn_failure_exits_spawn(monkeypatch, config, tmp_path):
    def boom(*a, **k):
        raise CommandNotFound("executable not found: 'pytest'")

    monkeypatch.setattr(cli, "execute", boom)
    action = PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                           risk="read")
    assert cli.run_action(config, _args(tmp_path), action) == cli.EXIT_SPAWN


def test_unexpected_error_exits_internal(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def boom(*a, **k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(cli, "dispatch", boom)
    rc = cli.main(["--env", _env_file(tmp_path), "--cwd", str(tmp_path),
                   "run tests"])
    assert rc == cli.EXIT_INTERNAL
    assert "internal error" in capsys.readouterr().err


def test_eval_provider_error_exits_jev_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    env = _env_file(tmp_path)
    ev = _write(tmp_path / "eval.toml",
                '[[test]]\ninput = "run tests"\nexpected = "pytest -q"\n')

    def boom(*a, **k):
        raise TypeSafeAPIConnectionError("no route")

    monkeypatch.setattr("hsom.dispatcher.dispatch", boom)
    rc = cli.main(["--env", env, "--cwd", str(tmp_path), "--eval", ev])
    assert rc == cli.EXIT_JEV_ERROR
    assert "provider errors" in capsys.readouterr().err


def test_timeout_logs_error_kind(monkeypatch, config, tmp_path):
    path = tmp_path / "run.jsonl"
    logger = JsonlLogger(str(path))
    try:
        def boom(*a, **k):
            raise ExecutionTimeout("timed out")

        monkeypatch.setattr(cli, "execute", boom)
        action = PlannedAction(command="pytest", subcommand=None,
                               confidence=0.9, risk="read")
        assert cli.run_action(config, _args(tmp_path), action,
                              logger=logger) == cli.EXIT_TIMEOUT
    finally:
        logger.close()
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert events[-1]["error_kind"] == "timeout"
