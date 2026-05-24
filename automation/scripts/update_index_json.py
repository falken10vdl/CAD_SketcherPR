#!/usr/bin/env python3
"""Update the Blender extension index for CAD_SketcherPR releases."""

import copy
import hashlib
import json
import os
import re
from pathlib import Path

GITHUB_OWNER = os.getenv("GITHUB_OWNER", "falken10vdl")
GITHUB_REPO = os.getenv("GITHUB_REPO", "CAD_SketcherPR")

DEFAULT_ENTRY = {
    "schema_version": "1.0.0",
    "id": "CAD_SketcherPR",
    "name": "CAD Sketcher PR",
    "tagline": "Automatic CAD Sketcher builds with merged pull requests.",
    "version": "0.0.0",
    "type": "add-on",
    "maintainer": "falken10vdl <falken10vdl@gmail.com>",
    "license": ["SPDX:GPL-3.0-or-later"],
    "blender_version_min": "4.0.0",
    "website": "https://github.com/falken10vdl/CAD_SketcherPR",
    "permissions": {
        "files": "Load and save CAD Sketcher projects from disk",
        "network": "Used to check for and download updates",
        "clipboard": "Copy and paste sketcher data",
    },
    "tags": ["3D View", "Development", "Modeling", "Mesh", "Object", "User Interface"],
    "platforms": ["linux-x64", "macos-x64", "macos-arm64", "windows-x64"],
    "python_versions": ["3.11", "3.12", "3.13"],
    "archive_url": "",
    "archive_size": 0,
    "archive_hash": "",
}


def _load_index(index_path: Path):
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"version": "v1", "blocklist": [], "data": [copy.deepcopy(DEFAULT_ENTRY)]}


def _platform_from_name(filename: str) -> str:
    lowered = filename.lower()
    if "linux-x64" in lowered:
        return "linux-x64"
    if "macos-arm64" in lowered or "macosm1" in lowered:
        return "macos-arm64"
    if "macos-x64" in lowered:
        return "macos-x64"
    if "windows-x64" in lowered or "win" in lowered:
        return "windows-x64"
    return "linux-x64"


def _python_version_from_name(filename: str) -> str:
    match = re.search(r"_py(\d+)-", filename)
    if not match:
        return "3.11"
    digits = match.group(1)
    if len(digits) == 3:
        return f"{digits[0]}.{digits[1:]}"
    if len(digits) == 2:
        return f"{digits[0]}.{digits[1]}"
    return digits


def update_index_json(index_path, release_tag, addon_files):
    """Write an extension index file for the supplied release assets."""

    index_path = Path(index_path)
    index = _load_index(index_path)

    assets = []
    for item in addon_files:
        if isinstance(item, tuple):
            local_path, asset_name = item
        else:
            local_path = item
            asset_name = Path(item).name

        local_path = Path(local_path)
        platform = _platform_from_name(asset_name)
        python_version = _python_version_from_name(asset_name)
        size = local_path.stat().st_size
        with local_path.open("rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()

        assets.append(
            {
                "filename": asset_name,
                "platform": platform,
                "python_version": python_version,
                "size": size,
                "hash": digest,
            }
        )

    if not assets:
        return False

    base_entry = index.get("data", [copy.deepcopy(DEFAULT_ENTRY)])[0]
    version_value = release_tag.lstrip("v")

    data = []
    for asset in assets:
        entry = copy.deepcopy(base_entry)
        entry.update(
            {
                "version": version_value,
                "platforms": [asset["platform"]],
                "python_versions": [asset["python_version"]],
                "archive_url": (
                    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/"
                    f"{release_tag}/{asset['filename']}"
                ),
                "archive_size": asset["size"],
                "archive_hash": f"sha256:{asset['hash']}",
            }
        )
        data.append(entry)

    index["version"] = "v1"
    index["blocklist"] = index.get("blocklist", [])
    index["data"] = data

    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return True