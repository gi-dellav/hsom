#!/usr/bin/env bash
# Run the frozen held-out suite through benchmark.py.
#
# Usage:
#   export OPENROUTER_API_KEY=...   # https://openrouter.ai/settings/keys
#   ./run_eval.sh [extra benchmark.py args...]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/../.."

: "${OPENROUTER_API_KEY:?Set OPENROUTER_API_KEY (https://openrouter.ai/settings/keys)}"

exec python benchmark.py run --suite container-ops --systems jev "$@"
