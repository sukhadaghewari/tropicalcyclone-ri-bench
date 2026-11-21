# Can Multimodal LLMs Predict Rapid Intensification?

Code, data, and results for the paper **"Can Multimodal LLMs Predict Rapid Intensification? A Leakage-Controlled Zero-Shot Benchmark for Tropical Cyclones"** (GeoCV Workshop, WACV 2027).

**Task.** A storm undergoes rapid intensification (RI) if its maximum sustained wind rises by 30 kt or more in the next 24 hours. For each 6-hourly observation, a model sees the storm's history so far and returns an RI probability.

**Benchmark.** 2,485 cases from 140 storms (2016–2025), built from IBTrACS best tracks, ERA5 environmental features, and GridSat-B1 infrared images. Each case has 16 tabular features per past observation and, optionally, the latest eight satellite images. Storm names, dates, latitude, and longitude are removed so that models cannot recognise the storm.

| Set | Seasons | Storms | Cases (RI) | Use |
|---|---|---|---|---|
| Development | 2016 | 40 (20 with RI) | 720 (94) | choose each model's threshold |
| Test | 2017–2025 | 100 (50 with RI) | 1,765 (190) | final evaluation |

**Models.** GPT-5 mini, GPT-5.4 mini, GPT-5.6 Luna, GPT-6 Luna, Claude Haiku 5.5, and Claude Sonnet 5.5, all zero-shot. An XGBoost model trained on 1980–2015 storms is the trained baseline.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt jupyterlab
```

Each notebook also runs in Colab. Its first code cell clones the repo and moves into it.

## Repository layout

```
data/            storm observations with features and RI labels (2016–2025, and 1980–2015 for XGBoost)
prompt/          prompt templates and the feature dictionary
src/prompts.py   builds prompts and case files, and parses model answers
src/make_result_figures.py   draws the result figures into results/figures/
model_inputs/    case files (one prompt per case) and the dev/test split
notebooks/       the full pipeline, numbered in run order
results/         raw model answers, scores, and figures
```

## Reproducing the paper

Every model answer is already in `results/`, so the scores can be rebuilt without any API calls. Run notebooks 08, 10, and 09, then `python src/make_result_figures.py`.

| Step | Notebook | Output |
|---|---|---|
| Build the dataset | `01_prepare_storm_data` | `data/` |
| Sample storms and build prompts | `02_make_prompt_files` | `model_inputs/ri_prediction/`, `model_inputs/splits/` |
| Check the prompts | `03_check_prompt_files` | – |
| Download satellite images | `04_download_satellite_images` | `model_inputs/images/` (about 900 MB, not in git) |
| Build the storm-identification probe | `05_make_storm_identification_prompts` | `model_inputs/storm_identification/` |
| Combine images into one picture per case | `06_combine_satellite_images` | `model_inputs/images/combined/` |
| Query the LLMs | `07a_run_claude`, `07b_run_openai_gpt` | `results/ri_prediction/`, `results/storm_identification/` |
| Score the identification probe | `08_score_storm_identification` | `results/analysis/*/storm_identification_*` |
| Score RI (thresholds on dev, frozen for test) | `09_score_ri_predictions` | `results/analysis/dev/ri_dev_*`, `results/analysis/test/ri_test_*` |
| XGBoost baseline | `10_xgboost_baseline` | `results/ri_prediction/*/ml/` |

Steps 01–06 only need re-running to rebuild the inputs. Notebook 02 reproduces the committed case files exactly (seed 42). Step 07 needs an Anthropic or OpenAI API key.

In notebook 09, set `VERSION` to `"_text_only"` (tabular history) or `"_text_image"` (history plus images). The images-only results are in `results/analysis/test/ri_test_image_only_*`.

## Data sources

- [IBTrACS v04r01](https://www.ncei.noaa.gov/products/international-best-track-archive) best tracks (NOAA NCEI).
- ERA5-derived and satellite-derived features from the [CCAI tropical cyclone RI tutorial dataset](https://github.com/ccai-tropicalcycloneri-tutorial-2026/tropicalcycloneriprediction/releases/tag/dataset_v4) (`dataset_v4`). The XGBoost baseline follows that tutorial's setup.
- [GridSat-B1](https://www.ncei.noaa.gov/products/gridded-geostationary-brightness-temperature) infrared images (NOAA NCEI).
