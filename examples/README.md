# Examples and benchmarks

Three real-world, multi-command hsom setups live here. Each bundles:

- `environment.toml` — allowlisted commands
- `eval.toml` — `[[test]]` cases (plans only, never executes)
- `workspace/` — fixture files/dirs so path slots have real candidates
- `run_eval.sh` — runs the eval via OpenRouter with `OPENROUTER_API_KEY`

Suites are declared in [`benchmark.toml`](benchmark.toml):

| Suite | Label | Commands |
| --- | --- | --- |
| `git-workflow` | regression | `git` (status/log/diff/add/branch), `ls`, `cp` |
| `python-qa` | regression | `pytest`, `ruff`, `python`, `ls` |
| `container-ops` | heldout | `docker`, `make`, `grep`, `find`, `cat`, `ls` |

The two regression suites were used during development and are **not**
held-out evidence. The held-out suite is `container-ops`; its
`manifest.json` freezes the hashes of the tree, test set, and workspace.

All benchmark environment files pin `model = "jev-1.13"` (OpenRouter
resolves it to `typesafe/jev-1.13-20260917`; `jev-1.13.0` is rejected by the
provider). Run logs record the model the provider actually returned.

## Running the benchmarks

```bash
export OPENROUTER_API_KEY=...   # https://openrouter.ai/settings/keys
python benchmark.py check       # leakage + frozen-manifest guard
python benchmark.py run         # all suites, Jev + both baselines
```

Useful variants:

```bash
python benchmark.py run --suite container-ops --systems jev --repeats 5
python benchmark.py run --systems structured,logprobs --repeats 3
python benchmark.py run --suite git-workflow --include-excluded
python benchmark.py run --limit 2 --no-excluded   # cheap smoke test
python benchmark.py report                       # regenerate from the latest logs
```

`run` writes one JSONL log per suite/system plus `report.md` and
`report.json` under `examples/benchmark-results/<timestamp>/` (override with
`--output`). The report is rebuilt from those logs by `report`/`run`, so the
stability and interval numbers are derived from the recorded events. Raw logs
are git-ignored. The latest full run is checked in as
[`BENCHMARK-REPORT.md`](BENCHMARK-REPORT.md) and summarized in
[`BENCHMARKS.md`](BENCHMARKS.md).

`run_eval.sh` still works for a per-suite Jev run:

```bash
cd examples/git-workflow && ./run_eval.sh
```

## Accuracy, repeats, and intervals

`benchmark.py` repeats every case `N` times (default 5), then reports:

- **strict** accuracy: a case counts only if every repeat passed;
- per-case `k/N` with an exact Clopper–Pearson interval;
- pooled run accuracy, labelled separately because repeated runs of one case
  are correlated;
- per-run stability ranges;
- token usage, latency p50/p95, and cost from [`pricing.toml`](pricing.toml).

A `0/88`-style result is reported as a one-sided upper bound, not as zero
error. Every rate states its denominator and interval method.

## Exclusions

Probes excluded from the regression suites live in
`git-workflow/excluded.toml` and `python-qa/excluded.toml`. Each has an
`exclude_reason`, and wrong-plan probes set `wrong_plan = true`. `run`
executes them by default and reports both denominators:

- **applied** — headline, excluded probes omitted;
- **removed** — all probes included.

Pass `--no-excluded` when the extra calls are not needed.

## Held-out freeze

`container-ops/manifest.json` was written by:

```bash
python benchmark.py freeze --suite container-ops --ref heldout-v1
```

`check` (and every `run`) verifies the manifest, model pinning, explicit
temperature, and leakage. If any frozen file changes,
the run refuses unless `--allow-unfrozen` is given. Re-freeze only after an
intentional, pre-run change; do not edit the held-out set after seeing
results. The manifest currently records `git_dirty = true` because the suite
was created in an uncommitted working tree; re-freeze after committing so the
manifest captures the final commit.

## Baselines

`run` also executes two LiteLLM baselines through OpenRouter, both pinned to
`openai/gpt-6-luna`:

- `structured` — JSON Schema with enums for each level;
- `logprobs` — numbered options scored from the model's log-probabilities,
  with deterministic ties by tree order. GPT-6 Luna is a reasoning model and
  OpenRouter rejects `logprobs` for it, so this baseline falls back to greedy
  answers. Fallback calls are counted in the report's `Logprob fallbacks`
  column; treat those numbers as a greedy-model comparison, not a true
  log-probability measurement.

Model IDs are pinned in `benchmark.toml`; override them with
`--structured-model` / `--logprob-model`. Baselines include
`none_of_the_above` at each level and abstain only through it; they do not
apply Jev's confidence thresholds. Baseline runs are single-step; the two
regression chain cases are reported as skipped because loop evaluation is out
of scope.

LiteLLM is an optional extra:

```bash
pip install -e '.[benchmark]'
```

## Notes

- Eval mode never executes and never prompts: `write`/`destructive` nodes
  such as `pytest`, `python`, `git add`, `cp`, `docker build`, and `make`
  are only *planned*.
- `python benchmark.py check` is run in CI to catch tree/input leakage and
  stale held-out manifests.
- [`BENCHMARKS.md`](BENCHMARKS.md) summarizes the latest run and links to the
  full [`BENCHMARK-REPORT.md`](BENCHMARK-REPORT.md). The held-out headline is
  `container-ops`; the older `git-workflow`/`python-qa` tables are regression
  data. Previous v1–v6 results remain in git history and are development data
  only.
