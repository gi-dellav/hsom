"""hsom as a Python library: plan, dry-run, and execute via Harness.

Run with:  PYTHONPATH=src python examples/library_usage.py
Uses dry_run=True so nothing executes and no API key is needed for the
resolve/execute demos. The live `plan` section needs TYPESAFE_API_KEY (or
OPENROUTER_API_KEY with provider="openrouter") and is skipped otherwise.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hsom import EnvConfig, Harness  # noqa: E402


def main() -> None:
    # 1. Config from a TOML-shaped dict (no file needed).
    # NOTE: singular keys mirror environment.toml: "command" (not
    # "commands"), "subcommand" / "flag" / "path" inside each node.
    h = Harness(env={
        "meta": {"model": "jev-latest", "max_steps": 2},
        "command": [
            {"name": "pytest", "description": "run tests",
             "argv": ["pytest", "-q"]},
        ],
    })
    print("commands:", [c.name for c in h.config.commands])

    # 2. Dynamic cwd: override get_cwd() any time.
    h.set_cwd_fn(lambda: os.getcwd())
    print("cwd:", h.get_cwd())

    # 3. Live plan (needs an API key). Provider follows the key: an
    # OpenRouter-only setup routes through OpenRouter billing.
    has_typesafe = bool(os.getenv("TYPESAFE_API_KEY"))
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    if has_typesafe or has_openrouter:
        if not has_typesafe:
            h = Harness(env=h.config, provider="openrouter",
                        get_cwd=lambda: os.getcwd())
        outcome = h.plan("run tests")
        print("plan ok:", outcome.ok, "| reason:", outcome.reason)
        if outcome.ok:
            print("argv:", h.resolve(outcome.action))

        # 4. Chained dry-run: plans only, never executes/prompts.
        result = h.run("run tests", max_steps=2, dry_run=True)
        print("dry-run:", result.stop_reason,
              [s.argv for s in result.steps])
    else:
        print("plan: skipped (set TYPESAFE_API_KEY or OPENROUTER_API_KEY)")

    # 5. Write-risk gating without stdin: on_confirm decides.
    # NOTE: dict configs use TOML-shaped singular keys:
    # "command" / "subcommand" / "flag" / "path" (not plurals).
    h2 = Harness(env={
        "meta": {"model": "jev-latest"},
        "command": [
            {"name": "git", "description": "vcs", "subcommand": [
                {"name": "status", "description": "status",
                 "argv": ["git", "status"]},
            ]},
        ],
    })
    print("config object also works:",
          isinstance(h2.config, EnvConfig))


if __name__ == "__main__":
    main()
