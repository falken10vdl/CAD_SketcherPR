# CAD_SketcherPR Automation

This package mirrors the bonsaiPR automation flow for CAD Sketcher.

Pipeline:
1. Sync local automation repo (`check_cad_sketcherpr_in_git.py`)
2. Clone/update fork and merge open upstream PRs into a timestamped branch (`00_clone_merge_and_create_branch.py`)
3. Build a distributable addon zip (`01_build_CAD_SketcherPR_addon.py`)
4. Upload release asset to GitHub Releases (`02_upload_to_falken10vdl.py`)

## Repository defaults

- Upstream: `hlorus/CAD_Sketcher`
- Fork: `falken10vdl/CAD_Sketcher`
- Release target: `falken10vdl/CAD_SketcherPR`

## Setup

1. Create directories:

```bash
mkdir -p /home/falken10vdl/CAD_SketcherPRDevel
mkdir -p /home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR/automation/logs
```

2. Install dependencies:

```bash
cd /home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR/automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
# Edit .env and set GITHUB_TOKEN
```

4. Run full pipeline:

```bash
cd /home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR/automation/src
python3 main.py
```

## Outputs

- Source branch in fork:
  - `build-<version>-<yymmddhhmm>`
- Build artifact:
  - `/home/falken10vdl/CAD_SketcherPRDevel/CAD_SketcherPR-build/dist/CAD_SketcherPR_<version>-<yymmddhhmm>.zip`
- Release:
  - `https://github.com/<GITHUB_OWNER>/<GITHUB_REPO>/releases/tag/v<version>-<yymmddhhmm>`
- Report:
  - `/home/falken10vdl/CAD_SketcherPRDevel/README-CAD_SketcherPR_<version>-<yymmddhhmm>.txt`

## Cron

Install one of the templates from `automation/cron/`.

Weekly:

```bash
crontab -e
# paste content from automation/cron/weekly-automation.cron
```

Hourly:

```bash
crontab -e
# paste content from automation/cron/hourly-automation.cron
```

## Notes

- `01_build_CAD_SketcherPR_addon.py` updates `blender_manifest.toml` for PR build branding:
  - `id = "CAD_SketcherPR"`
  - `name = "CAD Sketcher PR"`
- If your release repository does not exist yet, create `falken10vdl/CAD_SketcherPR` first.
