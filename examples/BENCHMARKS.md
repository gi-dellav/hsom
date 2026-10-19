# Benchmarks

Results generated on **2026-10-18** by `benchmark.py` from the frozen
examples under `examples/`. The complete per-case report is checked in as
[`BENCHMARK-REPORT.md`](BENCHMARK-REPORT.md); this file summarizes it.

## Methodology

- Jev: pinned `model = "jev-1.13"` (OpenRouter resolves it to
  `typesafe/jev-1.13-20260917`), `temperature = 0.0`, provider OpenRouter.
- Jev was run **5 times per case** on all three suites. Exclusions were run
  and reported both with and without them.
- Both LiteLLM baselines use `openai/gpt-6-luna` through OpenRouter. Held-out
  baselines were run **3 times per case**; regression baselines **1 time per
  case**. Multi-step cases are not evaluated by the single-step baselines and
  are counted as skipped.
- GPT-6 Luna is a reasoning model and OpenRouter rejects `logprobs` for it.
  The `logprobs` baseline therefore falls back to greedy answers; the number
  of fallback calls is reported in the cost table and the full report
  (held-out fallbacks: 359; regression totals: git
  210, python-qa 156). Its numbers are a greedy-model comparison, not a
  true log-probability measurement.
- **Strict pass** means every repeat passed. Intervals are exact
  Clopper–Pearson 95% over cases. Pooled-run intervals are repeatability
  estimates; repeated runs of one case are correlated, so case-level
  intervals are the primary generalization statement.
- Headline evidence comes from the frozen held-out suite `container-ops`
  (`heldout-v1`). `git-workflow` and `python-qa` are development/regression
  suites and are reported separately.
- Cost uses OpenRouter pricing dated 2026-10-18 (USD). Jev's OpenRouter
  pricing is dynamic/unpublished, so Jev cost is `n/a`.

## Held-out headline (container-ops, 50 cases)

| System | Repeats | Strict pass | Strict rate | 95% CI | Pooled runs | Pooled CI | Skipped | p50 ms | p95 ms | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jev | 5 | 46/50 | 92.0% | 80.8%–97.8% | 230/250 | 87.9%–95.0% | 0 | 364.5 | 448.9 | n/a |
| structured LLM | 3 | 31/50 | 62.0% | 47.2%–75.3% | 105/150 | 62.0%–77.2% | 0 | 3044.9 | 5010.2 | 0.0073 USD |
| logprob LLM (greedy fallback) | 3 | 34/50 | 68.0% | 53.3%–80.5% | 111/150 | 66.2%–80.8% | 0 | 2470.2 | 5546.2 | 0.0054 USD |

Jev held-out failures (all 5/5 runs):

| Case | Expected | Actual |
| --- | --- | --- |
| compose up foreground | `'docker compose up'` | `'docker compose up -d'` |
| find no scope abstains | abstain | `'find src -name '*.py''` |
| grep no scope abstains | abstain | `'grep -R src -e TODO'` |
| make deploy | `'make deploy'` | `'make'` |

Baseline failure highlights:

- `structured` failed 19/50 cases, including enabling `-n`,
  `--tail`, or `--no-cache` when not requested, confusing `cat` with `find`,
  and abstaining on some valid commands.
- `logprobs` (greedy fallback) failed 16/50 cases, including
  wrong command routing, unwanted `-n` injection, and several
  `none_of_the_above` abstentions. One case timed out on a provider call.

## Regression suites

### Aggregate accuracy

`strict` means every repeat passed. Intervals are exact Clopper–Pearson at 95% over cases; pooled intervals treat runs as trials and are labelled separately because repeated runs of one case are correlated.
| Suite | Label | System | Cases | Strict pass | Strict rate | 95% CI | Pooled runs | Pooled CI | Provider-error cases | Skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| git-workflow | regression | jev | 64 | 61 | 95.3% | 86.9%–99.0% | 311/320 | 94.7%–98.7% | 0 | 0 |
| git-workflow | regression | logprobs | 63 | 42 | 66.7% | 53.7%–78.0% | 42/63 | 53.7%–78.0% | 0 | 1 |
| git-workflow | regression | structured | 63 | 37 | 58.7% | 45.6%–71.0% | 37/63 | 45.6%–71.0% | 0 | 1 |
| python-qa | regression | jev | 52 | 50 | 96.2% | 86.8%–99.5% | 254/260 | 95.0%–99.1% | 0 | 0 |
| python-qa | regression | logprobs | 51 | 23 | 45.1% | 31.1%–59.7% | 23/51 | 31.1%–59.7% | 0 | 2 |
| python-qa | regression | structured | 51 | 22 | 43.1% | 29.3%–57.8% | 22/51 | 29.3%–57.8% | 0 | 2 |

### With and without exclusions

`applied` is the headline denominator (excluded probes omitted). `removed` includes the excluded probes and is only available when they were run with `--include-excluded`.
| Suite | System | Exclusions | Cases | Strict pass | Strict rate | 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| git-workflow | jev | applied | 64 | 61 | 95.3% | 86.9%–99.0% |
| git-workflow | jev | removed | 72 | 61 | 84.7% | 74.3%–92.1% |
| git-workflow | logprobs | applied | 63 | 42 | 66.7% | 53.7%–78.0% |
| git-workflow | logprobs | removed | 71 | 42 | 59.2% | 46.8%–70.7% |
| git-workflow | structured | applied | 63 | 37 | 58.7% | 45.6%–71.0% |
| git-workflow | structured | removed | 71 | 38 | 53.5% | 41.3%–65.5% |
| python-qa | jev | applied | 52 | 50 | 96.2% | 86.8%–99.5% |
| python-qa | jev | removed | 62 | 51 | 82.3% | 70.5%–90.8% |
| python-qa | logprobs | applied | 51 | 23 | 45.1% | 31.1%–59.7% |
| python-qa | logprobs | removed | 60 | 25 | 41.7% | 29.1%–55.1% |
| python-qa | structured | applied | 51 | 22 | 43.1% | 29.3%–57.8% |
| python-qa | structured | removed | 60 | 24 | 40.0% | 27.6%–53.5% |

### Stability across repeats

| Suite | System | Per-run pass rates | Range | All-repeat cases |
| --- | --- | --- | --- | --- |
| git-workflow | jev | 95.3%, 98.4%, 98.4%, 96.9%, 96.9% | 95.3%–98.4% | 61/64 |
| git-workflow | logprobs | 66.7% | 66.7%–66.7% | 42/63 |
| git-workflow | structured | 58.7% | 58.7%–58.7% | 37/63 |
| python-qa | jev | 98.1%, 96.2%, 98.1%, 98.1%, 98.1% | 96.2%–98.1% | 50/52 |
| python-qa | logprobs | 45.1% | 45.1%–45.1% | 23/51 |
| python-qa | structured | 43.1% | 43.1%–43.1% | 22/51 |

### Jev regression cases with any failed repeat

This includes excluded probes; see the exclusion table below.

| Suite | Case | Passes | Pattern | Last reason |
| --- | --- | --- | --- | --- |
| git-workflow | brief history | 0/5 | `00000` | expected 'git log --oneline' got 'git log' |
| git-workflow | brief last ten | 2/5 | `01100` | expected 'git log --oneline --max-count=10' got 'git log --max-count=10' |
| git-workflow | changed file names | 0/5 | `00000` | expected abstention but planned 'git status' |
| git-workflow | detailed docs listing | 0/5 | `00000` | expected 'ls -la docs' got 'ls docs -la' |
| git-workflow | different from HEAD | 0/5 | `00000` | expected 'git diff' got 'git diff --stat' |
| git-workflow | overview of all changes | 2/5 | `10100` | expected 'git diff --stat' got 'git diff' |
| git-workflow | scoped diff | 0/5 | `00000` | expected 'git diff src/main.py' got 'git diff' |
| git-workflow | shortlog of contributors | 0/5 | `00000` | expected abstention but planned 'git log --oneline' |
| git-workflow | stage then status | 4/5 | `01111` | ok |
| git-workflow | tip commit | 0/5 | `00000` | expected abstention but planned 'git log' |
| git-workflow | what did I break | 0/5 | `00000` | abstained: request matches no known command |
| python-qa | build green | 3/5 | `10011` | ok |
| python-qa | cross command chain | 0/5 | `00000` | abstained: confidence 0.49 below minimum 0.50 (risk read) |
| python-qa | detailed tests listing | 0/5 | `00000` | abstained: confidence 0.26 below minimum 0.50 (risk read) |
| python-qa | failure summary only | 0/5 | `00000` | expected 'pytest -q --tb=no' got 'pytest -q' |
| python-qa | format write abstains | 4/5 | `10111` | abstained as expected: confidence 0.45 below minimum 0.50 (cli --min-confidence) |
| python-qa | lint test file vague | 3/5 | `10011` | ok |
| python-qa | lint then format | 0/5 | `00000` | expected 2 step(s) but Jev produced 1 (stop: confidence 0.30 below minimum 0.50 (cli --min-confidence)) |
| python-qa | look over code | 0/5 | `00000` | abstained: 'ruff' needs a subcommand and none matches |
| python-qa | run app vague | 0/5 | `00000` | abstained: confidence 0.38 below minimum 0.70 (risk write) |
| python-qa | scrutinize code | 0/5 | `00000` | abstained: confidence 0.40 below minimum 0.50 (risk read) |
| python-qa | verify code | 0/5 | `00000` | abstained: confidence 0.69 below minimum 0.70 (risk write) |

The old chaining cases remain single-run-oriented: `git-workflow / stage then
status` failed 1/5 repeats and `python-qa / lint then format` failed 5/5.
They are regression probes only; loop evaluation remains out of scope.

## Cost and latency (all suites)

Pricing: USD, as of 2026-10-18 (https://openrouter.ai/api/v1/models).

| Suite | System | Models | Input tokens | Output tokens | p50 ms | p95 ms | Cost | Logprob fallbacks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| git-workflow | jev | typesafe/jev-1.13-20260917 | 439627 | 223702 | 333.8 | 511.3 | n/a | 0 |
| git-workflow | logprobs | openai/gpt-6-luna | 24164 | 1050 | 2789.9 | 4428.0 | 0.0029 USD | 210 |
| git-workflow | structured | openai/gpt-6-luna | 27782 | 2924 | 4195.2 | 10514.8 | 0.0042 USD | 0 |
| python-qa | jev | jev-1.13, typesafe/jev-1.13-20260917 | 299635 | 142286 | 364.2 | 574.4 | n/a | 0 |
| python-qa | logprobs | openai/gpt-6-luna | 17787 | 780 | 2709.0 | 3910.6 | 0.0022 USD | 156 |
| python-qa | structured | openai/gpt-6-luna | 20177 | 2162 | 3075.7 | 4431.7 | 0.0031 USD | 0 |
| container-ops | jev | typesafe/jev-1.13-20260917 | 437370 | 259493 | 364.5 | 448.9 | n/a | 0 |
| container-ops | logprobs | openai/gpt-6-luna | 45013 | 1801 | 2470.2 | 5546.2 | 0.0054 USD | 359 |
| container-ops | structured | openai/gpt-6-luna | 48757 | 4925 | 3044.9 | 5010.2 | 0.0073 USD | 0 |

## Exclusions

Every declared exclusion is listed with its reason. `wrong plan` marks probes where the selected operation is not the intended one.
Declared exclusions: 18 (wrong plan: 15).

| Suite | Case | Input | Expected | Actual | Reason | Wrong plan | Runs | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| git-workflow | tip commit | show just the tip commit | abstain | git log | wrong-but-stable: the allowlist only models 5/10/20-commit counts, so the closest plan is bare git log | yes | 5 | 0 |
| git-workflow | overview of all changes | give me an overview of all changes | git diff --stat | git diff | input-fragile: --stat toggles between runs | yes | 5 | 2 |
| git-workflow | what did I break | what did I break? | git diff |  | input-fragile: abstains or flips to a different diff plan | yes | 5 | 0 |
| git-workflow | different from HEAD | what's different from HEAD? | git diff | git diff --stat | input-fragile: abstains or flips to a different diff plan | yes | 5 | 0 |
| git-workflow | shortlog of contributors | show a shortlog of contributors | abstain | git log --oneline | wrong-but-stable: plans git log --oneline although shortlog is not allowlisted | yes | 5 | 0 |
| git-workflow | scoped diff | limit the diff to the main file | git diff src/main.py | git diff | wrong-but-stable: the optional diff scope slot is silently dropped | yes | 5 | 0 |
| git-workflow | detailed docs listing | list the docs directory with details | ls -la docs | ls docs -la | argv-order artifact: flags are appended after the path slot, producing 'ls docs -la' | no | 5 | 0 |
| git-workflow | changed file names | show only the names of changed files | abstain | git status | wrong-but-stable: --name-only is not allowlisted; the closest plan is a diff variant | yes | 5 | 0 |
| python-qa | build green | is the build green? | pytest -q | pytest -q | wrong-but-stable: abstains below the read threshold while the stable twin is kept in the suite | yes | 5 | 3 |
| python-qa | smoke test app | smoke-test the app | pytest -q | pytest -q | input-fragile: pytest-vs-python routing is defensible either way | no | 5 | 5 |
| python-qa | failure summary only | run tests and show only the failure summary | pytest -q --tb=no | pytest -q | wrong-but-stable: drops the requested --tb=no flag | yes | 5 | 0 |
| python-qa | detailed tests listing | list tests in detail | ls tests |  | unsupported detail flag: the allowlist has no long-listing flag, so the base listing is the honest degradation | no | 5 | 0 |
| python-qa | verify code | verify the code | ruff check |  | input-fragile: a single-word synonym without a file anchor abstains | yes | 5 | 0 |
| python-qa | scrutinize code | scrutinize the code | ruff check |  | input-fragile: a single-word synonym without a file anchor abstains | yes | 5 | 0 |
| python-qa | look over code | look over the code | ruff check |  | input-fragile: a single-word synonym without a file anchor abstains | yes | 5 | 0 |
| python-qa | lint test file vague | lint the test file | ruff check tests/test_app.py | ruff check tests/test_app.py | wrong-but-stable: the vague file reference does not resolve to the test file | yes | 5 | 3 |
| python-qa | run app vague | run the app | python src/app.py |  | wrong-but-stable: the script slot needs the filename spelled out | yes | 5 | 0 |
| python-qa | cross command chain | run ruff check then run tests | ruff check ; pytest -q |  | wrong-but-stable: cross-command chains abstain at the command layer | yes | 5 | 0 |

## Artifacts and reproduce

```bash
export OPENROUTER_API_KEY=...
python benchmark.py check
python benchmark.py run --systems jev --repeats 5 --include-excluded
python benchmark.py report
```

Raw JSONL logs and the generated report are git-ignored under
`examples/benchmark-results/`. The checked-in
[`BENCHMARK-REPORT.md`](BENCHMARK-REPORT.md) is the complete record for the
run above, including every per-case result, all baseline cases, and
provenance hashes.

## History

Previous `v1`–`v6` development runs are retained in git history. Their tables
were development data, not held-out evidence: they predated model pinning,
leakage removal, repeated runs, confidence intervals, and baselines. This
document supersedes them for citation.
