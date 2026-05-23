#!/usr/bin/env python3
"""Upload CAD_SketcherPR build artifact to GitHub Releases."""

import glob
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "falken10vdl")
GITHUB_REPO = os.getenv("GITHUB_REPO", "CAD_SketcherPR")
SOURCE_REPO_OWNER = os.getenv("SOURCE_REPO_OWNER", "hlorus")
SOURCE_REPO_NAME = os.getenv("SOURCE_REPO_NAME", "CAD_Sketcher")
BUILD_BASE_DIR = Path(os.getenv("BUILD_BASE_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR-build"))


def headers(content_type=None):
    h = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {GITHUB_TOKEN}",
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def read_state():
    state_file = Path(__file__).resolve().parents[1] / "logs" / "pr_state.json"
    if not state_file.exists():
        raise RuntimeError("Missing state file. Run previous steps first.")
    return json.loads(state_file.read_text(encoding="utf-8"))


def get_or_create_release(tag_name, release_name, body):
    repo_api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    existing = requests.get(f"{repo_api}/releases/tags/{tag_name}", headers=headers(), timeout=30)

    if existing.status_code == 200:
        return existing.json()["id"]
    if existing.status_code not in (404,):
        existing.raise_for_status()

    payload = {
        "tag_name": tag_name,
        "name": release_name,
        "body": body,
        "draft": False,
        "prerelease": True,
    }
    created = requests.post(f"{repo_api}/releases", headers=headers(), json=payload, timeout=30)
    created.raise_for_status()
    return created.json()["id"]


def upload_asset(release_id, asset_path: Path):
    list_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/{release_id}/assets"
    resp = requests.get(list_url, headers=headers(), timeout=30)
    resp.raise_for_status()
    for asset in resp.json():
        if asset["name"] == asset_path.name:
            requests.delete(asset["url"], headers=headers(), timeout=30).raise_for_status()

    upload_url = f"https://uploads.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/{release_id}/assets"
    params = {"name": asset_path.name}
    with asset_path.open("rb") as f:
        up = requests.post(
            upload_url,
            headers=headers("application/zip"),
            params=params,
            data=f,
            timeout=300,
        )
    up.raise_for_status()
    return up.json().get("browser_download_url", "")


def append_report(report_file: Path, lines):
    with report_file.open("a", encoding="utf-8") as f:
        f.write("\n")
        for line in lines:
            f.write(line + "\n")


def format_pr_items(pr_items):
    if not pr_items:
        return "- None"
    lines = []
    for item in pr_items:
        number = item.get("number")
        title = item.get("title", "")
        pr_url = f"https://github.com/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/pull/{number}"
        lines.append(f"- [#{number}]({pr_url}) {title}")
    return "\n".join(lines)


def main():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required")

    state = read_state()
    version = state["version"]
    timestamp = state["timestamp"]
    branch = state["branch"]
    pushed_to_origin = state.get("pushed_to_origin", True)
    merged_prs = state.get("merged_prs", [])
    failed_prs = state.get("failed_prs", [])
    report_file = Path(state["report"])

    dist_dir = BUILD_BASE_DIR / "dist"
    artifacts = sorted(glob.glob(str(dist_dir / "*.zip")))
    if not artifacts:
        raise RuntimeError(f"No ZIP artifacts found in {dist_dir}")

    artifact = Path(artifacts[-1])
    tag_name = f"v{version}-{timestamp}"
    release_name = f"CAD_SketcherPR {version} {timestamp}"

    merged_block = format_pr_items(merged_prs)
    failed_block = format_pr_items(failed_prs)

    body = (
        "Automated CAD_SketcherPR build.\n\n"
        f"- Source branch: {branch}\n"
        f"- Source branch pushed: {'yes' if pushed_to_origin else 'no'}\n"
        f"- Version: {version}\n"
        f"- Timestamp: {timestamp}\n"
        f"- Merged PRs: {len(merged_prs)}\n"
        f"- Failed PR merges: {len(failed_prs)}\n"
        "\n"
        "## Merged PRs\n"
        f"{merged_block}\n"
        "\n"
        "## Failed PR merges\n"
        f"{failed_block}\n"
    )

    release_id = get_or_create_release(tag_name, release_name, body)
    download_url = upload_asset(release_id, artifact)

    append_report(
        report_file,
        [
            "Release Result",
            "--------------",
            f"Release: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/{tag_name}",
            f"Asset: {artifact.name}",
            f"Download URL: {download_url}",
        ],
    )

    print(f"Release tag: {tag_name}")
    print(f"Uploaded: {artifact}")
    print(f"Download: {download_url}")


if __name__ == "__main__":
    main()
