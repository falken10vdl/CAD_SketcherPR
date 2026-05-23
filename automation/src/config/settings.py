import os
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "falken10vdl")
GITHUB_REPO = os.getenv("GITHUB_REPO", "CAD_SketcherPR")

FORK_OWNER = os.getenv("FORK_OWNER", "falken10vdl")
FORK_REPO = os.getenv("FORK_REPO", "CAD_Sketcher")
SOURCE_REPO_OWNER = os.getenv("SOURCE_REPO_OWNER", "hlorus")
SOURCE_REPO_NAME = os.getenv("SOURCE_REPO_NAME", "CAD_Sketcher")
SOURCE_BASE_BRANCH = os.getenv("SOURCE_BASE_BRANCH", "main")

BASE_CLONE_DIR = os.getenv("BASE_CLONE_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/CAD_Sketcher")
BUILD_BASE_DIR = os.getenv("BUILD_BASE_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR-build")
REPORT_PATH = os.getenv("REPORT_PATH", "/home/falken10vdl/CAD_SketcherPRDevel")
WORKING_DIR = os.getenv("WORKING_DIR", "/home/falken10vdl/CAD_SketcherPRDevel/MergingPR")

MAX_PRS_TO_MERGE = int(os.getenv("MAX_PRS_TO_MERGE", "100"))
KEEP_RELEASES = int(os.getenv("KEEP_RELEASES", "10"))


def ts_compact() -> str:
    return datetime.now().strftime("%y%m%d%H%M")


def report_filename(version: str, timestamp: str) -> str:
    return f"README-CAD_SketcherPR_{version}-{timestamp}.txt"


def branch_name(version: str, timestamp: str) -> str:
    return f"build-{version}-{timestamp}"


def tag_name(version: str, timestamp: str) -> str:
    return f"v{version}-{timestamp}"
