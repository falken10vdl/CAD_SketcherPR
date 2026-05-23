#!/usr/bin/env python3
"""Clone/update CAD_Sketcher, merge open upstream PRs, and push a timestamped branch to fork."""

import json
import os
import re
import subprocess
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
FORK_OWNER = os.getenv("FORK_OWNER", "falken10vdl")
FORK_REPO = os.getenv("FORK_REPO", "CAD_Sketcher")
SOURCE_REPO_OWNER = os.getenv("SOURCE_REPO_OWNER", "hlorus")
SOURCE_REPO_NAME = os.getenv("SOURCE_REPO_NAME", "CAD_Sketcher")
SOURCE_BASE_BRANCH = os.getenv("SOURCE_BASE_BRANCH", "main")
BASE_CLONE_DIR = Path(os.getenv("BASE_CLONE_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/CAD_Sketcher"))
REPORT_PATH = Path(os.getenv("REPORT_PATH", "/home/falken10vdl/CAD_SketcherPRDevel"))
MAX_PRS_TO_MERGE = int(os.getenv("MAX_PRS_TO_MERGE", "100"))


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def read_output(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def read_version_from_manifest(repo_dir: Path) -> str:
    manifest = repo_dir / "blender_manifest.toml"
    if not manifest.exists():
        return "0.0.0"
    text = manifest.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "0.0.0"


def fetch_open_prs():
    url = f"https://api.github.com/repos/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/pulls"
    params = {"state": "open", "per_page": 100}
    base_headers = {"Accept": "application/vnd.github+json"}

    # If token auth fails (e.g. expired token), fall back to public API access.
    if GITHUB_TOKEN:
        auth_headers = dict(base_headers)
        auth_headers["Authorization"] = f"token {GITHUB_TOKEN}"
        r = requests.get(url, headers=auth_headers, params=params, timeout=30)
        if r.status_code != 401:
            r.raise_for_status()
            return r.json()[:MAX_PRS_TO_MERGE]
        print("Warning: GITHUB_TOKEN unauthorized for pulls API; retrying without auth")

    r = requests.get(url, headers=base_headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()[:MAX_PRS_TO_MERGE]


def ensure_repo():
    BASE_CLONE_DIR.parent.mkdir(parents=True, exist_ok=True)
    if not (BASE_CLONE_DIR / ".git").exists():
        run(["git", "clone", f"https://github.com/{FORK_OWNER}/{FORK_REPO}.git", str(BASE_CLONE_DIR)])

    run(["git", "remote", "set-url", "origin", f"https://github.com/{FORK_OWNER}/{FORK_REPO}.git"], cwd=BASE_CLONE_DIR)

    remotes = read_output(["git", "remote"], cwd=BASE_CLONE_DIR).splitlines()
    if "upstream" not in remotes:
        run(["git", "remote", "add", "upstream", f"https://github.com/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}.git"], cwd=BASE_CLONE_DIR)
    else:
        run(["git", "remote", "set-url", "upstream", f"https://github.com/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}.git"], cwd=BASE_CLONE_DIR)

    run(["git", "fetch", "origin", "--prune"], cwd=BASE_CLONE_DIR)
    run(["git", "fetch", "upstream", "--prune"], cwd=BASE_CLONE_DIR)


def main():
    ensure_repo()

    version = read_version_from_manifest(BASE_CLONE_DIR)
    timestamp = subprocess.check_output(["date", "+%y%m%d%H%M"], text=True).strip()
    branch_name = f"build-{version}-{timestamp}"
    merge_order = "descending (highest -> lowest PR#)"

    run(["git", "checkout", "-B", branch_name, f"upstream/{SOURCE_BASE_BRANCH}"], cwd=BASE_CLONE_DIR)
    source_commit_before_merge = read_output(["git", "rev-parse", "HEAD"], cwd=BASE_CLONE_DIR)

    prs = sorted(fetch_open_prs(), key=lambda pr: pr.get("number", 0), reverse=True)
    merged = []
    failed = []

    for pr in prs:
        number = pr["number"]
        sha = pr["head"]["sha"]
        ref_name = f"pr-{number}"
        try:
            run(["git", "fetch", "upstream", f"pull/{number}/head:{ref_name}"], cwd=BASE_CLONE_DIR)
            run(["git", "merge", "--no-ff", "--no-edit", ref_name], cwd=BASE_CLONE_DIR)
            merged.append({"number": number, "title": pr.get("title", ""), "sha": sha})
        except subprocess.CalledProcessError:
            run(["git", "merge", "--abort"], cwd=BASE_CLONE_DIR)
            failed.append({"number": number, "title": pr.get("title", ""), "sha": sha})

    pushed_to_origin = True
    try:
        run(["git", "push", "-u", "origin", branch_name, "--force"], cwd=BASE_CLONE_DIR)
    except subprocess.CalledProcessError:
        pushed_to_origin = False
        print("Warning: failed to push branch to origin; continuing with local branch")

    REPORT_PATH.mkdir(parents=True, exist_ok=True)
    report_name = f"README-CAD_SketcherPR_{version}-{timestamp}.txt"
    report_file = REPORT_PATH / report_name
    commit_hash = read_output(["git", "rev-parse", "HEAD"], cwd=BASE_CLONE_DIR)

    with report_file.open("w", encoding="utf-8") as f:
        f.write("CAD_SketcherPR Automation Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Version: {version}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Branch: {branch_name}\n")
        f.write(f"Source commit (before PR merging): {source_commit_before_merge}\n")
        f.write(f"Merge order: {merge_order}\n")
        f.write(f"Commit: {commit_hash}\n")
        f.write(f"Source: https://github.com/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}\n")
        f.write(f"Fork: https://github.com/{FORK_OWNER}/{FORK_REPO}\n\n")
        f.write(f"Merged PRs ({len(merged)}):\n")
        for item in merged:
            f.write(f"- #{item['number']}: {item['title']}\n")
        f.write(f"\nFailed PR merges ({len(failed)}):\n")
        for item in failed:
            f.write(f"- #{item['number']}: {item['title']}\n")

    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    state_file = logs_dir / "pr_state.json"
    state = {
        "version": version,
        "timestamp": timestamp,
        "branch": branch_name,
        "source_commit_before_merge": source_commit_before_merge,
        "merge_order": merge_order,
        "total_prs_processed": len(prs),
        "pushed_to_origin": pushed_to_origin,
        "report": str(report_file),
        "merged_prs": merged,
        "failed_prs": failed,
    }
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print(f"Created branch: {branch_name}")
    if not pushed_to_origin:
        print("Branch push status: local only (origin push failed)")
    print(f"Report: {report_file}")


if __name__ == "__main__":
    main()
