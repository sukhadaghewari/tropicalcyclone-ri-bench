#!/bin/bash
# Download GridSat-B1 infrared images for every case and combine them (about 73 GB of downloads, 900 MB kept).
set -euo pipefail
cd "$(dirname "$0")/.."

run() { python -m nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output-dir runs "$@"; }

run notebooks/04_download_satellite_images.ipynb  # storm-centred crops -> model_inputs/images/
run notebooks/06_combine_satellite_images.ipynb   # one 8-frame picture per case
