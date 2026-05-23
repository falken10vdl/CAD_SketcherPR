# CAD_SketcherPR

Automation package to build and publish PR-based CAD Sketcher addon builds.

- Upstream source: https://github.com/hlorus/CAD_Sketcher
- Fork source branch host: https://github.com/falken10vdl/CAD_Sketcher
- Release target repo (configurable): https://github.com/falken10vdl/CAD_SketcherPR

## Installation with automated updates

CAD_SketcherPR publishes a Blender extension repository index so Blender can
check for new releases automatically.

1. Open Blender and go to Edit > Preferences > Get Extensions.
2. Add a remote repository with this URL:

	https://raw.githubusercontent.com/falken10vdl/CAD_SketcherPR/main/index.json

3. Enable "Check for Updates on Startup".
4. Search for CAD_SketcherPR and install it.
5. Disable the stock CAD Sketcher add-on before enabling CAD_SketcherPR.

The current automatic feed publishes the Linux x64 build. If you need a
different platform, install the release ZIP manually.

## Pipeline

1. Sync local automation repo
2. Clone/update fork and merge open upstream PRs
3. Build distributable addon zip
4. Upload artifact to GitHub Releases
5. Refresh index.json for Blender automatic updates

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

## Manual download

If you do not want to use Blender's remote repository support, download the
latest ZIP from the GitHub Releases page and install it from disk in Blender.

## Cron

- Hourly template: `automation/cron/hourly-automation.cron`
- Weekly template: `automation/cron/weekly-automation.cron`

See `automation/README.md` for setup and usage.
