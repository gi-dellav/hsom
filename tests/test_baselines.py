"""Baseline planners: structured enum output and logprob scoring."""

import json
from types import SimpleNamespace

import pytest

import hsom.baselines as baselines
from hsom.baselines import BaselineError, LogprobPlanner, StructuredPlanner
from hsom.executor import resolve_argv


def _response(content: str = "", *, tokens=None, model="fake-model"):
    usage = SimpleNamespace(prompt_tokens=11, completion_tokens=3)
    message = SimpleNamespace(content=content, parsed=None)
    logprobs = None
    if tokens is not None:
        top = [SimpleNamespace(token=tok, logprob=lp) for tok, lp in tokens]
        logprobs = SimpleNamespace(content=[SimpleNamespace(top_logprobs=top)])
    choice = SimpleNamespace(message=message, logprobs=logprobs)
    return SimpleNamespace(choices=[choice], usage=usage, model=model)


class FakeLitellm:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def completion(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("unexpected extra LiteLLM call")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def fake_completion(monkeypatch):
    def install(responses):
        fake = FakeLitellm(responses)
        monkeypatch.setattr(baselines, "_litellm", lambda: fake)
        return fake
    return install


def test_structured_plans_command_and_subcommand(config, workdir, fake_completion):
    fake = fake_completion([
        _response(json.dumps({"choice": "git"})),
        _response(json.dumps({"choice": "status"})),
    ])
    outcome, usage = StructuredPlanner(
        "openrouter/test-model", api_key="x").plan(config, "show status", workdir)
    assert outcome.ok and outcome.action is not None
    assert resolve_argv(config, outcome.action, workdir) == ["git", "status"]
    assert usage.calls == 2
    assert usage.input_tokens == 22 and usage.output_tokens == 6
    assert usage.model == "fake-model"
    # Both calls constrain the answer with an enum.
    for call in fake.calls:
        schema = call["response_format"]["json_schema"]["schema"]
        assert "enum" in schema["properties"]["choice"]


def test_structured_abstains_on_none(config, workdir, fake_completion):
    fake_completion([_response(json.dumps({"choice": baselines.NONE_LABEL}))])
    outcome, _usage = StructuredPlanner(
        "openrouter/test-model", api_key="x").plan(config, "do something", workdir)
    assert not outcome.ok and outcome.action is None


def test_structured_rejects_invalid_enum(config, workdir, fake_completion):
    fake_completion([_response(json.dumps({"choice": "not-a-command"}))])
    with pytest.raises(BaselineError):
        StructuredPlanner("openrouter/test-model", api_key="x").plan(
            config, "show status", workdir)


def test_logprob_picks_highest_score(config, workdir, fake_completion):
    fake_completion([
        _response("0", tokens=[("0", -0.1), ("1", -1.0)]),
        _response("0", tokens=[("0", -0.2), ("1", -0.8)]),
    ])
    outcome, usage = LogprobPlanner(
        "openrouter/test-model", api_key="x").plan(config, "show status", workdir)
    assert outcome.ok and outcome.action is not None
    assert resolve_argv(config, outcome.action, workdir) == ["git", "status"]
    assert usage.calls == 2


def test_logprob_ties_go_to_tree_order(config, workdir, fake_completion):
    fake_completion([
        _response("1", tokens=[("1", -0.5), ("0", -0.5)]),
        _response("1", tokens=[("1", -0.5), ("0", -0.5)]),
    ])
    outcome, _usage = LogprobPlanner(
        "openrouter/test-model", api_key="x").plan(config, "show status", workdir)
    assert outcome.ok and outcome.action is not None
    assert outcome.action.command == "git"
    assert outcome.action.subcommand == "status"


def test_logprob_accepts_dict_entries(config, workdir, fake_completion):
    response = _response("0", tokens=[("0", -0.1)])
    response.choices[0].logprobs.content[0].top_logprobs = [
        {"token": "0", "logprob": -0.1},
        {"token": "1", "logprob": -2.0},
    ]
    fake_completion([
        response,
        _response("0", tokens=[("0", -0.1), ("1", -2.0)]),
    ])
    outcome, _usage = LogprobPlanner(
        "openrouter/test-model", api_key="x").plan(config, "show status", workdir)
    assert outcome.ok and outcome.action is not None
    assert outcome.action.command == "git"


def test_logprob_falls_back_to_greedy_when_provider_omits_logprobs(
        config, workdir, fake_completion):
    fake_completion([
        _response("0"),
        _response("0"),
    ])
    outcome, usage = LogprobPlanner(
        "openrouter/test-model", api_key="x").plan(config, "show status", workdir)
    assert outcome.ok and outcome.action is not None
    assert outcome.action.command == "git"
    assert usage.fallbacks == 2


def test_logprob_falls_back_when_provider_rejects_logprobs(
        config, workdir, fake_completion):
    fake_completion([
        RuntimeError(
            "No endpoints found that can handle the requested parameters"),
        _response("0"),
        _response("0"),
    ])
    outcome, usage = LogprobPlanner(
        "openrouter/test-model", api_key="x").plan(config, "show status", workdir)
    assert outcome.ok and outcome.action is not None
    assert outcome.action.command == "git"
    assert usage.fallbacks == 2
    # The failed logprob call is not counted as a completion call.
    assert usage.calls == 2


def test_logprob_tournament_for_large_option_sets(workdir):
    planner = LogprobPlanner("openrouter/test-model", max_options=2)
    seen = []

    def choose(instructions, options, usage):
        seen.append(list(options))
        return options[0]

    planner._choose_chunk = choose  # type: ignore[method-assign]
    picked = planner._choose("pick", ["a", "b", "c", "d", "e"], baselines.Usage())
    assert picked == "a"  # chunk winners are a, c, e; tournament picks a
    assert seen[0] == ["a", "b"]
    assert seen[1] == ["c", "d"]
    assert seen[2] == ["e"]
