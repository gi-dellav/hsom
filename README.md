# hsom

*Harness for System One Models. Allows Jev to operate on a bash shell using decision trees.*

hsom is a strict-allowlist harness. `environment.toml` defines which bash commands Jev (the TypeSafe System One classifier) may select. In one step, Jev picks: command → subcommand → flags (boolean or valued) → path slots; this works by navigating the decision tree as defined by the TOML file.

- `read` actions run directly.
- `write` and `destructive` actions ask for confirmation (`y/N`, default N; non-tty declines).
- `--dry-run` previews without executing or prompting.

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
temperature = 0.0         # optional; sampling temperature (extra_body)
command_question = "What shell task is the user asking for?"

  [meta.risk_thresholds]
  read = 0.5
  write = 0.7
  destructive = 0.9
```

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
    stated_question = "Does the request name a specific Python file?"
```

### Multi-path and legacy v1 style

Multi-path example: `argv = ["cp", "{path:src}", "{path:dst}"]` with two `[[command.path]]` tables (max 3 slots, one placeholder per token).

Legacy v1 style (`takes_path` / `path_kind` / `path_optional` plus bare `{path}`) still loads. It desugars to a single slot named `path`. Do not mix both styles.

## Usage

Run `hsom` with a natural-language request:

```bash
hsom "show git status" --dry-run --show-probs
hsom "brief git history"              # -> git log --oneline
hsom "stage readme"                   # -> git add ... (asks [y/N], risk write)
hsom "copy readme into docs"          # -> cp README.md docs
hsom "run tests" --max-steps 3        # dynamic chaining: Jev decides each step
hsom "run tests" --max-steps 1        # single shot (never asks to continue)
hsom "run tests" --max-history 2      # send back at most 2 prior steps
hsom "run tests" --continue-threshold 0.3  # lower the __continue__ chaining bar (CLI wins)
hsom "run tests" --temperature 0.2    # sampling temperature (extra_body)
hsom "run tests" --log run.jsonl      # opt-in structured JSONL run log
hsom "run tests" --min-confidence 0.8 # CLI flag wins over all config
hsom "run tests" --provider openrouter --dry-run  # one-shot OpenRouter routing
hsom --eval eval.toml                 # eval harness: plans only, never runs
```

## Python library

`hsom` is also an importable library built around the `Harness` class
(sync-only). The CLI uses the same machinery.

```bash
pip install hsom
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
result = h.run("stage readme", on_confirm=lambda action, argv: True)

# Dynamic working directory: subclass, pass get_cwd=..., assign
# h.get_cwd = lambda: ..., or h.set_cwd_fn(...) / h.set_cwd(...).
# A per-call cwd=... always wins over get_cwd().
h.set_cwd_fn(lambda: "/path/to/project")
result = h.run("run tests", cwd="/override", dry_run=True)

# Eval harness (plans only, never executes) -> EvalSummary.
summary = h.eval("eval.toml")
print(f"{summary.passed}/{summary.total} passed")
```

Lower-level pieces are re-exported too (`plan_full`, `execute`,
`load_config`, `load_eval`, `PlannedAction`, `EnvConfig`, ...). See
`examples/library_usage.py` for a runnable version (`dry_run=True`
except the live `plan` demo, which needs `TYPESAFE_API_KEY` or
`OPENROUTER_API_KEY` + `provider="openrouter"`).

### Abstention and confidence

`none_of_the_above` semantics, by layer:

- L1 (command): abstain.
- L2 (subcommand): run base `argv` as-made; abstain if none.
- Valued-flag/path layer: omit if optional; abstain if required.

Confidence = the least-certain Choice layer.

Threshold resolution (highest first): CLI `--min-confidence` > per-node > per-risk tier > global. The reason names the winner, e.g. `below minimum 0.70 (risk write)`.

### Chaining

`--max-steps N` / `meta.max_steps` set the step budget. N is the upper bound, not a fixed count (`--steps` is a legacy alias).

- While budget remains, each Jev call also answers a `__continue__` Noul gate. After a step succeeds, the loop stops as soon as Jev declines. A missing gate is treated as "stop".
- The gate bar resolves CLI `--continue-threshold` > `[meta] continue_threshold` > 0.5 default, and is logged per step (`continue_threshold[_source]` in `plan` events). Per-eval-test `continue_threshold` overrides it for that test.
- On step 2+, the L1 and `__continue__` instructions are step-aware: they name the step number, the completed steps (`node` + argv), and the remaining budget, so Jev plans the *next* part instead of repeating. History entries also carry `node`/`describe` alongside `argv`.
- If a step resolves to the previous step's argv verbatim, the harness re-plans once with an anti-repeat nudge instead of executing a duplicate; a second repeat stops honestly (`repeat_guard=False` disables this for canned unit probes; eval pins it off).
- With `--max-steps 1`, the gate is never asked and the run is single-shot.
- After each step, the CWD is rescanned and `{step, node, describe, argv, returncode, stdout_tail}` is appended to the Jev state history (`state["step"]`/`state["max_steps"]` ride along too). `--max-history N` / `meta.max_history` keeps only the N most recent entries (0 sends none; unset sends all, still bounded by the step budget).
- The run stops on abstention, non-zero exit (unless `--no-stop-on-error`), decline, Jev's stop decision, a repeated step, or budget exhaustion.

`dispatch_sequence()` in `dispatcher.py` exposes this programmatically.

## Eval mode

`hsom --eval eval.toml` runs each `[[test]]` input through Jev and compares the planned argv to `expected`. Nothing executes and nothing prompts:

```toml
[[test]]
name = "brief history"            # optional (default test-N), must be unique
input = "brief git history"       # given to Jev
expected = "git log --oneline"    # shell-parsed, compared as argv list

[[test]]
name = "stage then status"        # multi-step: expected is an array
input = "stage readme then show status"
expected = ["git add README.md", "git status"]   # max_steps = len(expected)

[[test]]
name = "nonsense abstains"
input = "launch the rockets"
expect_abstain = true             # pass iff Jev abstains (no expected)
```

Per-test overrides exist for `cwd` (relative, joined onto `--cwd`), `min_confidence`, and `continue_threshold`. `[meta]` provides defaults for all three.

- A string `expected` runs single-shot (`max_steps = 1`, no `__continue__` gate).
- An array runs `max_steps = len(expected)`. Every planned step's argv must match the matching entry, so Jev must not stop early.

Exit 0 when all tests pass, 5 otherwise. See `eval.toml.example`.

## Run logging

`--log PATH` (opt-in) appends one JSON object per line.

- Interactive runs emit a `plan` event (state summary, node, flags, paths, confidence, risk, threshold/threshold_source, per-layer decisions, continue gate) followed by a `result` event (resolved argv, dry-run/declined/error, returncode, stdout, stderr) for each step.
- Eval mode emits one `eval` event per `[[test]]`.

Nothing is written without `--log`. The file opens in append mode.

## Layout

- `src/hsom/config.py` – toml loading + validation, risk/threshold resolution
- `src/hsom/client.py` – provider/base_url/API-key resolution, `TypeSafeClient` factory
- `src/hsom/discovery.py` – recursive `discover()` + containment-safe validation
- `src/hsom/questions.py` – Jev Choice/Noul builder + custom instructions
- `src/hsom/dispatcher.py` – `system_one` call, branch reader, `dispatch_sequence`
- `src/hsom/executor.py` – strict multi-slot/`{value}` resolution + `subprocess`
- `src/hsom/cli.py` – `hsom` entrypoint, confirm prompt, step transcript
- `src/hsom/api.py` – `Harness`/`RunResult` Python library API (CLI uses it)
- `src/hsom/eval.py` – `--eval` toml loading + no-exec comparison harness
- `src/hsom/runlog.py` – opt-in JSONL run logging (`--log`)
- `tests/` – 134 tests (`PYTHONPATH=src:tests pytest`)
