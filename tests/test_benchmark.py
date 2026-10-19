"""Benchmark orchestration: leakage, freeze manifests, stats, reporting."""

import json
from pathlib import Path

import pytest

import hsom.benchmark as bench
from hsom.eval import EvalCase, EvalSummary, EvalTestResult

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def _suite(tmp_path, *, name="suite", with_excluded=False):
    suite_dir = tmp_path / name
    suite_dir.mkdir()
    (suite_dir / "workspace").mkdir()
    (suite_dir / "workspace" / "a.txt").write_text("a")
    env = suite_dir / "environment.toml"
    env.write_text('[meta]\nmodel = "jev-1.13.0"\n[[command]]\n'
                   'name = "git"\ndescription = "version control"\n'
                   'argv = ["git", "status"]\n')
    ev = suite_dir / "eval.toml"
    ev.write_text('[[test]]\nname = "t"\ninput = "show status"\n'
                  'expected = "git status"\n')
    excluded = None
    if with_excluded:
        excluded = suite_dir / "excluded.toml"
        excluded.write_text('[[test]]\nname = "x"\ninput = "unsupported thing"\n'
                            'expect_abstain = true\nexclude_reason = "test probe"\n'
                            'wrong_plan = true\n')
    return bench.Suite(
        name=name, label="heldout", env=env, eval=ev,
        cwd=suite_dir / "workspace", excluded=excluded,
        manifest=suite_dir / "manifest.json")


def _result(case, passed, *, actual=None, reason="ok", model="jev-1.13.0",
            latency=10.0, error_kind=None):
    return EvalTestResult(case, passed, actual, reason,
                          confidence=0.9, risk="read", error_kind=error_kind,
                          model=model, input_tokens=5, output_tokens=2,
                          latency_ms=latency)


def _case(name, *, input="show status", expected="git status", excluded=False,
          wrong_plan=False):
    return EvalCase(
        name=name, input=input,
        expected=(tuple(expected.split()),) if expected else None,
        expected_str=(expected,) if expected else None,
        exclude_reason="probe" if excluded else None,
        wrong_plan=wrong_plan)


def test_repo_examples_have_no_leakage_and_valid_manifests():
    config = bench.load_benchmark_config()
    hits, errors = bench.check_all(config)
    assert hits == []
    assert errors == []


def test_leakage_checker_detects_verbatim_input(tmp_path):
    suite = _suite(tmp_path)
    suite.env.write_text(
        '[meta]\nmodel = "jev-1.13.0"\n[[command]]\n'
        'name = "git"\ndescription = "show status commands"\n'
        'argv = ["git", "status"]\n')
    hits = bench.check_suite_leakage(suite)
    assert len(hits) == 1
    assert hits[0].case == "t" and "description" in hits[0].field


def test_freeze_and_verify_manifest(tmp_path, monkeypatch):
    suite = _suite(tmp_path)
    monkeypatch.setattr(bench, "EXAMPLES_DIR", tmp_path)
    path = bench.freeze_suite(suite, "v1")
    assert path.exists()
    assert bench.verify_manifest(suite) == []
    suite.env.write_text(suite.env.read_text() + "\n# changed\n")
    errors = bench.verify_manifest(suite)
    assert errors and "changed" in errors[0]


def test_aggregate_exclusions_and_patterns(tmp_path):
    suite = _suite(tmp_path)
    c1 = _case("a")
    c2 = _case("b")
    cx = _case("x", expected=None, excluded=True, wrong_plan=True)
    records = [
        bench.CaseRecord("unused", "jev", 1, 2, _result(c1, True, actual=(("git", "status"),))),
        bench.CaseRecord("unused", "jev", 2, 2, _result(c1, True, actual=(("git", "status"),))),
        bench.CaseRecord("unused", "jev", 1, 2, _result(c2, True, actual=(("git", "status"),))),
        bench.CaseRecord("unused", "jev", 2, 2, _result(c2, False, reason="miss")),
        bench.CaseRecord("unused", "jev", 1, 2, _result(cx, False, reason="wrong"), True),
        bench.CaseRecord("unused", "jev", 2, 2, _result(cx, False, reason="wrong"), True),
    ]
    agg = bench.aggregate(suite, "jev", records, 2)
    assert agg.strict_counts(agg.headline_cases()) == (1, 2)
    assert agg.strict_counts(agg.all_cases()) == (1, 3)
    assert agg.per_run_rates() == [1.0, 0.5]
    by_name = {c.name: c for c in agg.cases}
    assert by_name["a"].pattern == "11"
    assert by_name["b"].pattern == "10"


def test_render_report_contains_headline_and_exclusions(tmp_path):
    suite = _suite(tmp_path)
    config = bench.BenchmarkConfig(suites=(suite,), repeats=2)
    case = _case("a", excluded=False)
    ex = _case("x", expected=None, excluded=True, wrong_plan=True)
    records = [
        bench.CaseRecord(suite.name, "jev", 1, 2,
                         _result(case, True, actual=(("git", "status"),))),
        bench.CaseRecord(suite.name, "jev", 2, 2,
                         _result(case, True, actual=(("git", "status"),))),
        bench.CaseRecord(suite.name, "jev", 1, 2,
                         _result(ex, False, reason="planned wrong"), True),
        bench.CaseRecord(suite.name, "jev", 2, 2,
                         _result(ex, False, reason="planned wrong"), True),
    ]
    agg = bench.aggregate(suite, "jev", records, 2)
    out = tmp_path / "report"
    text = bench.render_report(config, [agg], None, output_dir=out)
    assert "Aggregate accuracy" in text
    assert "With and without exclusions" in text
    assert "test probe" not in text  # no excluded.toml in this synthetic suite
    assert (out / "report.md").exists()
    data = json.loads((out / "report.json").read_text())
    assert data["alpha"] == 0.05


def test_pricing_cost():
    pricing = bench.Pricing(
        as_of="2026-10-18", currency="USD",
        per_mtok={"openrouter/test-model": (0.10, 0.20)})
    assert pricing.cost("test-model", 1_000_000, 1_000_000) == pytest.approx(0.30)
    assert pricing.cost("openrouter/test-model", 1_000, 0) == pytest.approx(0.0001)
    assert pricing.cost("unknown", 1, 1) is None


def test_run_jev_suite_repeats_and_logs(tmp_path, monkeypatch, config):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    suite = _suite(tmp_path)
    case = _case("a")
    summary = EvalSummary(total=1, passed=1, failed=0, results=(
        _result(case, True, actual=(("git", "status"),)),))
    monkeypatch.setattr(bench, "load_config", lambda path: config)
    monkeypatch.setattr(bench, "load_eval", lambda path: [case])
    monkeypatch.setattr(bench, "run_eval", lambda *a, **k: summary)
    log = tmp_path / "run.jsonl"
    with bench.JsonlLogger(str(log)) as logger:
        records = bench.run_jev_suite(
            suite, bench.BenchmarkConfig(suites=(suite,)), repeats=2,
            include_excluded=False, logger=logger)
    assert len(records) == 2
    events = [json.loads(line) for line in log.read_text().splitlines()]
    assert events[0]["type"] == "run"
    assert all(e["type"] == "eval" and e["system"] == "jev" for e in events[1:])
    assert [e["run_index"] for e in events[1:]] == [1, 2]


def test_records_from_logs_roundtrip(tmp_path):
    suite = _suite(tmp_path)
    case = _case("a")
    result = _result(case, True, actual=(("git", "status"),))
    from hsom.runlog import JsonlLogger, eval_event, run_event
    log = tmp_path / "suite.jev.jsonl"
    with JsonlLogger(str(log)) as logger:
        logger.log(run_event(suite=suite.name, model="jev-1.13",
                             repeats=1))
        logger.log(eval_event(case, result, suite=suite.name,
                              run_index=1, repeats=1, system="jev"))
    grouped = bench.records_from_logs([log])
    records = grouped[(suite.name, "jev", 1)]
    assert len(records) == 1 and records[0].result.passed
    config = bench.BenchmarkConfig(suites=(suite,))
    aggregates = bench.build_aggregates_from_logs(config, [log])
    assert len(aggregates) == 1
    assert aggregates[0].strict_counts(aggregates[0].headline_cases()) == (1, 1)


def test_cli_check_passes_on_repo():
    assert bench.main(["check"]) == 0
