"""Risk, thresholds, valued flags, multi-slot planning, confirm, sequence."""

import pytest

from hsom.config import (
    Command, EnvConfig, Flag, PathSlot, Subcommand,
    effective_threshold, node_risk,
)
from hsom.dispatcher import (
    PlannedAction, _clip_history, continue_requested, dispatch,
    dispatch_sequence, plan_from_answers,
)
from conftest import FakeChoice, FakeNoul, sample_config


def _cmd(choice="git", conf=0.9):
    return {"__command__": FakeChoice(choice, {choice: 0.9, "none_of_the_above": 0.1}, conf)}


def _rich_config(**over):
    cmds = (
        Command(name="git", description="vcs", argv=None, risk="read", subcommands=(
            Subcommand(name="add", description="stage",
                       argv=("git", "add", "{path:src}"),
                       paths=(PathSlot(name="src", kind="files"),),
                       risk="write"),
            Subcommand(name="reset", description="nuke",
                       argv=("git", "reset", "--hard"), risk="destructive"),
        )),
        Command(name="ls", description="list", argv=("ls", "--fmt", "{value}", "{path:out}"),
                risk="read",
                flags=(Flag("--fmt", "fmt", ("--fmt={value}",),
                            values=("json", "plain"),
                            value_descriptions={"json": "machine"}),),
                paths=(PathSlot(name="out", kind="dirs", optional=True),)),
    )
    kw = dict(model="jev-latest", min_confidence=0.5, timeout=60.0, commands=cmds,
              risk_thresholds={"read": 0.5, "write": 0.7, "destructive": 0.9})
    kw.update(over)
    return EnvConfig(**kw)


@pytest.fixture
def rich():
    return _rich_config()


def _rich_ctx():
    return {"candidates": {(("git.add", "src")): ["a.txt"],
                           "git.add": ["a.txt"],
                           (("ls", "out")): ["d"],
                           "ls": ["d"]},
            "cwd_files": ["a.txt"], "cwd_dirs": ["d"]}


def test_risk_inheritance_and_threshold_resolution():
    cfg = sample_config()
    git = cfg.get_command("git")
    assert node_risk(cfg, git, None) == "read"  # meta default
    cfg2 = sample_config(default_risk="write")
    assert node_risk(cfg2, git, None) == "write"
    bar, src = effective_threshold(cfg2, git, None, "write")
    assert bar == 0.5 and src == "global"
    cfg3 = _rich_config()
    g3 = cfg3.get_command("git")
    add = [s for s in g3.subcommands if s.name == "add"][0]
    bar, src = effective_threshold(cfg3, g3, add, "write")
    assert bar == 0.7 and src == "risk write"
    cfg4 = _rich_config()
    cmds = list(cfg4.commands)
    assert effective_threshold(cfg4, cmds[0], add, "write", cli_override=0.1) == (0.1, "cli --min-confidence")


def test_node_threshold_cannot_weaken_risk_tier():
    add = Subcommand(name="add", description="stage",
                     argv=("git", "add", "{path:src}"),
                     paths=(PathSlot(name="src", kind="files"),),
                     risk="write", min_confidence=0.6)
    cfg = EnvConfig(
        commands=(Command(name="git", description="vcs", argv=None,
                          subcommands=(add,)),),
        risk_thresholds={"read": 0.5, "write": 0.7, "destructive": 0.9},
    )
    git = cfg.get_command("git")
    # 0.6 < write tier 0.7 => tier wins (nesting invariant holds)
    assert effective_threshold(cfg, git, add, "write") == (0.7, "risk write")

    stricter = Subcommand(name="add", description="stage",
                          argv=("git", "add", "{path:src}"),
                          paths=(PathSlot(name="src", kind="files"),),
                          risk="write", min_confidence=0.8)
    cfg2 = EnvConfig(
        commands=(Command(name="git", description="vcs", argv=None,
                          subcommands=(stricter,)),),
        risk_thresholds={"read": 0.5, "write": 0.7, "destructive": 0.9},
    )
    # 0.8 > tier 0.7 => node wins, still stricter than the tier
    assert effective_threshold(cfg2, cfg2.get_command("git"), stricter,
                               "write") == (0.8, "node git.add")

    # Parent overrides inherit to subcommands and obey the same floor.
    parent = Command(name="git", description="vcs",
                     argv=("git",),
                     min_confidence=0.6,
                     subcommands=(Subcommand(name="add", description="stage",
                                             argv=("git", "add"),
                                             risk="write"),))
    cfg3 = EnvConfig(
        commands=(parent,),
        risk_thresholds={"read": 0.5, "write": 0.7, "destructive": 0.9},
    )
    assert effective_threshold(cfg3, parent, parent.subcommands[0],
                               "write") == (0.7, "risk write")


def test_write_below_risk_threshold_abstains(rich):
    ans = (_cmd("git", 0.6)
           | {"__subcommand__:git": FakeChoice("add", {"add": 0.9}, 0.6),
              "path.git.add.src": FakeChoice("a.txt", {"a.txt": 0.9}, 0.6)})
    out = plan_from_answers(rich, ans, _rich_ctx())
    assert not out.ok and "0.70 (risk write)" in out.reason


def test_multislot_and_valued_flag_planning(rich):
    ans = ({"__command__": FakeChoice("ls", {"ls": 0.95}, 0.95)}
           | {"flag.ls.--fmt": FakeNoul(0.9),
              "flagval.ls.--fmt": FakeChoice("json", {"json": 0.9}, 0.92),
              "path_stated.ls.out": FakeNoul(0.9),
              "path.ls.out": FakeChoice("d", {"d": 0.9}, 0.93)})
    out = plan_from_answers(rich, ans, _rich_ctx())
    assert out.ok, out.reason
    assert out.action.flag_values == {"--fmt": "json"}
    assert out.action.paths == {"out": "d"}
    assert out.action.risk == "read"


def test_valued_flag_none_means_off(rich):
    ans = ({"__command__": FakeChoice("ls", {"ls": 0.95}, 0.95)}
           | {"flag.ls.--fmt": FakeNoul(0.9),
              "flagval.ls.--fmt": FakeChoice("none_of_the_above", {"none_of_the_above": 0.9}, 0.9),
              "path_stated.ls.out": FakeNoul(0.05)})
    out = plan_from_answers(rich, ans, _rich_ctx())
    assert out.ok and out.action.flags == () and out.action.describe() == "ls"


def test_confirm_accept_decline(monkeypatch):
    from hsom import cli
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _p: "y")
    a = PlannedAction(command="git", subcommand="add", flags=(), paths={"src": "a"},
                      confidence=0.8, risk="write")
    assert cli.confirm(a, ["git", "add", "a"]) is True
    monkeypatch.setattr("builtins.input", lambda _p: "n")
    assert cli.confirm(a, ["git", "add", "a"]) is False

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert cli.confirm(a, ["git", "add", "a"]) is False  # fail-closed


def test_sequence_stops_on_error():
    cfg = sample_config()
    calls = {"n": 0}

    class FakeResp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw): return FakeResp()

    def boom(action, cwd):
        calls["n"] += 1
        return (["pytest", "-q"], 1, "", "fail")

    steps, reason = dispatch_sequence(cfg, "run tests", ".", client=FakeClient(),
                                      execute_fn=boom, max_steps=3)
    assert len(steps) == 1 and "exited 1" in reason and calls["n"] == 1


def test_sequence_max_steps():
    cfg = sample_config()
    class FakeResp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99),
                   "__continue__": FakeNoul(0.9)}

    class FakeClient:
        def system_one(self, **kw): return FakeResp()

    def ok_exec(action, cwd):
        return (["pytest", "-q"], 0, "ok", "")

    # repeat_guard=False: canned fakes pin identical plans across steps;
    # the P2 anti-repeat retry only fires on live runs (guard on).
    steps, reason = dispatch_sequence(cfg, "run tests", ".", client=FakeClient(),
                                      execute_fn=ok_exec, max_steps=2,
                                      repeat_guard=False)
    assert len(steps) == 2 and reason == "max_steps reached"


def test_sequence_stops_when_jev_declines_to_continue():
    cfg = sample_config()
    calls = {"n": 0}

    class FakeResp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99),
                   "__continue__": FakeNoul(0.1)}

    class FakeClient:
        def system_one(self, **kw): return FakeResp()

    def ok_exec(action, cwd):
        calls["n"] += 1
        return (["pytest", "-q"], 0, "ok", "")

    steps, reason = dispatch_sequence(cfg, "run tests", ".", client=FakeClient(),
                                      execute_fn=ok_exec, max_steps=5)
    assert len(steps) == 1 and "Jev ended" in reason and calls["n"] == 1


def test_sequence_missing_continue_gate_stops():
    cfg = sample_config()

    class FakeResp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw): return FakeResp()

    def ok_exec(action, cwd):
        return (["pytest", "-q"], 0, "ok", "")

    steps, reason = dispatch_sequence(cfg, "run tests", ".", client=FakeClient(),
                                      execute_fn=ok_exec, max_steps=4)
    assert len(steps) == 1 and "Jev ended" in reason  # fail-closed


def test_sequence_max_steps_one_never_asks_continue():
    cfg = sample_config()
    seen = {}

    class FakeResp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw):
            seen["questions"] = kw.get("questions", {})
            return FakeResp()

    def ok_exec(action, cwd):
        return (["pytest", "-q"], 0, "ok", "")

    steps, reason = dispatch_sequence(cfg, "run tests", ".", client=FakeClient(),
                                      execute_fn=ok_exec, max_steps=1)
    assert len(steps) == 1 and reason == "max_steps reached"
    assert "__continue__" not in seen["questions"]


def test_clip_history():
    hist = [{"step": i} for i in range(1, 6)]
    assert _clip_history(hist, None) == hist
    assert _clip_history(hist, 2) == hist[-2:]
    assert _clip_history(hist, 0) == []
    assert _clip_history([], 3) == []


def test_continue_requested_fail_closed():
    class Resp:
        def __init__(self, answers): self.answers = answers

    assert continue_requested(Resp({"__continue__": FakeNoul(0.9)})) is True
    assert continue_requested(Resp({"__continue__": FakeNoul(0.49)})) is False
    assert continue_requested(Resp({})) is False
    assert continue_requested(Resp(None)) is False


def test_continue_requested_honors_threshold():
    class Resp:
        def __init__(self, answers): self.answers = answers

    ans = {"__continue__": FakeNoul(0.47)}
    assert continue_requested(Resp(ans)) is False  # default 0.5
    assert continue_requested(Resp(ans), 0.4) is True
    assert continue_requested(Resp(ans), 0.5) is False


def test_history_entry_carries_node_and_describe():
    from hsom.dispatcher import history_entry
    a = PlannedAction(command="ruff", subcommand="check",
                      paths={"target": "src/app.py"},
                      confidence=0.9, risk="read")
    h = history_entry(2, a, ["ruff", "check", "src/app.py"], 0, "ok", "")
    assert h["step"] == 2 and h["node"] == "ruff.check"
    assert h["describe"] == "ruff check src/app.py"
    assert h["argv"] == ["ruff", "check", "src/app.py"]
    assert h["returncode"] == 0


def test_dispatch_sends_step_and_history_state(config, tmp_path):
    seen = {}

    class Resp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw):
            seen["state"] = kw["state"]
            seen["questions"] = kw["questions"]
            return Resp()

    hist = [{"step": 1, "node": "git.add", "describe": "git add a",
             "argv": ["git", "add", "a"], "returncode": 0,
             "stdout_tail": "", "stderr_tail": ""}]
    dispatch(config, "run tests", str(tmp_path), client=FakeClient(),
             history=hist, max_steps=4, max_history=5, step_index=1)
    assert seen["state"]["step"] == 2
    assert seen["state"]["max_steps"] == 4
    assert seen["state"]["history"] == hist
    assert "step 2 of at most 4" in seen["questions"]["__command__"].instructions


def test_repeat_guard_retries_once_then_stops(config, tmp_path):
    """P2: identical step-2 argv triggers one nudged retry; a second repeat
    stops honestly without executing a duplicate."""
    import types

    plans = iter([
        ("pytest", None, 0.9),   # step 1
        ("pytest", None, 0.9),   # step 2: repeats step 1
        ("pytest", None, 0.9),   # retry: still repeats
    ])
    seen_hints = []

    class FakeClient:
        def system_one(self, **kw):
            if "hint" in kw.get("state", {}):
                seen_hints.append(kw["state"]["hint"])
            cmd, _sub, conf = next(plans)
            answers = {"__command__": FakeChoice(cmd, {cmd: 1.0}, conf),
                       "__continue__": FakeNoul(0.9)}
            return types.SimpleNamespace(answers=answers)

    def ok_exec(action, cwd):
        executed.append(list(action.describe().split()))
        return (["pytest", "-q"], 0, "ok", "")

    executed = []
    steps, reason = dispatch_sequence(
        config, "run tests", str(tmp_path), client=FakeClient(),
        execute_fn=ok_exec, max_steps=3, repeat_guard=True)
    assert len(steps) == 1
    assert executed == [["pytest"]]
    assert "repeats step 1" in reason
    assert len(seen_hints) == 1  # exactly one retry with the nudge


def test_repeat_guard_accepts_redirected_retry(config, tmp_path):
    """P2: when the retry plans a *different* argv, it is executed and kept."""
    import types

    script = iter([
        # (command choice, subcommand choice, planned node, continue noul)
        ("ruff", "check", "ruff.check", 0.9),    # step 1
        ("ruff", "check", "ruff.check", 0.9),    # step 2: repeats...
        ("ruff", "format", "ruff.format", 0.9),  # retry: switches node
    ])

    class FakeClient:
        def system_one(self, **kw):
            cmd, sub, node, conf = next(script)
            answers = {
                "__command__": FakeChoice(cmd, {cmd: 1.0}, conf),
                f"__subcommand__:{cmd}": FakeChoice(
                    sub, {sub: 1.0}, conf),
                "__continue__": FakeNoul(0.9),
            }
            FakeClient.last_node.append(node)
            return types.SimpleNamespace(answers=answers)
    FakeClient.last_node = []

    executed = []

    def scripted_exec(action, cwd):
        # resolve the argv the model *would* have planned on this call:
        # FakeClient answers carry no slots, so map node -> canned argv.
        node = FakeClient.last_node[-1]
        argv = {"ruff.check": ["ruff", "check"],
                "ruff.format": ["ruff", "format", "--check"]}[node]
        executed.append(argv)
        return (argv, 0, "ok", "")

    from hsom.config import Command, Subcommand
    cfg = EnvConfig(
        model="jev-latest", min_confidence=0.5, timeout=60.0,
        commands=(
            Command(name="ruff", description="lint", argv=None, subcommands=(
                Subcommand(name="check", description="lint",
                           argv=("ruff", "check")),
                Subcommand(name="format", description="fmt",
                           argv=("ruff", "format", "--check")),
            )),
        ))
    (tmp_path / "src").mkdir(exist_ok=True)
    steps, reason = dispatch_sequence(
        cfg, "lint then format", str(tmp_path), client=FakeClient(),
        execute_fn=scripted_exec, max_steps=2, repeat_guard=True)
    assert [tuple(s.argv) for s in steps] == [
        ("ruff", "check"), ("ruff", "format", "--check")]
    # the repeated step was re-planned before execution; only two commands ran
    assert executed == [["ruff", "check"], ["ruff", "format", "--check"]]
    assert reason == "max_steps reached"


def test_dispatch_sequence_declines_write_by_default(tmp_path):
    """P8: write/destructive steps are fail-closed without on_confirm."""
    import types

    cfg = sample_config(default_risk="write")

    class FakeClient:
        def system_one(self, **kw):
            return types.SimpleNamespace(answers={
                "__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)})

    executed = []
    steps, reason = dispatch_sequence(
        cfg, "run tests", str(tmp_path), client=FakeClient(),
        execute_fn=lambda a, c: executed.append(a) or (["pytest", "-q"], 0, "", ""),
        max_steps=1)
    assert steps == [] and reason == "declined by user"
    assert executed == []


def test_dispatch_sequence_on_confirm_allows_write(tmp_path):
    import types

    cfg = sample_config(default_risk="write")

    class FakeClient:
        def system_one(self, **kw):
            return types.SimpleNamespace(answers={
                "__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)})

    seen = []
    steps, reason = dispatch_sequence(
        cfg, "run tests", str(tmp_path), client=FakeClient(),
        execute_fn=lambda a, c: (["pytest", "-q"], 0, "", ""),
        max_steps=1, on_confirm=lambda action, argv: seen.append(
            (action.risk, list(argv))) or True)
    assert reason == "max_steps reached" and len(steps) == 1
    assert seen == [("write", ["pytest", "-q"])]


def test_dispatch_clips_history_and_asks_continue(config, tmp_path):
    seen = {}

    class Resp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw):
            seen["state"] = kw["state"]
            seen["questions"] = kw["questions"]
            return Resp()

    hist = [{"step": i} for i in range(1, 6)]
    dispatch(config, "run tests", str(tmp_path), client=FakeClient(),
             history=hist, max_steps=4, max_history=2, allow_continue=True)
    assert seen["state"]["history"] == hist[-2:]
    assert "__continue__" in seen["questions"]

    dispatch(config, "run tests", str(tmp_path), client=FakeClient(),
             max_steps=1)
    assert "history" not in seen["state"]
    assert "__continue__" not in seen["questions"]


def test_max_history_zero_keeps_step_aware_prompts(config, tmp_path):
    """Clipping all history entries must not drop step-awareness (P1)."""
    seen = {}

    class Resp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw):
            seen["state"] = kw["state"]
            seen["questions"] = kw["questions"]
            return Resp()

    hist = [{"step": 1, "node": "pytest", "describe": "pytest",
             "argv": ["pytest", "-q"]}]
    dispatch(config, "run tests", str(tmp_path), client=FakeClient(),
             history=hist, max_steps=3, max_history=0, step_index=1,
             allow_continue=True)
    assert "history" not in seen["state"]
    l1 = seen["questions"]["__command__"].instructions
    assert "step 2 of at most 3" in l1
    assert "NEXT step" in l1


def _cli_args(*argv):
    from hsom import cli
    return cli.build_parser().parse_args(list(argv))


def test_cli_run_sequence_stops_when_jev_declines(monkeypatch, config):
    from hsom import cli
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult

    calls = {"n": 0}
    answers = iter([True, False])
    plans = iter([
        PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                      risk="read"),
        PlannedAction(command="git", subcommand="status", confidence=0.9,
                      risk="read"),
    ])

    def fake_dispatch(cfg, request, cwd=".", **kw):
        return PlanOutcome(True, next(plans), "ok", 0.9), {}, {}, object()

    monkeypatch.setattr(cli, "dispatch", fake_dispatch)
    monkeypatch.setattr(cli, "continue_requested", lambda resp, threshold=None: next(answers))

    def fake_exec(cfg, action, cwd):
        calls["n"] += 1
        return ExecutionResult(argv=["pytest", "-q"], returncode=0,
                               stdout="", stderr="")

    monkeypatch.setattr(cli, "execute", fake_exec)
    args = _cli_args("run tests", "--max-steps", "5")
    rc = cli.run_sequence(config, args, 5)
    assert rc == cli.EXIT_OK and calls["n"] == 2


def _repeat_outcome(command, subcommand=None, confidence=0.9):
    return PlannedAction(command=command, subcommand=subcommand,
                         confidence=confidence, risk="read")


def test_cli_sequence_repeat_guard_skips_duplicate(monkeypatch, config):
    """P2 in the CLI: a repeated plan is re-planned, never executed twice."""
    from hsom import cli
    import hsom.dispatcher as disp
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult

    script = iter([
        PlanOutcome(True, _repeat_outcome("pytest"), "ok", 0.9),  # step 1
        PlanOutcome(True, _repeat_outcome("pytest"), "ok", 0.9),  # repeats
        PlanOutcome(True, _repeat_outcome("pytest"), "ok", 0.9),  # still repeats
    ])

    def fake_dispatch(cfg, request, cwd=".", **kw):
        return next(script), {}, {}, object()

    monkeypatch.setattr(cli, "dispatch", fake_dispatch)
    monkeypatch.setattr(disp, "dispatch", fake_dispatch)
    monkeypatch.setattr(cli, "continue_requested",
                        lambda resp, threshold=None: True)
    executed = []
    monkeypatch.setattr(
        cli, "execute",
        lambda cfg, a, cwd: executed.append(a) or ExecutionResult(
            argv=["pytest", "-q"], returncode=0, stdout="", stderr=""))

    rc = cli.run_sequence(config, _cli_args(
        "run tests", "--max-steps", "3"), 3)
    assert rc == cli.EXIT_ABSTAIN
    assert len(executed) == 1  # only step 1 actually ran


def test_cli_sequence_repeat_guard_redirects(monkeypatch, config):
    """P2 redirect: the retried (different) step runs exactly once."""
    from hsom import cli
    import hsom.dispatcher as disp
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult, resolve_argv

    script = iter([
        PlanOutcome(True, _repeat_outcome("pytest"), "ok", 0.9),  # step 1
        PlanOutcome(True, _repeat_outcome("pytest"), "ok", 0.9),  # repeats
        PlanOutcome(True, _repeat_outcome("git", "status"), "ok", 0.9),  # retry
    ])

    def fake_dispatch(cfg, request, cwd=".", **kw):
        return next(script), {}, {}, object()

    monkeypatch.setattr(cli, "dispatch", fake_dispatch)
    monkeypatch.setattr(disp, "dispatch", fake_dispatch)
    monkeypatch.setattr(cli, "continue_requested",
                        lambda resp, threshold=None: True)
    executed = []

    def fake_exec(cfg, action, cwd):
        argv = resolve_argv(cfg, action, cwd)
        executed.append(argv)
        return ExecutionResult(argv=argv, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli, "execute", fake_exec)
    rc = cli.run_sequence(config, _cli_args(
        "run tests", "--max-steps", "2"), 2)
    assert rc == cli.EXIT_OK
    assert executed == [["pytest", "-q"], ["git", "status"]]


def test_cli_midchain_abstention_exits_3(monkeypatch, config):
    from hsom import cli
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult

    outcomes = iter([
        PlanOutcome(True, _repeat_outcome("pytest"), "ok", 0.9),
        PlanOutcome(False, None,
                    "confidence 0.20 below minimum 0.50 (risk read)", 0.2),
    ])
    monkeypatch.setattr(
        cli, "dispatch", lambda *a, **k: (next(outcomes), {}, {}, object()))
    monkeypatch.setattr(cli, "continue_requested",
                        lambda resp, threshold=None: True)
    monkeypatch.setattr(
        cli, "execute",
        lambda cfg, a, cwd: ExecutionResult(
            argv=["pytest", "-q"], returncode=0, stdout="", stderr=""))

    rc = cli.run_sequence(config, _cli_args(
        "run tests", "--max-steps", "3"), 3)
    assert rc == cli.EXIT_ABSTAIN


def test_cli_max_steps_one_never_asks_continue(monkeypatch, config):
    from hsom import cli
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult

    def fake_dispatch(cfg, request, cwd=".", **kw):
        a = PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                          risk="read")
        return PlanOutcome(True, a, "ok", 0.9), {}, {}, object()

    def boom(resp):
        raise AssertionError("must not ask continue at max-steps=1")

    monkeypatch.setattr(cli, "dispatch", fake_dispatch)
    monkeypatch.setattr(cli, "continue_requested", boom)
    monkeypatch.setattr(cli, "execute",
                        lambda cfg, a, cwd: ExecutionResult(
                            argv=["pytest", "-q"], returncode=0,
                            stdout="", stderr=""))
    args = _cli_args("run tests", "--max-steps", "1")
    assert cli.run_sequence(config, args, 1) == cli.EXIT_OK


def test_dispatch_passes_temperature(config, tmp_path):
    seen = {}

    class Resp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99)}

    class FakeClient:
        def system_one(self, **kw):
            seen.clear()
            seen.update(kw)
            return Resp()

    dispatch(config, "run tests", str(tmp_path), client=FakeClient(),
             temperature=0.3)
    assert seen["extra_body"] == {"temperature": 0.3}

    dispatch(config, "run tests", str(tmp_path), client=FakeClient())
    assert seen["extra_body"] is None

    import dataclasses
    cfg = dataclasses.replace(config, temperature=0.15)
    dispatch(cfg, "run tests", str(tmp_path), client=FakeClient())
    assert seen["extra_body"] == {"temperature": 0.15}


def test_sequence_logs_plan_and_result(tmp_path):
    import json

    from hsom.runlog import JsonlLogger

    cfg = sample_config()

    class Resp:
        answers = {"__command__": FakeChoice("pytest", {"pytest": 1.0}, 0.99),
                   "__continue__": FakeNoul(0.9)}

    class FakeClient:
        def system_one(self, **kw): return Resp()

    def ok_exec(action, cwd):
        return (["pytest", "-q"], 0, "out", "")

    path = tmp_path / "run.jsonl"
    with JsonlLogger(str(path)) as log:
        steps, reason = dispatch_sequence(
            cfg, "run tests", ".", client=FakeClient(), execute_fn=ok_exec,
            max_steps=2, logger=log, repeat_guard=False)
    assert len(steps) == 2
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert [e["type"] for e in events] == ["plan", "result", "plan", "result"]
    assert events[0]["continue_asked"] is True
    assert events[0]["continue"] == 0.9
    assert events[2]["continue_asked"] is False
    assert events[1]["argv"] == ["pytest", "-q"]
    assert events[1]["returncode"] == 0 and events[1]["stdout"] == "out"


def test_cli_single_run_writes_jsonl_log(monkeypatch, tmp_path):
    import json

    from hsom import cli
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult

    env = tmp_path / "environment.toml"
    env.write_text('[meta]\nmodel = "jev-latest"\n' + """\
[[command]]
name = "pytest"
description = "tests"
argv = ["pytest", "-q"]
""")
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def fake_dispatch(cfg, request, cwd=".", **kw):
        a = PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                          risk="read")
        return PlanOutcome(True, a, "ok", 0.9), {}, {"cwd_files": [], "cwd_dirs": []}, object()

    monkeypatch.setattr(cli, "dispatch", fake_dispatch)
    monkeypatch.setattr(cli, "execute",
                        lambda cfg, a, cwd: ExecutionResult(
                            argv=["pytest", "-q"], returncode=0,
                            stdout="ok", stderr=""))
    logp = tmp_path / "run.jsonl"
    rc = cli.main(["--env", str(env), "--cwd", str(tmp_path),
                   "--log", str(logp), "run tests"])
    assert rc == cli.EXIT_OK
    events = [json.loads(line) for line in logp.read_text().splitlines()]
    assert [e["type"] for e in events] == ["plan", "result"]
    assert events[0]["command"] == "pytest" and events[0]["ok"] is True
    assert events[1]["argv"] == ["pytest", "-q"] and events[1]["returncode"] == 0


def test_cli_temperature_flag_passed(monkeypatch, tmp_path):
    from hsom import cli
    from hsom.dispatcher import PlanOutcome
    from hsom.executor import ExecutionResult

    env = tmp_path / "environment.toml"
    env.write_text('[meta]\nmodel = "jev-latest"\n' + """\
[[command]]
name = "pytest"
description = "tests"
argv = ["pytest", "-q"]
""")
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    seen = {}

    def fake_dispatch(cfg, request, cwd=".", **kw):
        seen["temperature"] = kw.get("temperature")
        a = PlannedAction(command="pytest", subcommand=None, confidence=0.9,
                          risk="read")
        return PlanOutcome(True, a, "ok", 0.9), {}, {}, object()

    monkeypatch.setattr(cli, "dispatch", fake_dispatch)
    monkeypatch.setattr(cli, "execute",
                        lambda cfg, a, cwd: ExecutionResult(
                            argv=["pytest", "-q"], returncode=0,
                            stdout="", stderr=""))
    rc = cli.main(["--env", str(env), "--cwd", str(tmp_path),
                   "--temperature", "0.4", "run tests"])
    assert rc == cli.EXIT_OK and seen["temperature"] == 0.4


def _write_env(tmp_path):
    env = tmp_path / "environment.toml"
    env.write_text('[meta]\nmodel = "jev-latest"\n' + """\
[[command]]
name = "pytest"
description = "tests"
argv = ["pytest", "-q"]
""")
    return str(env)


def test_cli_surfaces_jev_error_as_distinct_exit(monkeypatch, tmp_path):
    import httpx2
    from typesafe_sdk import TypeSafeInternalServerError

    from hsom import cli

    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def boom_dispatch(cfg, request, cwd=".", **kw):
        raise TypeSafeInternalServerError(500, "kaboom", httpx2.Headers())

    monkeypatch.setattr(cli, "dispatch", boom_dispatch)
    rc = cli.main(["--env", _write_env(tmp_path), "--cwd", str(tmp_path),
                   "run tests"])
    assert rc == cli.EXIT_JEV_ERROR


def test_cli_sequence_surfaces_jev_error_as_distinct_exit(monkeypatch, tmp_path, capsys):
    from typesafe_sdk import TypeSafeAPIConnectionError

    from hsom import cli
    from hsom.config import load_config

    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    cfg = load_config(_write_env(tmp_path))
    args = cli.build_parser().parse_args(
        ["--max-steps", "2", "--cwd", str(tmp_path), "run tests"])

    def boom_dispatch(config, request, cwd=".", **kw):
        raise TypeSafeAPIConnectionError("no route")

    monkeypatch.setattr(cli, "dispatch", boom_dispatch)
    rc = cli.run_sequence(cfg, args, 2)
    assert rc == cli.EXIT_JEV_ERROR
    err = capsys.readouterr().err
    assert "TypeSafeAPIConnectionError" in err
