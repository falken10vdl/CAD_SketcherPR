# CAD_SketcherPR

Automation package to build and publish PR-based CAD Sketcher addon builds.

- Upstream source: https://github.com/hlorus/CAD_Sketcher
- Fork source branch host: https://github.com/falken10vdl/CAD_Sketcher
- Release target repo (configurable): https://github.com/falken10vdl/CAD_SketcherPR

## Pipeline

1. Sync local automation repo
2. Clone/update fork and merge open upstream PRs
3. Build distributable addon zip
4. Upload artifact to GitHub Releases

## Naming convention

- Source branch: `build-<version>-<yymmddhhmm>`
- Build artifact: `CAD_SketcherPR_<version>-<yymmddhhmm>.zip`
- Release tag: `v<version>-<yymmddhhmm>`
- Report: `README-CAD_SketcherPR_<version>-<yymmddhhmm>.txt`

Version is read from upstream `blender_manifest.toml`.

## Quick start

```bash
cd automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd src
python3 main.py
```

## Cron

- Hourly template: `automation/cron/hourly-automation.cron`
- Weekly template: `automation/cron/weekly-automation.cron`

See `automation/README.md` for setup and usage.
