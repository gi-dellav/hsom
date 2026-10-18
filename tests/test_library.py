"""Harness library API: construction, get_cwd, plan/resolve/run/eval, on_confirm."""

import types

import pytest

from conftest import FakeChoice, FakeNoul, sample_config
from hsom import Harness, RunResult
from hsom.api import apply_provider_overrides
from hsom.config import ConfigError, EnvConfig
from hsom.dispatcher import PlannedAction


class FakeResp:
    def __init__(self, answers):
        self.answers = answers


def _pytest_client(continue_value=None):
    answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}
    if continue_value is not None:
        answers["__continue__"] = FakeNoul(continue_value)

    class FakeClient:
        def system_one(self, **kw):
            return FakeResp(dict(answers))

    return FakeClient()


def test_construct_from_envconfig_and_dict():
    cfg = sample_config()
    assert Harness(env=cfg).config is cfg

    h = Harness(env={"meta": {"model": "jev-latest"},
                     "command": [{"name": "pytest", "description": "t",
                                   "argv": ["pytest", "-q"]}]})
    assert isinstance(h.config, EnvConfig)
    assert h.config.get_command("pytest") is not None

    with pytest.raises(ConfigError):
        Harness(env={"meta": {}, "command": []})


def test_construct_from_path_and_provider_override(tmp_path):
    p = tmp_path / "environment.toml"
    p.write_text('[meta]\nmodel = "jev-latest"\n[[command]]\n'
                 'name = "pytest"\ndescription = "t"\nargv = ["pytest", "-q"]\n')
    h = Harness(env=str(p), provider="openrouter")
    assert h.config.provider == "openrouter"
    assert h.config.effective_base_url == "https://openrouter.ai/api"

    with pytest.raises(ConfigError):
        Harness(env=str(tmp_path / "missing.toml"))


def test_apply_provider_overrides_rejects_bad():
    with pytest.raises(ConfigError, match="--provider"):
        apply_provider_overrides(sample_config(), "bogus")
    with pytest.raises(ConfigError, match="--base-url"):
        apply_provider_overrides(sample_config(), None, "notaurl")


def test_get_cwd_default_set_and_fn():
    h = Harness(env=sample_config(), cwd="/tmp/a")
    assert h.get_cwd() == "/tmp/a" == h.cwd
    h.set_cwd("/tmp/b")
    assert h.get_cwd() == "/tmp/b"

    h.set_cwd_fn(lambda: "/tmp/dyn")
    assert h.get_cwd() == "/tmp/dyn"
    h.set_cwd_fn(None)
    assert h.get_cwd() == "/tmp/b"

    h2 = Harness(env=sample_config(), get_cwd=lambda: "/tmp/ctor")
    assert h2.get_cwd() == "/tmp/ctor"

    # instance-attribute override (user style)
    h2.get_cwd = lambda: "/tmp/shadow"
    assert h2._resolve_cwd(None) == "/tmp/shadow"
    assert h2._resolve_cwd("/explicit") == "/explicit"


def test_get_cwd_subclass_override():
    class MyH(Harness):
        def get_cwd(self):
            return "/sub/class"

    assert MyH(env=sample_config())._resolve_cwd(None) == "/sub/class"


def test_run_uses_dynamic_cwd_per_call(workdir):
    seen = []

    class FakeClient:
        def system_one(self, **kw):
            seen.append(kw["state"])
            return FakeResp({"__command__": FakeChoice(
                "pytest", {"pytest": 1.0}, 0.99)})

    h = Harness(env=sample_config(), client=FakeClient())
    h.set_cwd_fn(lambda: workdir)
    r = h.run("run tests", dry_run=True)
    assert isinstance(r, RunResult) and r.ok
    assert r.argv_list == [["pytest", "-q"]]
    assert r.stop_reason == "max_steps reached"


def test_plan_and_resolve(workdir):
    h = Harness(env=sample_config(), cwd=workdir,
                client=_pytest_client())
    outcome = h.plan("run tests")
    assert outcome.ok
    assert h.resolve(outcome.action) == ["pytest", "-q"]


def test_plan_full_returns_tuple(workdir):
    h = Harness(env=sample_config(), cwd=workdir,
                client=_pytest_client())
    outcome, questions, context, response = h.plan_full("run tests")
    assert outcome.ok and "__command__" in questions


def test_execute_dry_run_and_real(workdir):
    h = Harness(env=sample_config(), cwd=workdir)
    action = PlannedAction(command="pytest", subcommand=None,
                           confidence=0.9, risk="read")
    res = h.execute(action, dry_run=True)
    assert res.argv == ["pytest", "-q"] and res.dry_run


def test_run_dry_run_single_and_chain(workdir):
    h = Harness(env=sample_config(), cwd=workdir,
                client=_pytest_client(continue_value=0.9))
    r = h.run("run tests", dry_run=True, max_steps=2, repeat_guard=False)
    assert r.ok and len(r.steps) == 2
    assert all(s.dry_run for s in r.steps)
    assert r.returncode == 0


def test_run_abstain_returns_runresult(workdir):
    class AbstainClient:
        def system_one(self, **kw):
            return FakeResp({"__command__": FakeChoice(
                "none_of_the_above", {"none_of_the_above": 1.0}, 0.99)})

    h = Harness(env=sample_config(), cwd=workdir, client=AbstainClient())
    r = h.run("launch rockets", dry_run=True)
    assert isinstance(r, RunResult)
    assert not r.ok and r.steps == ()
    assert r.stop_reason.startswith("abstained:")


def test_run_write_declined_by_default_and_approved(workdir):
    (workdir_path := __import__("pathlib").Path(workdir))
    (workdir_path / "a.txt").write_text("x")

    class AddClient:
        def system_one(self, **kw):
            return FakeResp({
                "__command__": FakeChoice("git", {"git": 1.0}, 0.9),
                "__subcommand__:git": FakeChoice("add", {"add": 1.0}, 0.9),
                "path.git.add.path": FakeChoice(
                    "README.md", {"README.md": 1.0}, 0.9),
            })

    h = Harness(env=sample_config(default_risk="write"), cwd=workdir,
                client=AddClient())
    r = h.run("stage readme", dry_run=False,
              execute_fn=lambda a, c: (["git", "add", "README.md"], 0, "", ""))
    assert r.declined and not r.ok and r.stop_reason == "declined by user"

    seen = {}

    def approve(action, argv):
        seen["argv"] = argv
        assert action.risk == "write"
        return True

    r2 = h.run("stage readme", on_confirm=approve,
               execute_fn=lambda a, c: (["git", "add", "README.md"], 0, "ok", ""))
    assert r2.ok and not r2.declined
    assert seen["argv"] == ["git", "add", "README.md"]
    assert r2.steps[0].stdout == "ok"


def test_run_stops_on_error(workdir):
    h = Harness(env=sample_config(), cwd=workdir,
                client=_pytest_client(continue_value=0.9))
    r = h.run("run tests", max_steps=3,
              execute_fn=lambda a, c: (["pytest", "-q"], 1, "", "boom"))
    assert not r.ok and "exited 1" in r.stop_reason

    r2 = h.run("run tests", max_steps=3, stop_on_error=False,
               repeat_guard=False,
               execute_fn=lambda a, c: (["pytest", "-q"], 1, "", "boom"))
    # stop_on_error=False + guard off: full budget runs (3 identical steps)
    assert len(r2.steps) == 3 and not r2.ok


def test_run_repeat_guard_stops_duplicate(workdir):
    h = Harness(env=sample_config(), cwd=workdir,
                client=_pytest_client(continue_value=0.9))
    r = h.run("run tests", max_steps=3,
              execute_fn=lambda a, c: (["pytest", "-q"], 0, "", ""))
    assert "repeats step 1" in r.stop_reason
    # only the first execution kept (retry produced same argv)
    assert len(r.steps) == 1


def test_run_no_api_key_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    h = Harness(env=sample_config(), cwd=str(tmp_path))
    # execute_fn bypasses the key requirement
    r = h.run("run tests", client=_pytest_client(),
              execute_fn=lambda a, c: (["pytest", "-q"], 0, "", ""))
    assert r.ok
    with pytest.raises(ConfigError, match="no API key"):
        h.run("run tests", client=None)


def test_eval_never_executes(workdir, tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("must not execute")))
    ev = tmp_path / "eval.toml"
    ev.write_text('[[test]]\nname = "t"\ninput = "run tests"\n'
                  'expected = "pytest -q"\n')
    h = Harness(env=sample_config(), cwd=workdir,
                client=_pytest_client())
    summary = h.eval(str(ev))
    assert summary.ok and summary.passed == 1


def test_eval_accepts_cases_and_multistep(workdir):
    from hsom.eval import EvalCase
    calls = {"n": 0}

    def fake_execute(action, cwd):
        raise AssertionError("must not execute")

    import hsom.dispatcher as disp

    orig = disp.dispatch

    def fake_dispatch(cfg, request, cwd=".", **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            a = PlannedAction(command="git", subcommand="add",
                              paths={"path": "README.md"},
                              confidence=0.9, risk="read")
            resp = types.SimpleNamespace(
                answers={"__continue__": FakeNoul(0.9)})
        else:
            a = PlannedAction(command="git", subcommand="status",
                              confidence=0.9, risk="read")
            resp = types.SimpleNamespace(answers={})
        from hsom.dispatcher import PlanOutcome
        return PlanOutcome(True, a, "ok", 0.9), None, None, resp

    disp.dispatch = fake_dispatch
    try:
        from hsom import Harness as H2
        h = H2(env=sample_config(), cwd=workdir,
               client=_pytest_client())
        case = EvalCase(name="t", input="x",
                        expected=(("git", "add", "README.md"),
                                  ("git", "status")),
                        expected_str=("git add README.md", "git status"))
        summary = h.eval([case])
        assert summary.ok
    finally:
        disp.dispatch = orig


def test_context_manager_owns_client(monkeypatch):
    from hsom import client as client_mod

    closed = {}

    class FakeOwned:
        def close(self):
            closed["yes"] = True

    monkeypatch.setattr(client_mod, "create_client",
                        lambda *a, **k: FakeOwned())
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    h = Harness(env=sample_config())
    with h as hh:
        assert hh._owned_client is not None
    assert closed.get("yes") is True


def test_harness_forwards_api_key_and_timeout(monkeypatch, workdir):
    """Direct plan()/run() must honor constructor api_key/timeout (not only `with`)."""
    from hsom import client as client_mod

    seen = {}
    closed = []

    class FakeClient:
        def system_one(self, **kw):
            return FakeResp({"__command__": FakeChoice(
                "pytest", {"pytest": 1.0}, 0.99)})

        def close(self):
            closed.append(True)

    def fake_create(cfg, **kw):
        seen.update(kw)
        return FakeClient()

    monkeypatch.setattr(client_mod, "create_client", fake_create)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    h = Harness(env=sample_config(), cwd=workdir, api_key="SECRET", timeout=7)
    outcome = h.plan("run tests")
    assert outcome.ok
    assert seen == {"api_key": "SECRET", "timeout": 7}
    assert closed == [True]
