#!/bin/bash
# Rebuild every table and figure in the paper from the saved model answers in results/ (no API calls).
set -euo pipefail
cd "$(dirname "$0")/.."

run() { python -m nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output-dir runs "$@"; }

run notebooks/08_score_storm_identification.ipynb   # storm-identification probe
run notebooks/10_xgboost_baseline.ipynb             # trained XGBoost baseline
RI_VERSION=_text_only  run notebooks/09_score_ri_predictions.ipynb --output 09_score_ri_predictions_text_only    # tabular input
RI_VERSION=_text_image run notebooks/09_score_ri_predictions.ipynb --output 09_score_ri_predictions_text_image   # tabular + images
python src/make_result_figures.py                   # figures -> results/figures/
