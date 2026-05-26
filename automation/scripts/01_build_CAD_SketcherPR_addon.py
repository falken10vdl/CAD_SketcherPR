#!/usr/bin/env python3
"""Build CAD_SketcherPR ZIP addon from merged branch."""

import glob
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_CLONE_DIR = Path(os.getenv("BASE_CLONE_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/CAD_Sketcher"))
BUILD_BASE_DIR = Path(os.getenv("BUILD_BASE_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR-build"))
REPORT_PATH = Path(os.getenv("REPORT_PATH", "/home/falken10vdl/CAD_SketcherPRDevel"))


def read_state():
    state_file = Path(__file__).resolve().parents[1] / "logs" / "pr_state.json"
    if not state_file.exists():
        raise RuntimeError("Missing state file. Run 00_clone_merge_and_create_branch.py first.")
    return json.loads(state_file.read_text(encoding="utf-8"))


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def update_manifest_for_pr_build(manifest_path: Path, package_version: str):
    text = manifest_path.read_text(encoding="utf-8")
    text = re.sub(r'^id\s*=\s*"[^"]+"', 'id = "CAD_SketcherPR"', text, flags=re.M)
    text = re.sub(r'^name\s*=\s*"[^"]+"', 'name = "CAD Sketcher PR"', text, flags=re.M)
    # Keep manifest version aligned with index/release version to satisfy Blender installer checks.
    text = re.sub(r'^version\s*=\s*"[^"]+"', f'version = "{package_version}"', text, flags=re.M)
    text = re.sub(
        r'^maintainer\s*=\s*"[^"]+"',
        'maintainer = "falken10vdl <noreply@users.noreply.github.com>"',
        text,
        flags=re.M,
    )
    manifest_path.write_text(text, encoding="utf-8")


def copy_source(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(
            ".git",
            ".github",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.log",
            "docs",
        ),
    )


def append_report(report_file: Path, lines):
    with report_file.open("a", encoding="utf-8") as f:
        f.write("\n")
        for line in lines:
            f.write(line + "\n")


def main():
    state = read_state()
    branch = state["branch"]
    version = state["version"]
    timestamp = state["timestamp"]
    package_version = f"{version}-{timestamp}"
    report_file = Path(state["report"])

    run(["git", "checkout", branch], cwd=BASE_CLONE_DIR)

    BUILD_BASE_DIR.mkdir(parents=True, exist_ok=True)
    package_dir = BUILD_BASE_DIR / "CAD_SketcherPR"
    dist_dir = BUILD_BASE_DIR / "dist"

    copy_source(BASE_CLONE_DIR, package_dir)

    manifest = package_dir / "blender_manifest.toml"
    if not manifest.exists():
        raise RuntimeError("blender_manifest.toml not found in source")

    update_manifest_for_pr_build(manifest, package_version)

    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_base = dist_dir / f"CAD_SketcherPR_{package_version}"

    if (zip_base.with_suffix(".zip")).exists():
        (zip_base.with_suffix(".zip")).unlink()

    # Create archive with CAD_SketcherPR folder at root (required by Blender extension format)
    shutil.make_archive(str(zip_base), "zip", root_dir=BUILD_BASE_DIR, base_dir="CAD_SketcherPR")
    zip_file = zip_base.with_suffix(".zip")

    append_report(
        report_file,
        [
            "Build Result",
            "------------",
            f"Package directory: {package_dir}",
            f"Artifact: {zip_file}",
        ],
    )

    artifacts = sorted(glob.glob(str(dist_dir / "*.zip")))
    print("Artifacts:")
    for a in artifacts:
        print(a)


if __name__ == "__main__":
    main()
