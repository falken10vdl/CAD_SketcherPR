#!/usr/bin/env python3
"""Run full CAD_SketcherPR automation pipeline."""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

PIPELINE = [
    "check_cad_sketcherpr_in_git.py",
    "00_clone_merge_and_create_branch.py",
    "01_build_CAD_SketcherPR_addon.py",
    "02_upload_to_falken10vdl.py",
]


def run_script(script_name: str):
    script = SCRIPTS_DIR / script_name
    print(f"Running {script_name}")
    subprocess.run([sys.executable, str(script)], check=True)


def main():
    for script_name in PIPELINE:
        run_script(script_name)
    print("CAD_SketcherPR automation completed")


if __name__ == "__main__":
    main()
