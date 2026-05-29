#!/usr/bin/env python3
"""Clean up old GitHub releases and local artifacts, keeping only the last 10."""

import os
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "falken10vdl")
GITHUB_REPO = os.getenv("GITHUB_REPO", "CAD_SketcherPR")
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
REPORT_DIR = Path(os.getenv("REPORT_PATH", "/home/falken10vdl/CAD_SketcherPRDevel"))
MAX_RELEASES = 10
MAX_LOGS = 10
MAX_REPORTS = 10


def headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {GITHUB_TOKEN}",
    }


def get_releases():
    """Fetch all releases sorted by creation date (newest first)."""
    repo_api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    releases = []
    page = 1
    
    while True:
        resp = requests.get(
            f"{repo_api}/releases",
            headers=headers(),
            params={"per_page": 100, "page": page},
            timeout=30
        )
        resp.raise_for_status()
        page_data = resp.json()
        if not page_data:
            break
        releases.extend(page_data)
        page += 1
    
    return releases


def delete_release(release_id):
    """Delete a release by ID."""
    repo_api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    resp = requests.delete(
        f"{repo_api}/releases/{release_id}",
        headers=headers(),
        timeout=30
    )
    resp.raise_for_status()


def delete_tag(tag_name):
    """Delete a git tag ref by tag name."""
    repo_api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    encoded_tag = quote(tag_name, safe="")
    resp = requests.delete(
        f"{repo_api}/git/refs/tags/{encoded_tag}",
        headers=headers(),
        timeout=30,
    )
    if resp.status_code != 404:
        resp.raise_for_status()


def cleanup_old_logs():
    """Delete old log files, keeping only the last 10."""
    if not LOGS_DIR.exists():
        print(f"Logs directory does not exist: {LOGS_DIR}")
        return

    patterns = [
        "cron_hourly_*.log",
        "cron_weekly_*.log",
        "check_build_*.log",
        "automation_*.log",
    ]
    log_files = []
    for pattern in patterns:
        log_files.extend(LOGS_DIR.glob(pattern))

    log_files = sorted(set(log_files), key=lambda p: p.stat().st_mtime, reverse=True)

    if len(log_files) <= MAX_LOGS:
        print(f"Only {len(log_files)} log files found. No cleanup needed. (max: {MAX_LOGS})")
        return

    to_delete = log_files[MAX_LOGS:]
    print(
        f"Found {len(log_files)} log files. Deleting {len(to_delete)} old logs (keeping last {MAX_LOGS})..."
    )

    for log_file in to_delete:
        try:
            log_file.unlink()
            print(f"  Deleted: {log_file.name}")
        except Exception as e:
            print(f"  Failed to delete {log_file.name}: {e}")


def cleanup_old_reports():
    """Delete old README report files, keeping only the last 10."""
    if not REPORT_DIR.exists():
        print(f"Report directory does not exist: {REPORT_DIR}")
        return

    report_files = sorted(
        REPORT_DIR.glob("README-CAD_SketcherPR_*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if len(report_files) <= MAX_REPORTS:
        print(
            f"Only {len(report_files)} report files found. No cleanup needed. (max: {MAX_REPORTS})"
        )
        return

    to_delete = report_files[MAX_REPORTS:]
    print(
        f"Found {len(report_files)} report files. Deleting {len(to_delete)} old reports (keeping last {MAX_REPORTS})..."
    )

    for report_file in to_delete:
        try:
            report_file.unlink()
            print(f"  Deleted: {report_file.name}")
        except Exception as e:
            print(f"  Failed to delete {report_file.name}: {e}")


def main():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required")

    releases = get_releases()
    
    if len(releases) <= MAX_RELEASES:
        print(f"Only {len(releases)} releases found. No cleanup needed. (max: {MAX_RELEASES})")
    else:
        to_delete = releases[MAX_RELEASES:]
        print(f"Found {len(releases)} releases. Deleting {len(to_delete)} old releases (keeping last {MAX_RELEASES})...")
        
        for release in to_delete:
            tag = release.get("tag_name", "unknown")
            release_id = release["id"]
            try:
                delete_release(release_id)
                if tag != "unknown":
                    delete_tag(tag)
                print(f"  Deleted: {tag}")
            except Exception as e:
                print(f"  Failed to delete {tag}: {e}")
    
    print()
    cleanup_old_logs()
    print()
    cleanup_old_reports()


if __name__ == "__main__":
    main()
