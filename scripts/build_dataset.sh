#!/bin/bash
# Build data/ from IBTrACS best tracks and the CCAI tutorial features (downloads both).
set -euo pipefail
cd "$(dirname "$0")/.."

run() { python -m nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output-dir runs "$@"; }

run notebooks/01_prepare_storm_data.ipynb
