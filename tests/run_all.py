#!/usr/bin/env python3
"""Run every test script in this folder, one process each, and count the passes.

  python3 tests/run_all.py [--app-repo <mosaico stage-v2 checkout or export>]

With --app-repo (or MOSAICO_APP_REPO) the application-side checks of test_outreach_tool_contract.py run too. Export what it needs without
checking anything out:  git -C <mosaico-app> archive origin/stage-v2 features/outreach | tar -x -C <dir>
Exit 0 only when every script passes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_AWARE = {"test_outreach_tool_contract.py"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-repo", type=Path, default=None)
    args = parser.parse_args()
    scripts = sorted(HERE.glob("test_*.py"))
    failed = []
    for script in scripts:
        command = [sys.executable, str(script)]
        if args.app_repo is not None and script.name in APP_AWARE:
            command += ["--app-repo", str(args.app_repo)]
        result = subprocess.run(command, capture_output=True, text=True)
        last = (result.stdout.strip().splitlines() or result.stderr.strip().splitlines() or [""])[-1]
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'}  {script.name}: {last[:140]}")
        if result.returncode != 0:
            failed.append(script.name)
    print(f"\n{len(scripts) - len(failed)} of {len(scripts)} test scripts passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
