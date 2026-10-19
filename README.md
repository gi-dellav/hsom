# hsom

*Harness for System One Models. Runs allowlisted shell commands using decision trees.*

*hsom* is a strict-allowlist harness. `environment.toml` defines which shell commands Jev (the TypeSafe System One classifier) may select. In one step, Jev picks: command → subcommand → flags (boolean or valued) → path slots; this works by navigating the decision tree as defined by the TOML file.

- `read` actions run directly.
- `write` and `destructive` actions ask for confirmation (`y/N`, default N; non-tty declines).
- `--dry-run` previews without executing or prompting.

*hsom* is usable both as a CLI tool for shell-based harnesses and as a Python library for building custom harnesses.

**PyPI:** https://pypi.org/project/hsom/1.0.0/

(*note*: I'm currently working on a research paper on the inner workings and theoritical aspects of the algorithm implemented by *hsom*.)

## Benchmark

Strict pass rate (all repeats passed) on the bundled suites; structured and
logprob baselines use `openai/gpt-6-luna`.

| Suite | Label | Jev | Structured | Logprobs |
| --- | --- | --- | --- | --- |
| git-workflow | regression | 95.3% | 58.7% | 66.7% |
| python-qa | regression | 96.2% | 43.1% | 45.1% |
| container-ops | heldout | **92.0%** | 62.0% | 68.0% |

Cost and speed per test case:

| Suite | System | Cost/test (USD) | p50 ms | p95 ms |
| --- | --- | --- | --- | --- |
| git-workflow | Jev | 0.0001 | 333.8 | 511.3 |
| git-workflow | Structured | 0.00007 | 4195.2 | 10514.8 |
| git-workflow | Logprobs | 0.00005 | 2789.9 | 4428.0 |
| python-qa | Jev | 0.0001 | 364.2 | 574.4 |
| python-qa | Structured | 0.00006 | 3075.7 | 4431.7 |
| python-qa | Logprobs | 0.00004 | 2709.0 | 3910.6 |
| container-ops | Jev | 0.0001 | 364.5 | 448.9 |
| container-ops | Structured | 0.00015 | 3044.9 | 5010.2 |
| container-ops | Logprobs | 0.00011 | 2470.2 | 5546.2 |

## Setup

```bash
pip install -e .
export TYPESAFE_API_KEY=...   # from https://console.typesafe.ai/keys
cp environment.toml.example environment.toml
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv venv                          # creates .venv
source .venv/bin/activate
uv pip install -e .
export TYPESAFE_API_KEY=...      # from https://console.typesafe.ai/keys
cp environment.toml.example environment.toml
```

### OpenRouter

hsom can call Jev through [OpenRouter's System One API](https://openrouter.ai/docs/guides/community/typesafe-sdk) (billed to your OpenRouter account) instead of TypeSafe Cloud. Pick one provider:

```toml
# environment.toml
[meta]
provider = "openrouter"   # default base_url: https://openrouter.ai/api
```

```bash
export OPENROUTER_API_KEY=...   # from https://openrouter.ai/settings/keys
```

Endpoint precedence (highest first): `--base-url` > `[meta] base_url` > `TYPESAFE_BASE_URL` > provider default.

Key precedence: `TYPESAFE_API_KEY` > `OPENROUTER_API_KEY`. The SDK itself reads only `TYPESAFE_API_KEY`, so hsom forwards `OPENROUTER_API_KEY` explicitly.

- `TYPESAFE_BASE_URL=https://openrouter.ai/api` also works and keeps `provider = "typesafe"`.
- Bare model IDs (`jev-latest`) and prefixed IDs (`typesafe/jev-1.13`) are both passed through.
- Model listing via the SDK is not supported by OpenRouter. Browse https://openrouter.ai/typesafe instead.

## Configuration

`environment.toml` holds one `[meta]` section and one `[[command]]` table per allowed command.

### `[meta]` settings

```toml
[meta]
model = "jev-latest"
min_confidence = 0.5
timeout = 60
default_risk = "read"     # read | write | destructive
max_steps = 1             # 1..10 upper bound; >1 lets Jev decide to continue
max_history = 5           # optional; cap history entries sent back to Jev
continue_threshold = 0.5  # optional; Noul bar for the __continue__ chaining gate
continue_question = "..." # optional; override the __continue__ gate instructions
temperature = 0.0         # optional; extra_body passthrough (provider-dependent)
command_question = "What shell task is the user asking for?"

  [meta.risk_thresholds]
  read = 0.5
  write = 0.7
  destructive = 0.9
```

`temperature` is forwarded through the SDK's `extra_body`. The OpenRouter
System One schema does not document a temperature parameter, so treat it as
provider-dependent and not as a determinism guarantee. The benchmark configs
set it explicitly to `0.0`, and run logs record the value used
(`temperature` in `plan`/`eval` events).

### Commands, subcommands, flags, and paths

```toml
[[command]]
name = "git"
description = "version control operations"
risk = "read"
instructions_subcommand = "Which git subcommand does the request need?"

  [[command.subcommand]]
  name = "log"
  description = "show commit history"
  argv = ["git", "log"]

    [[command.subcommand.flag]]          # boolean flag
    name = "--oneline"
    description = "compact one-line-per-commit history"
    argv_fragment = ["--oneline"]
    question = "Does the user want compact one-line history?"  # optional

    [[command.subcommand.flag]]          # valued flag
    name = "--format"
    description = "history output format"
    argv_fragment = ["--format={value}"]
    values = ["json", "plain"]
    [command.subcommand.flag.value_descriptions]
    json = "one JSON object per commit"

  [[command.subcommand]]
  name = "add"
  description = "stage a file for commit"
  argv = ["git", "add", "{path:src}"]   # named slot; legacy "{path}" also works
  risk = "write"                        # prompts for confirmation

    [[command.subcommand.path]]
    name = "src"
    kind = "files"          # files | dirs | both
    optional = false
    description = "file to stage"
    base = "."              # relative root inside --cwd
    depth = 3               # 1 = top level only
    glob = "*.py"           # optional fnmatch
    include_dotfiles = false
    max_results = 200
    question = "Which Python file does the request want to stage?"
```

`stated_question` is an optional yes/no gate for **optional** slots: when
Jev says the request names no specific path, the slot is omitted. A
missing, malformed, or non-Noul gate answer is fail-closed and also omits
the slot. It has no effect on required slots.

## Usage

Run `hsom` with a natural-language request:

```bash
hsom "show git status" --dry-run --show-probs
hsom "brief git history"              # -> git log --oneline
hsom "stage main.py"                  # -> git add main.py (asks [y/N], risk write)
hsom "copy readme into examples"      # -> cp README.md examples
hsom "run tests" --max-steps 3        # dynamic chaining: Jev decides each step
hsom "run tests" --max-steps 1        # single shot (never asks to continue)
hsom "run tests" --max-history 2      # send back at most 2 prior steps
hsom "run tests" --continue-threshold 0.3  # lower the __continue__ chaining bar (CLI wins)
hsom "run tests" --temperature 0.2    # sampling temperature (extra_body)
hsom "run tests" --log run.jsonl      # opt-in structured JSONL run log
hsom "run tests" --min-confidence 0.8 # CLI flag wins over all config
hsom "run tests" --provider openrouter --dry-run  # one-shot OpenRouter routing
hsom --eval eval.toml.example         # eval harness: plans only, never runs
```

## Python library

`hsom` is also an importable library built around the `Harness` class
(sync-only). The CLI shares the same dispatcher/executor machinery.

```bash
pip install -e .
```

```python
from hsom import Harness

# Config: environment.toml path, EnvConfig, or TOML-shaped dict.
h = Harness(env="environment.toml")
h = Harness(env={"meta": {"model": "jev-latest"},
                 "command": [{"name": "pytest", "description": "run tests",
                               "argv": ["pytest", "-q"]}]})

# Single-shot plan (max_steps=1) -> PlanOutcome(ok, action, reason, ...).
outcome = h.plan("brief git history")
if outcome.ok:
    print(h.resolve(outcome.action))   # argv from the toml template only

# Chained run -> RunResult(steps, stop_reason, ok, declined).
result = h.run("run tests", max_steps=3, dry_run=True)
print(result.stop_reason, [s.argv for s in result.steps])

# Write/destructive steps never prompt on stdin here. Pass on_confirm
# (default None = fail-closed auto-decline, like the CLI off-tty):
result = h.run("stage main.py", on_confirm=lambda action, argv: True)

# Dynamic working directory: subclass, pass get_cwd=..., assign
# h.get_cwd = lambda: ..., or h.set_cwd_fn(...) / h.set_cwd(...).
# A per-call cwd=... always wins over get_cwd().
h.set_cwd_fn(lambda: "/path/to/project")
result = h.run("run tests", cwd="/override", dry_run=True)

# Eval harness (plans only, never executes) -> EvalSummary.
summary = h.eval("eval.toml.example")
print(f"{summary.passed}/{summary.total} passed")
```
