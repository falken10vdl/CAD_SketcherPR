#!/usr/bin/env python3
"""Ensure the local CAD_SketcherPR automation repo is up to date."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

DEFAULT_REPO_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = Path(os.getenv("AUTOMATION_REPO_DIR", str(DEFAULT_REPO_DIR)))
LOGS_DIR = REPO_DIR / "automation" / "logs"


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)


def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"check_cad_sketcherpr_in_git_{ts}.log"

    with log_file.open("w", encoding="utf-8") as log:
        log.write(f"Checking repository: {REPO_DIR}\n")
        if not (REPO_DIR / ".git").exists():
            log.write("Skipping sync: target path is not a git repository.\n")
            print(f"Skipping repo sync (not a git repository): {REPO_DIR}")
            return

        run(["git", "fetch", "origin", "--prune"], cwd=REPO_DIR)
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_DIR).stdout.strip()
        run(["git", "pull", "--ff-only", "origin", branch], cwd=REPO_DIR)
        commit = run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR).stdout.strip()

        log.write(f"Branch: {branch}\n")
        log.write(f"HEAD: {commit}\n")

    print(f"Updated {REPO_DIR} on branch {branch}")


if __name__ == "__main__":
    main()
