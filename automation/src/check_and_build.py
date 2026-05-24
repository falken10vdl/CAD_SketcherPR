#!/usr/bin/env python3
"""Smart orchestrator: check PR changes, only run full automation when needed."""

import datetime
import glob
import logging
import os
import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
MAX_CHECK_BUILD_LOGS = 10


def setup_logging() -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"check_build_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )
    return log_file


def cleanup_old_check_logs() -> None:
    log_files = sorted(
        glob.glob(str(LOGS_DIR / "check_build_*.log")),
        key=os.path.getmtime,
        reverse=True,
    )
    for old_log in log_files[MAX_CHECK_BUILD_LOGS:]:
        try:
            os.remove(old_log)
            logging.info(f"Removed old check log: {old_log}")
        except Exception as exc:
            logging.warning(f"Could not remove log {old_log}: {exc}")


def check_for_changes() -> bool:
    check_script = SCRIPTS_DIR / "check_pr_changes.py"
    logging.info("Checking for PR changes...")

    try:
        result = subprocess.run(
            [sys.executable, str(check_script)],
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logging.error("Change detection timed out")
        return False
    except Exception as exc:
        logging.error(f"Error running change detection: {exc}")
        return False

    if result.stdout:
        for line in result.stdout.splitlines():
            if line.strip():
                logging.info(f"  {line}")
    if result.stderr:
        for line in result.stderr.splitlines():
            if line.strip():
                logging.warning(f"  {line}")

    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False

    logging.error(f"Change detection failed with exit code {result.returncode}")
    return False


def run_full_build() -> bool:
    logging.info("Changes detected, starting full automation pipeline")
    try:
        result = subprocess.run(
            [sys.executable, str(MAIN)],
            cwd=str(MAIN.parent),
            timeout=7200,
            check=False,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logging.error("Full build timed out after 2 hours")
        return False
    except Exception as exc:
        logging.error(f"Error during full build: {exc}")
        return False


def main():
    start = datetime.datetime.now()
    log_file = setup_logging()
    cleanup_old_check_logs()

    logging.info("=" * 70)
    logging.info("CAD_SketcherPR Smart Build - Check and Build")
    logging.info(f"Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 70)

    force_build = "--force" in sys.argv
    if force_build:
        logging.info("Force mode enabled: skipping change detection")
        should_build = True
    else:
        should_build = check_for_changes()

    if not should_build:
        end = datetime.datetime.now()
        logging.info("No changes detected, build skipped")
        logging.info(f"Check duration: {end - start}")
        return 0

    success = run_full_build()
    end = datetime.datetime.now()
    logging.info(f"Total duration: {end - start}")

    if success:
        logging.info("Build completed successfully")
        return 0

    logging.error("Build failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
