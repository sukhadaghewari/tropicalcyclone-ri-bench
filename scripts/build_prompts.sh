#!/bin/bash
# Sample the dev and test storms and build every case file in model_inputs/ (seed 42, reproduces the committed files).
set -euo pipefail
cd "$(dirname "$0")/.."

run() { python -m nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output-dir runs "$@"; }

run notebooks/02_make_prompt_files.ipynb                  # RI case files and the dev/test split
run notebooks/05_make_storm_identification_prompts.ipynb  # storm-identification probe
