#!/usr/bin/env python3
"""
check_pr_changes.py - PR change detection for CAD_SketcherPR automation.

Exit codes:
- 0: changes detected (run build)
- 1: no changes detected (skip build)
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
SOURCE_REPO_OWNER = os.getenv("SOURCE_REPO_OWNER", "hlorus")
SOURCE_REPO_NAME = os.getenv("SOURCE_REPO_NAME", "CAD_Sketcher")
MAX_PRS_TO_MERGE = int(os.getenv("MAX_PRS_TO_MERGE", "100"))

RAW_EXCLUDED = os.getenv("EXCLUDED", "")
EXCLUDED_PRS = {
    int(x.strip()) for x in RAW_EXCLUDED.split(",") if x.strip().isdigit()
}

RAW_USERNAMES = os.getenv("USERNAMES", "")
USERS = [u.strip() for u in RAW_USERNAMES.split(",") if u.strip()]

STATE_FILE = Path(__file__).resolve().parents[1] / "logs" / "pr_check_state.json"
UPSTREAM_REPO = f"{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}"


def github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def fetch_open_prs():
    url = f"https://api.github.com/repos/{UPSTREAM_REPO}/pulls"
    all_prs = []
    page = 1

    while True:
        resp = requests.get(
            url,
            headers=github_headers(),
            params={"state": "open", "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()

        prs = resp.json()
        if not prs:
            break

        if USERS:
            prs = [pr for pr in prs if pr.get("user", {}).get("login") in USERS]

        all_prs.extend(prs)

        if len(prs) < 100:
            break
        page += 1

    return all_prs[:MAX_PRS_TO_MERGE]


def normalize_prs(prs):
    normalized = []

    for pr in prs:
        number = pr.get("number")
        if number in EXCLUDED_PRS:
            continue

        head = pr.get("head") or {}
        if not head.get("repo"):
            continue

        normalized.append(
            {
                "number": number,
                "updated_at": pr.get("updated_at"),
                "draft": bool(pr.get("draft", False)),
                "head_sha": head.get("sha"),
                "state": pr.get("state"),
            }
        )

    normalized.sort(key=lambda x: x["number"])
    return normalized


def calculate_state_hash(normalized_prs):
    state_str = json.dumps(normalized_prs, sort_keys=True)
    return hashlib.sha256(state_str.encode()).hexdigest()


def load_previous_state():
    if not STATE_FILE.exists():
        return None

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Warning: failed to parse previous state: {exc}")
        return None


def save_state(state_hash, pr_count):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "hash": state_hash,
        "pr_count": pr_count,
        "checked_at": datetime.now().isoformat(),
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main():
    print("=" * 60)
    print("CAD_SketcherPR Change Detection")
    print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    prs = fetch_open_prs()
    normalized = normalize_prs(prs)
    state_hash = calculate_state_hash(normalized)

    print(f"Current relevant PRs: {len(normalized)}")

    previous = load_previous_state()
    if previous is None:
        print("No previous state found, initial build required")
        save_state(state_hash, len(normalized))
        return 0

    prev_hash = previous.get("hash")
    prev_count = int(previous.get("pr_count", 0))
    prev_checked = previous.get("checked_at", "unknown")

    print(f"Previous check: {prev_checked}")
    print(f"Previous relevant PRs: {prev_count}")

    if state_hash != prev_hash:
        print("Changes detected: build required")
        if len(normalized) != prev_count:
            delta = len(normalized) - prev_count
            if delta > 0:
                print(f"PR delta: +{delta}")
            else:
                print(f"PR delta: {delta}")
        else:
            print("PR metadata/content updated")

        save_state(state_hash, len(normalized))
        return 0

    print("No changes detected: build not required")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
