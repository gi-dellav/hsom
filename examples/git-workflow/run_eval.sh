#!/usr/bin/env bash
# Run the git-workflow eval against OpenRouter (Jev via OpenRouter System One API).
#
# Usage:
#   export OPENROUTER_API_KEY=...   # from https://openrouter.ai/settings/keys
#   ./run_eval.sh [extra hsom args...]
#
# Validates both TOML files load, then runs every [[test]] in eval.toml
# (plans only — nothing executes) and appends JSONL events to eval-results.jsonl.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY (https://openrouter.ai/settings/keys)}"

hsom --provider openrouter \
  --env environment.toml \
  --cwd workspace \
  --eval eval.toml \
  --log eval-results.jsonl \
  "$@"
