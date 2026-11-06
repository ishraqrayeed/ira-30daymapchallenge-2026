#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" != "--final-polish" && "${1:-}" != "--render-only" && "${1:-}" != "--linkedin-only" && "${1:-}" != "--highres-only" && "${1:-}" != "--web-only" ]]; then python3 scripts/download.py; fi
# Discover the installed macOS bundle (allow an explicit QGIS_APP override).
if [[ -z "${QGIS_APP:-}" ]]; then
 for candidate in /Applications/QGIS*.app "$HOME"/Applications/QGIS*.app; do
  if [[ -d "$candidate/Contents/Resources/qgis/python" ]]; then QGIS_APP="$candidate"; break; fi
 done
fi
if [[ -z "${QGIS_APP:-}" ]]; then echo 'QGIS.app not found; set QGIS_APP to its bundle path.' >&2; exit 1; fi
QGIS_PYTHON=''
for candidate in "$QGIS_APP"/Contents/MacOS/python3.*; do
 if [[ -x "$candidate" && ! "$candidate" == *-config ]]; then QGIS_PYTHON="$candidate"; break; fi
done
[[ -n "$QGIS_PYTHON" ]] || { echo 'No bundled QGIS Python found' >&2; exit 1; }
export PYTHONHOME="$QGIS_APP/Contents/Frameworks"
export PYTHONPATH="$QGIS_APP/Contents/Resources/qgis/python"
export QGIS_PREFIX_PATH="$QGIS_APP/Contents/MacOS"
export PROJ_DATA="$QGIS_APP/Contents/Resources/qgis/proj"
export GDAL_DATA="$QGIS_APP/Contents/Resources/qgis/gdal"
export QT_QPA_PLATFORM=offscreen
if [[ "${1:-}" == "--final-polish" ]]; then
 "$QGIS_PYTHON" scripts/final_polish.py
 exit 0
fi
if [[ "${1:-}" == "--linkedin-only" ]]; then
 "$QGIS_PYTHON" scripts/export_linkedin.py
 exit 0
fi
if [[ "${1:-}" == "--highres-only" ]]; then
 "$QGIS_PYTHON" scripts/export_highres.py
 exit 0
fi
if [[ "${1:-}" == "--web-only" ]]; then
 "$QGIS_PYTHON" scripts/export_web.py
 python3 scripts/validate_web.py
 exit 0
fi
"$QGIS_PYTHON" -c 'from qgis.core import Qgis; from osgeo import gdal; print("QGIS",Qgis.QGIS_VERSION,"GDAL",gdal.VersionInfo())'
if [[ "${1:-}" != "--render-only" ]]; then "$QGIS_PYTHON" scripts/prepare.py; fi
"$QGIS_PYTHON" scripts/render.py
"$QGIS_PYTHON" scripts/validate.py
"$QGIS_PYTHON" scripts/export_linkedin.py
"$QGIS_PYTHON" scripts/export_highres.py
"$QGIS_PYTHON" scripts/export_web.py
python3 scripts/validate_web.py
