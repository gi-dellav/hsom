"""Opt-in JSONL run logging: writer + event builders."""

import json
import os
import stat

import pytest

from hsom.dispatcher import PlanOutcome, PlannedAction
from hsom.eval import EvalCase, EvalTestResult
from hsom.runlog import JsonlLogger, eval_event, plan_event, result_event, run_event


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_jsonl_logger_creates_private_file(tmp_path):
    path = tmp_path / "run.jsonl"
    with JsonlLogger(str(path)) as log:
        log.log({"a": 1})
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_jsonl_logger_tightens_existing_file(tmp_path):
    path = tmp_path / "run.jsonl"
    path.write_text("")
    path.chmod(0o644)
    with JsonlLogger(str(path)) as log:
        log.log({"a": 1})
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_jsonl_logger_appends_across_instances(tmp_path):
    path = tmp_path / "run.jsonl"
    with JsonlLogger(str(path)) as log:
        log.log({"a": 1})
    with JsonlLogger(str(path)) as log:
        log.log({"b": 2})
    lines = [json.loads(x) for x in path.read_text().splitlines()]
    assert lines == [{"a": 1}, {"b": 2}]


def test_plan_event_fields():
    action = PlannedAction(command="git", subcommand="status", confidence=0.9,
                           risk="read", threshold=0.5, threshold_source="global")
    out = PlanOutcome(True, action, "ok", 0.9)
    ev = plan_event(1, "req", ".", out,
                    {"cwd_files": ["a"], "cwd_dirs": ["d"]},
                    continue_asked=True, continue_value=0.8,
                    continue_threshold=0.4,
                    continue_threshold_source="meta continue_threshold",
                    max_steps=3, max_history=2, history_len=0,
                    temperature=0.0)
    assert ev["type"] == "plan"
    assert ev["command"] == "git" and ev["subcommand"] == "status"
    assert ev["continue_asked"] is True and ev["continue"] == 0.8
    assert ev["temperature"] == 0.0
    assert ev["continue_threshold"] == 0.4
    assert ev["continue_threshold_source"] == "meta continue_threshold"
    assert ev["cwd_files"] == ["a"] and ev["cwd_dirs"] == ["d"]
    assert ev["max_steps"] == 3 and ev["max_history"] == 2
    assert ev["layers"] == []
    assert ev["repeat_retry"] is False


def test_result_event_fields():
    ev = result_event(2, ["ls"], returncode=0, stdout="x", stderr="")
    assert ev["type"] == "result" and ev["step"] == 2
    assert ev["argv"] == ["ls"] and ev["returncode"] == 0
    assert ev["dry_run"] is False and ev["declined"] is False
    assert ev["error_kind"] is None

    ev = result_event(3, error="timed out", error_kind="timeout")
    assert ev["error_kind"] == "timeout"


def test_eval_event_fields():
    case = EvalCase(name="t", input="run", expected=(("git", "status"),),
                    expected_str=("git status",))
    result = EvalTestResult(case, True, (("git", "status"),), "ok",
                            confidence=0.9, risk="read")
    ev = eval_event(case, result, temperature=0.0)
    assert ev["type"] == "eval" and ev["name"] == "t"
    assert ev["expected"] == "git status" and ev["actual"] == "git status"
    assert ev["passed"] is True and ev["steps"] == 1
    assert ev["error_kind"] is None
    assert ev["temperature"] == 0.0
    assert ev["system"] == "jev" and ev["run_index"] == 1
    assert ev["excluded"] is False and ev["wrong_plan"] is False


def test_eval_event_metadata_and_exclusion():
    case = EvalCase(name="t", input="run", expected=(("git", "status"),),
                    expected_str=("git status",),
                    exclude_reason="probe", wrong_plan=True)
    result = EvalTestResult(case, True, (("git", "status"),), "ok",
                            model="jev-1.13.0", input_tokens=7,
                            output_tokens=3, latency_ms=12.5)
    ev = eval_event(case, result, suite="s", run_index=3, repeats=5,
                    system="jev", temperature=0.0)
    assert ev["suite"] == "s" and ev["run_index"] == 3 and ev["repeats"] == 5
    assert ev["model"] == "jev-1.13.0"
    assert ev["input_tokens"] == 7 and ev["output_tokens"] == 3
    assert ev["latency_ms"] == 12.5
    assert ev["excluded"] is True and ev["wrong_plan"] is True
    assert ev["exclude_reason"] == "probe"


def test_run_event_fields():
    ev = run_event(suite="s", label="heldout", model="jev-1.13.0",
                   repeats=5, frozen=True, frozen_ref="v1")
    assert ev["type"] == "run" and ev["suite"] == "s"
    assert ev["label"] == "heldout" and ev["repeats"] == 5
    assert ev["frozen"] is True and ev["frozen_ref"] == "v1"
