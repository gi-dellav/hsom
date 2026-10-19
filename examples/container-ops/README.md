# container-ops (held-out)

A command tree written for the held-out benchmark: Docker, Make, grep, find,
cat, and ls over a small release workspace.

The `eval.toml` cases were committed and frozen (`manifest.json`, ref
`heldout-v1`) before any benchmark run. Do not edit them after seeing
results; re-freeze only for an intentional, pre-run change.

```bash
export OPENROUTER_API_KEY=...
./run_eval.sh
```
