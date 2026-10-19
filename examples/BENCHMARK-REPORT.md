# hsom benchmark report

Generated: 2026-10-18 21:38:33Z

Suites under `examples/`. `regression` suites were used during development; `heldout` suites are frozen before execution. Headline numbers should come from held-out suites only.

## Aggregate accuracy

`strict` means every repeat passed. Intervals are exact Clopper–Pearson at 95% over cases; pooled intervals treat runs as trials and are labelled separately because repeated runs of one case are correlated.

| Suite | Label | System | Cases | Strict pass | Strict rate | 95% CI | Pooled runs | Pooled CI | Provider-error cases | Skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| git-workflow | regression | jev | 64 | 61 | 95.3% | 86.9%–99.0% | 311/320 | 94.7%–98.7% | 0 | 0 |
| git-workflow | regression | logprobs | 63 | 42 | 66.7% | 53.7%–78.0% | 42/63 | 53.7%–78.0% | 0 | 1 |
| git-workflow | regression | structured | 63 | 37 | 58.7% | 45.6%–71.0% | 37/63 | 45.6%–71.0% | 0 | 1 |
| python-qa | regression | jev | 52 | 50 | 96.2% | 86.8%–99.5% | 254/260 | 95.0%–99.1% | 0 | 0 |
| python-qa | regression | logprobs | 51 | 23 | 45.1% | 31.1%–59.7% | 23/51 | 31.1%–59.7% | 0 | 2 |
| python-qa | regression | structured | 51 | 22 | 43.1% | 29.3%–57.8% | 22/51 | 29.3%–57.8% | 0 | 2 |
| container-ops | heldout | jev | 50 | 46 | 92.0% | 80.8%–97.8% | 230/250 | 87.9%–95.0% | 0 | 0 |
| container-ops | heldout | logprobs | 50 | 34 | 68.0% | 53.3%–80.5% | 111/150 | 66.2%–80.8% | 0 | 0 |
| container-ops | heldout | structured | 50 | 31 | 62.0% | 47.2%–75.3% | 105/150 | 62.0%–77.2% | 0 | 0 |

## With and without exclusions

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
| container-ops | jev | applied | 50 | 46 | 92.0% | 80.8%–97.8% |
| container-ops | logprobs | applied | 50 | 34 | 68.0% | 53.3%–80.5% |
| container-ops | structured | applied | 50 | 31 | 62.0% | 47.2%–75.3% |

## Stability across repeats

| Suite | System | Per-run pass rates | Range | All-repeat cases |
| --- | --- | --- | --- | --- |
| git-workflow | jev | 95.3%, 98.4%, 98.4%, 96.9%, 96.9% | 95.3%–98.4% | 61/64 |
| git-workflow | logprobs | 66.7% | 66.7%–66.7% | 42/63 |
| git-workflow | structured | 58.7% | 58.7%–58.7% | 37/63 |
| python-qa | jev | 98.1%, 96.2%, 98.1%, 98.1%, 98.1% | 96.2%–98.1% | 50/52 |
| python-qa | logprobs | 45.1% | 45.1%–45.1% | 23/51 |
| python-qa | structured | 43.1% | 43.1%–43.1% | 22/51 |
| container-ops | jev | 92.0%, 92.0%, 92.0%, 92.0%, 92.0% | 92.0%–92.0% | 46/50 |
| container-ops | logprobs | 76.0%, 70.0%, 76.0% | 70.0%–76.0% | 34/50 |
| container-ops | structured | 72.0%, 68.0%, 70.0% | 68.0%–72.0% | 31/50 |

## Cost and latency

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

## Per-case results

### git-workflow / jev

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all branches | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| amend abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| back up file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| bare diff | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| bare history | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| bare ls | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| bare ls detail | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| blame abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| branches paraphrase | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| brief history | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | no | expected 'git log --oneline' got 'git log' |
| brief last ten | 5 | 2 | 40.0% | 5.3%–85.3% | `01100` | no | expected 'git log --oneline --max-count=10' got 'git log --max-count=10' |
| brief last twenty | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| casual status | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| changed file names | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected abstention but planned 'git status' |
| clone trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| commit abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| compact five | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| copy all abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: no cp.src file/dir matches the request |
| copy bare | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| copy here | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| copy main into docs | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| copy utils into docs | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| current branch | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| current dir | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| delete abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| detailed docs listing | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected 'ls -la docs' got 'ls docs -la' |
| diff stat | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| different from HEAD | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected 'git diff' got 'git diff --stat' |
| dirty tree | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| duplicate file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| fetch trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| full five | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| last five commits | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lately commits | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| list branches | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| list docs dir | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| local only | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| merge abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| move trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| newest first | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| nonsense abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| not compact | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| outstanding work | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| overview changes | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| overview of all changes | 5 | 2 | 40.0% | 5.3%–85.3% | `10100` | yes | expected 'git diff --stat' got 'git diff' |
| push abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| remotes shorthand | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| rename trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| repo state | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| reset abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: no git.add.src file/dir matches the request |
| revert trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| scoped diff | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected 'git diff src/main.py' got 'git diff' |
| shortlog of contributors | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected abstention but planned 'git log --oneline' |
| show patch | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| squash trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| stage all abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: no git.add.src file/dir matches the request |
| stage main file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| stage markdown abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: no git.add.src file/dir matches the request |
| stage then status | 5 | 4 | 80.0% | 28.4%–99.5% | `01111` | no | ok |
| stage utils file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| stash abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| status | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| status paraphrase | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| summarize changes | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| tag trap abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'git' needs a subcommand and none matches |
| tip commit | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected abstention but planned 'git log' |
| tree clean | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| uncommitted full | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| unstaged compact | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| what did I break | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: request matches no known command |
| whats here | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| whole history | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |

### git-workflow / logprobs

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all branches | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| amend abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| back up file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| bare diff | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git diff' got 'git diff --stat' |
| bare history | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline' |
| bare ls | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls' got 'ls -la' |
| bare ls detail | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| blame abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| branches paraphrase | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git branch' got 'git branch -a' |
| brief history | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log --oneline' got 'git log --oneline --max-count=5' |
| brief last ten | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| brief last twenty | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| casual status | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| changed file names | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected abstention but planned 'git status' |
| clone trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| commit abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| compact five | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| copy all abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'cp src/main.py docs' |
| copy bare | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| copy here | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| copy main into docs | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| copy utils into docs | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| current branch | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git branch' got 'git branch -a' |
| current dir | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls' got 'ls -la' |
| delete abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| detailed docs listing | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ls -la docs' got 'ls docs -la' |
| diff stat | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| different from HEAD | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff' got 'git diff --stat' |
| dirty tree | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| duplicate file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| fetch trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| full five | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log --max-count=5' got 'git log --oneline --max-count=5' |
| last five commits | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log --max-count=5' got 'git log --oneline --max-count=5' |
| lately commits | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline --max-count=5' |
| list branches | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git branch' got 'git branch -a' |
| list docs dir | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls docs' got 'ls docs -la' |
| local only | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| merge abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| move trap abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'cp src/main.py docs' |
| newest first | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline --max-count=5' |
| nonsense abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| not compact | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| outstanding work | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| overview changes | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git diff --stat' got 'git log --oneline --max-count=10' |
| overview of all changes | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff --stat' got 'git log --oneline --max-count=10' |
| push abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| remotes shorthand | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| rename trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| repo state | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| reset abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git add src/main.py' |
| revert trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| scoped diff | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff src/main.py' got 'git diff src/main.py --stat' |
| shortlog of contributors | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected abstention but planned 'git log --oneline --max-count=5' |
| show patch | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git diff' got 'git diff --stat' |
| squash trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| stage all abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git add src/main.py' |
| stage main file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| stage markdown abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git add src/utils.py' |
| stage utils file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| stash abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| status | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| status paraphrase | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| summarize changes | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| tag trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| tip commit | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected abstention but planned 'git log --oneline --max-count=5' |
| tree clean | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| uncommitted full | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| unstaged compact | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| what did I break | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff' got 'git status' |
| whats here | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls' got 'ls -la' |
| whole history | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |

### git-workflow / structured

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all branches | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| amend abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| back up file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| bare diff | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git diff' got 'git diff --stat' |
| bare history | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline --max-count=10' |
| bare ls | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls' got 'ls -la' |
| bare ls detail | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| blame abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| branches paraphrase | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git branch' got 'git branch -a' |
| brief history | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log --oneline' got 'git log --oneline --max-count=5' |
| brief last ten | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| brief last twenty | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| casual status | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| changed file names | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected abstention but planned 'git diff --stat' |
| clone trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| commit abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| compact five | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| copy all abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'cp src/main.py docs' |
| copy bare | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| copy here | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'cp src/main.py' got 'cp src/main.py src' |
| copy main into docs | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'cp src/main.py docs' got 'cp src/main.py' |
| copy utils into docs | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| current branch | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git branch' got 'git branch -a' |
| current dir | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls' got 'ls -la' |
| delete abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| detailed docs listing | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ls -la docs' got 'ls docs -la' |
| diff stat | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| different from HEAD | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff' got 'git diff --stat' |
| dirty tree | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| duplicate file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| fetch trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| full five | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log --max-count=5' got 'git log --oneline --max-count=5' |
| last five commits | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log --max-count=5' got 'git log --oneline --max-count=5' |
| lately commits | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline' |
| list branches | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git branch' got 'git branch -a' |
| list docs dir | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls docs' got 'ls docs -la' |
| local only | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| merge abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git branch -a' |
| move trap abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'cp src/main.py docs' |
| newest first | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline' |
| nonsense abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| not compact | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| outstanding work | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| overview changes | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git diff --stat' got 'git status' |
| overview of all changes | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | yes | ok |
| push abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git branch -a' |
| remotes shorthand | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| rename trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| repo state | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| reset abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| revert trap abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git diff src/main.py --stat' |
| scoped diff | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff src/main.py' got 'git diff src/main.py --stat' |
| shortlog of contributors | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected abstention but planned 'git log --oneline' |
| show patch | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git diff' got 'git diff --stat' |
| squash trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| stage all abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git add src/main.py' |
| stage main file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| stage markdown abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'git add src/main.py' |
| stage utils file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| stash abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| status | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| status paraphrase | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| summarize changes | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| tag trap abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: 'git' needs a subcommand |
| tip commit | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected abstention but planned 'git log --oneline --max-count=5' |
| tree clean | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| uncommitted full | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| unstaged compact | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| what did I break | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'git diff' got 'git status' |
| whats here | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ls' got 'ls -la' |
| whole history | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'git log' got 'git log --oneline' |

### python-qa / jev

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| apply format maps to check | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| audit app | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| build green | 5 | 3 | 60.0% | 14.7%–94.7% | `10011` | yes | ok |
| build passing | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| coverage flagless | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| cross command chain | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: confidence 0.49 below minimum 0.50 (risk read) |
| debugger abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| detailed tests listing | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: confidence 0.26 below minimum 0.50 (risk read) |
| execute interpreter | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| failure summary only | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | expected 'pytest -q --tb=no' got 'pytest -q' |
| filter flagless | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| fix lint maps to lint | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| format app explicit | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| format check | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| format check app file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| format quietly | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| format write abstains | 5 | 4 | 80.0% | 28.4%–99.5% | `10111` | no | abstained as expected: confidence 0.45 below minimum 0.50 (cli --min-confidence) |
| hygiene repo | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint app and tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint app file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint both maps to lint | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint everything | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint project | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint test file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| lint test file vague | 5 | 3 | 60.0% | 14.7%–94.7% | `10011` | yes | ok |
| lint then format | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | no | expected 2 step(s) but Jev produced 1 (stop: confidence 0.30 below minimum 0.50 (cli --min-confidence)) |
| list src dir | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| list tests dir | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| long keep going | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| look over code | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: 'ruff' needs a subcommand and none matches |
| mypy maps to lint | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| nonsense abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| oneliner abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: no python.script file/dir matches the request |
| pip install abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| pytest by tool | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| python on tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| quiet tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| root contents | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run app paraphrase | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run app script | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run app vague | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: confidence 0.38 below minimum 0.70 (risk write) |
| run suite paraphrase | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run tests both flags | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run tests long traceback | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run tests no traceback | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run tests short traceback | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| run tests stop early | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| scrutinize code | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: confidence 0.40 below minimum 0.50 (risk read) |
| smoke test app | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | yes | ok |
| start app | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| stop early no traceback | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| test app file | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| test doctor | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| tidy formatting | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| unit tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| upgrade abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| venv abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| verbose trap | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| verify code | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | yes | abstained: confidence 0.69 below minimum 0.70 (risk write) |
| verify formatting | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| whole suite | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |

### python-qa / logprobs

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| apply format maps to check | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff format --check' got 'ruff check src/app.py' |
| audit app | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| build green | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'pytest -q' got 'pytest -q --tb=short' |
| build passing | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q --tb=short' |
| coverage flagless | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| debugger abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'python src/app.py' |
| detailed tests listing | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ls tests' got 'pytest -q -x --tb=long' |
| execute interpreter | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| failure summary only | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'pytest -q --tb=no' got 'pytest -q -x --tb=short' |
| filter flagless | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| fix lint maps to lint | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff check' got 'ruff check src/app.py' |
| format app explicit | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| format check | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| format check app file | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff format --check src/app.py' got 'ruff check src/app.py' |
| format quietly | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff format --check' got 'ruff check' |
| format write abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'ruff format --check src/app.py' |
| hygiene repo | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint app and tests | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint app file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint both maps to lint | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint everything | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint project | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff check' got 'ruff check src/app.py' |
| lint test file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint test file vague | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | yes | ok |
| list src dir | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| list tests dir | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| long keep going | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| look over code | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ruff check' got 'ls' |
| mypy maps to lint | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | abstained: none_of_the_above at command layer |
| nonsense abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| oneliner abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'python src/app.py' |
| pip install abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| pytest by tool | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=long' |
| python on tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'python tests/test_app.py' |
| quiet tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| root contents | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run app paraphrase | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run app script | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run app vague | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | yes | ok |
| run suite paraphrase | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| run tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| run tests both flags | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run tests long traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q --tb=long' got 'pytest -q -x --tb=long' |
| run tests no traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q --tb=no' got 'pytest -q -x --tb=no' |
| run tests short traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q --tb=short' got 'pytest -q -x --tb=short' |
| run tests stop early | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q -x' got 'pytest -q -x --tb=short' |
| scrutinize code | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | abstained: none_of_the_above at command layer |
| smoke test app | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| start app | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| stop early no traceback | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| test app file | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| test doctor | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| tidy formatting | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | abstained: 'ruff' needs a subcommand |
| unit tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| upgrade abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| venv abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'python src/app.py' |
| verbose trap | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=long' |
| verify code | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ruff check' got 'pytest -q --tb=long' |
| verify formatting | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| whole suite | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x' |

### python-qa / structured

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| apply format maps to check | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff format --check' got 'ruff format --check src/app.py' |
| audit app | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| build green | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | yes | ok |
| build passing | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q --tb=short' |
| coverage flagless | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| debugger abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'python src/app.py' |
| detailed tests listing | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ls tests' got 'pytest -q -x --tb=long' |
| execute interpreter | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| failure summary only | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'pytest -q --tb=no' got 'pytest -q -x --tb=short' |
| filter flagless | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| fix lint maps to lint | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff check' got 'ruff check src/app.py' |
| format app explicit | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| format check | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| format check app file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| format quietly | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff format --check' got 'ruff check src/app.py' |
| format write abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'ruff format --check src/app.py' |
| hygiene repo | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint app and tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff check' got 'ruff check src/app.py' |
| lint app file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint both maps to lint | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint everything | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint project | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'ruff check' got 'ruff check src/app.py' |
| lint test file | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| lint test file vague | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | yes | ok |
| list src dir | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| list tests dir | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| long keep going | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| look over code | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ruff check' got 'ls' |
| mypy maps to lint | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | abstained: none_of_the_above at command layer |
| nonsense abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| oneliner abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'python src/app.py' |
| pip install abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| pytest by tool | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| python on tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| quiet tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| root contents | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run app paraphrase | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run app script | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run app vague | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | abstained: none_of_the_above at command layer |
| run suite paraphrase | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| run tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| run tests both flags | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| run tests long traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q --tb=long' got 'pytest -q -x --tb=long' |
| run tests no traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q --tb=no' got 'pytest -q -x --tb=short' |
| run tests short traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q --tb=short' got 'pytest -q -x --tb=short' |
| run tests stop early | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q -x' got 'pytest -q -x --tb=short' |
| scrutinize code | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | abstained: none_of_the_above at command layer |
| smoke test app | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| start app | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | abstained: none_of_the_above at command layer |
| stop early no traceback | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q -x --tb=no' got 'pytest -q -x --tb=short' |
| test app file | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| test doctor | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| tidy formatting | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| unit tests | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=short' |
| upgrade abstains | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | abstained: none_of_the_above at command layer |
| venv abstains | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected abstention but planned 'python src/app.py' |
| verbose trap | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=long' |
| verify code | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | yes | expected 'ruff check' got 'pytest -q -x --tb=short' |
| verify formatting | 1 | 1 | 100.0% | 2.5%–100.0% | `1` | no | ok |
| whole suite | 1 | 0 | 0.0% | 0.0%–97.5% | `0` | no | expected 'pytest -q' got 'pytest -q -x --tb=long' |

### container-ops / jev

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all containers | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| build image | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| build without cache | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| cat app | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| cat compose | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| cat deploy script | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| cat dockerfile | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| cat readme | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| compose down | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| compose up background | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| compose up foreground | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | no | expected 'docker compose up' got 'docker compose up -d' |
| copy abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| delete logs abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| find logs | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| find markdown docs | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| find no scope abstains | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | no | expected abstention but planned 'find src -name '*.py'' |
| find python src | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| format python abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| git abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| grep FIXME tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| grep TODO src | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| grep def docs | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| grep import line numbers | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| grep no scope abstains | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | no | expected abstention but planned 'grep -R src -e TODO' |
| install deps abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| kubectl abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| local images | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| logs no tail | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| logs tail 100 | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| logs tail 20 | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| logs tail 50 | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| logs unsupported tail | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| ls docs | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| ls root | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| ls scripts | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| ls tests | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| make build | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| make build verbose degrade | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| make clean | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| make default | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| make deploy | 5 | 0 | 0.0% | 0.0%–52.2% | `00000` | no | expected 'make deploy' got 'make' |
| make test | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| make test stop degrade | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| move abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| push image abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: confidence 0.64 below minimum 0.70 (risk write) |
| pytest abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: request matches no known command |
| remove containers abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'docker' needs a subcommand and none matches |
| running containers | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| stopped containers | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | ok |
| version abstains | 5 | 5 | 100.0% | 47.8%–100.0% | `11111` | no | abstained as expected: 'docker' needs a subcommand and none matches |

### container-ops / logprobs

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all containers | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| build image | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'docker build .' got 'docker build . --no-cache' |
| build without cache | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat app | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat compose | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat deploy script | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat dockerfile | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat readme | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| compose down | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| compose up background | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| compose up foreground | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'docker compose up' got 'docker compose up -d' |
| copy abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| delete logs abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| find logs | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| find markdown docs | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| find no scope abstains | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected abstention but planned 'find src -name '*.py'' |
| find python src | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| format python abstains | 3 | 2 | 66.7% | 9.4%–99.2% | `101` | no | abstained: none_of_the_above at command layer |
| git abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| grep FIXME tests | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'grep -R tests -e FIXME' got 'grep -R tests -e FIXME -n' |
| grep TODO src | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'grep -R src -e TODO' got 'grep -R src -e TODO -n' |
| grep def docs | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'grep -R docs -e def' got 'grep -R docs -e def -n' |
| grep import line numbers | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| grep no scope abstains | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected abstention but planned 'grep -R src/utils.py -e TODO -n' |
| install deps abstains | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected abstention but planned 'make build' |
| kubectl abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| local images | 3 | 2 | 66.7% | 9.4%–99.2% | `011` | no | ok |
| logs no tail | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'docker compose logs' got 'docker compose logs --tail=50' |
| logs tail 100 | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs tail 20 | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs tail 50 | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs unsupported tail | 3 | 1 | 33.3% | 0.8%–90.6% | `100` | no | expected 'docker compose logs' got 'docker compose logs --tail=20' |
| ls docs | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| ls root | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| ls scripts | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| ls tests | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make build | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make build verbose degrade | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make clean | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make default | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make deploy | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make test | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make test stop degrade | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| move abstains | 3 | 2 | 66.7% | 9.4%–99.2% | `101` | no | abstained: none_of_the_above at command layer |
| push image abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: 'docker' needs a subcommand |
| pytest abstains | 3 | 1 | 33.3% | 0.8%–90.6% | `001` | no | abstained: none_of_the_above at command layer |
| remove containers abstains | 3 | 1 | 33.3% | 0.8%–90.6% | `100` | no | expected abstention but planned 'docker ps -a' |
| running containers | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | baseline error: Timeout: litellm.Timeout: Timeout Error: OpenrouterException - litellm.Timeout: Connection timed out after 60.0 seconds. |
| stopped containers | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| version abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: 'docker' needs a subcommand |

### container-ops / structured

| Case | Runs | Pass | Rate | 95% CI | Pattern | Excluded | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all containers | 3 | 2 | 66.7% | 9.4%–99.2% | `101` | no | ok |
| build image | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'docker build .' got 'docker build . --no-cache' |
| build without cache | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat app | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'cat src/app.py' got 'find src -name '*.py'' |
| cat compose | 3 | 2 | 66.7% | 9.4%–99.2% | `011` | no | ok |
| cat deploy script | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'cat scripts/deploy.sh' got 'find scripts -name '*.py'' |
| cat dockerfile | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| cat readme | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| compose down | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| compose up background | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| compose up foreground | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'docker compose up' got 'docker compose up -d' |
| copy abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: 'docker' needs a subcommand |
| delete logs abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| find logs | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| find markdown docs | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| find no scope abstains | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected abstention but planned 'find src -name '*.py'' |
| find python src | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| format python abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| git abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| grep FIXME tests | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'grep -R tests -e FIXME' got 'grep -R tests -e FIXME -n' |
| grep TODO src | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'grep -R src -e TODO' got 'grep -R src -e TODO -n' |
| grep def docs | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'grep -R docs -e def' got 'grep -R docs -e def -n' |
| grep import line numbers | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| grep no scope abstains | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected abstention but planned 'grep -R src -e TODO -n' |
| install deps abstains | 3 | 1 | 33.3% | 0.8%–90.6% | `100` | no | expected abstention but planned 'make build' |
| kubectl abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| local images | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs no tail | 3 | 1 | 33.3% | 0.8%–90.6% | `100` | no | expected 'docker compose logs' got 'docker compose logs --tail=50' |
| logs tail 100 | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs tail 20 | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs tail 50 | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| logs unsupported tail | 3 | 2 | 66.7% | 9.4%–99.2% | `101` | no | ok |
| ls docs | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| ls root | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| ls scripts | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| ls tests | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make build | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make build verbose degrade | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make clean | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make default | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'make' got 'make build' |
| make deploy | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make test | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| make test stop degrade | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | ok |
| move abstains | 3 | 2 | 66.7% | 9.4%–99.2% | `011` | no | abstained: none_of_the_above at command layer |
| push image abstains | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected abstention but planned 'docker images' |
| pytest abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: none_of_the_above at command layer |
| remove containers abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: 'docker' needs a subcommand |
| running containers | 3 | 0 | 0.0% | 0.0%–70.8% | `000` | no | expected 'docker ps' got 'docker ps -a' |
| stopped containers | 3 | 2 | 66.7% | 9.4%–99.2% | `110` | no | abstained: none_of_the_above at command layer |
| version abstains | 3 | 3 | 100.0% | 29.2%–100.0% | `111` | no | abstained: 'docker' needs a subcommand |

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

## Provenance

- **git-workflow** (regression): `git-workflow/environment.toml` sha256 `b6069d6731a74dab`, `git-workflow/eval.toml` sha256 `b0d9620a48d8326b`
  requested model `jev-1.13`, temperature `0.0`, provider `openrouter`
- **python-qa** (regression): `python-qa/environment.toml` sha256 `bd8d42021bbeaf81`, `python-qa/eval.toml` sha256 `2b8c231d8fb03d82`
  requested model `jev-1.13`, temperature `0.0`, provider `openrouter`
- **container-ops** (heldout): `container-ops/environment.toml` sha256 `1562da2cfb06b18e`, `container-ops/eval.toml` sha256 `8b183b2227d07a1e`
  requested model `jev-1.13`, temperature `0.0`, provider `openrouter`
  frozen ref `heldout-v1`, git `689d4c3e7e8417ef5ce931ecd31d45034f3f2a7d`, dirty=True

Pricing file: `pricing.toml`

