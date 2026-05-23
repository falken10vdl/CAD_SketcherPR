#!/usr/bin/env python3
"""Trigger full automation run. Kept as separate entrypoint for cron parity with bonsaiPR."""

import subprocess
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parent / "main.py"


def main():
    subprocess.run([sys.executable, str(MAIN)], check=True)


if __name__ == "__main__":
    main()
