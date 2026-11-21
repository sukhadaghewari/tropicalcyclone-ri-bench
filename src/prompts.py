"""Build rapid-intensification prompts: one prompt per storm observation, with the history growing over time.

Also builds the storm-identification probe (can a model name the storm from its history?).
Shared by all the notebooks: prompt building, case files, results files and answer parsers.
Import with `from prompts import ...` (src/ must be on sys.path).
"""
import gzip
import io
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent   # repo root (this file is in src/)
PROMPT_DIR = ROOT / "prompt"
INPUTS_DIR = ROOT / "model_inputs"                      # case files, and images/ beside them

FEATURES = ["usa_wind", "usa_sshs", "dist2land", "usa_wind_delta_tminus6h", "usa_wind_delta_tminus12h", "usa_wind_delta_tminus24h", "sea_surface_temp_200km_mean", "sea_level_pressure_200km_mean", "column_water_vapour_200km_mean", "wind_east_200hPa_annulus_mean", "wind_north_200hPa_annulus_mean", "wind_east_850hPa_annulus_mean", "wind_north_850hPa_annulus_mean", "wind_shear_annulus_ms", "cold_cloud_fraction_100km", "cold_cloud_fraction_200km"]
TARGET = "ri_tplus24"

# Never shown to the model: with the track's position, LLMs can recognise the storm and recall what it did.
HIDDEN_LOCATION_FEATURES = ["lat", "lon", "abs_lat"]
assert not set(HIDDEN_LOCATION_FEATURES) & set(FEATURES), "location features must not be in FEATURES"

# Satellite image crops at time t (made by notebooks/04_download_satellite_images.ipynb).
IMAGE_CROPS = ["core", "mid", "wide"]


def image_relpath(case_id, crop):
    """Where a case's image lives, relative to the model_inputs folder: images/<crop>/<case_id>_<crop>.png.

    The case files always hold these paths. Whether an image was actually made (and how much data it is
    missing) is recorded only in model_inputs/images/manifest.csv, keyed by case_id.
    """
    return f"images/{crop}/{case_id}_{crop}.png"


TEMPLATE = (PROMPT_DIR / "ri_prediction.md").read_text()
FEATURE_DICT_TEXT = (PROMPT_DIR / "features.json").read_text().strip()
FEATURE_DICT = json.loads(FEATURE_DICT_TEXT)

# The dictionary must describe exactly the features sent, in the same order.
assert list(FEATURE_DICT) == FEATURES, "features.json does not match FEATURES"

# RI with satellite pictures (notebook 06's combined picture, sent after the prompt text): the RI prompt plus a
# description of the picture ("text_image").
IMAGE_TEMPLATES = {
    "text_image": (PROMPT_DIR / "ri_prediction_text_image.md").read_text(),
}

# Storm-identification probe: its own template, and descriptions of the location features (used only there).
IDENTIFY_TEMPLATE = (PROMPT_DIR / "storm_identification.md").read_text()
LOCATION_DICT = json.loads((PROMPT_DIR / "location_features.json").read_text())
assert list(LOCATION_DICT) == HIDDEN_LOCATION_FEATURES, "location_features.json does not match HIDDEN_LOCATION_FEATURES"

# The two probe versions: the RI prompt's features, without and with location (inserted after dist2land).
IDENTIFY_VARIANTS = {
    "no_location": FEATURES,
    "with_location": FEATURES[:3] + HIDDEN_LOCATION_FEATURES + FEATURES[3:],
}


def prepare_storm(df, sid):
    """Return one storm's rows in time order with obs_index and hours_since_start columns."""
    storm = df[df["sid"] == sid].copy()
    storm["_t"] = pd.to_datetime(storm["iso_time"])
    storm = storm.sort_values("_t").reset_index(drop=True)
    assert storm["_t"].is_unique, f"duplicate times in storm {sid}"
    storm["obs_index"] = range(len(storm))
    storm["hours_since_start"] = (storm["_t"] - storm["_t"].iloc[0]).dt.total_seconds() / 3600
    return storm.drop(columns="_t")


def _clean(value):
    """Convert one cell to a JSON-ready value: missing -> None, floats rounded to 6 significant digits."""
    if pd.isna(value):
        return None
    if isinstance(value, (bool, str)):
        return value
    number = float(f"{float(value):.6g}")
    return int(number) if number.is_integer() else number


def history_to_json(history, features=FEATURES):
    """Render the storm history as a JSON array with one record (key-value object) per line."""
    keys = ["hours_since_start"] + features
    lines = [json.dumps({k: _clean(row[k]) for k in keys}) for _, row in history[keys].iterrows()]
    return "[\n" + ",\n".join(lines) + "\n]"


def build_prompt(history):
    """history: the storm's rows up to and including the current time (output of prepare_storm, sliced)."""
    prompt = (TEMPLATE
              .replace("{{FEATURE_DICTIONARY_JSON}}", FEATURE_DICT_TEXT)
              .replace("{{HISTORY_JSON}}", history_to_json(history)))
    assert "{{" not in prompt, "unfilled placeholder left in prompt"
    return prompt


def prompt_for_row(df_eval, i):
    """Prompt and true label for row i of df_eval: the storm's history from its first observation up to row i."""
    row = df_eval.loc[i]
    history = df_eval.loc[i - row["obs_index"] : i]
    assert (history["sid"] == row["sid"]).all() and len(history) == row["obs_index"] + 1
    return build_prompt(history), int(row[TARGET])


def iter_prompts(df_eval):
    """Yield (row_index, prompt, label) for every row of df_eval, building each prompt only when requested."""
    for i in df_eval.index:
        prompt, label = prompt_for_row(df_eval, i)
        yield i, prompt, label


def case_id(row):
    """Unique key of one observation: storm ID + 3-digit observation number, e.g. 2016240N13224_007."""
    return f"{row['sid']}_{int(row['obs_index']):03d}"


def case_record(df_eval, i, split):
    """One case (row i of df_eval): metadata, true label, image paths and the prompt.

    The metadata (sid, name, season, basin, iso_time) is for bookkeeping only; it never appears in a prompt.
    """
    row = df_eval.loc[i]
    record = {
        "case_id": case_id(row),
        "split": split,
        "sid": row["sid"],
        "name": row["name"],
        "season": int(row["season"]),
        "basin": row["basin"],
        "iso_time": row["iso_time"],
        "obs_index": int(row["obs_index"]),
        "hours_since_start": _clean(row["hours_since_start"]),
        "storm_group": row["storm_group"],
        TARGET: int(row[TARGET]),
    }
    for crop in IMAGE_CROPS:
        record[f"image_t_{crop}"] = image_relpath(record["case_id"], crop)
    record["prompt"], _ = prompt_for_row(df_eval, i)
    return record


def write_records(records, path):
    """Write records (dicts) to path as JSON Lines. A path ending in .gz is written compressed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as raw:
        # mtime=0 keeps the compressed bytes identical between runs, so git only sees real changes.
        binary = gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) if path.suffix == ".gz" else raw
        with io.TextIOWrapper(binary, encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def read_records(path):
    """Read a JSON Lines file (compressed or not) back into a list of dicts, exactly as written."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def write_cases(df_eval, path, split):
    """Write every case of df_eval to path as JSON Lines. A path ending in .gz is written compressed."""
    return write_records((case_record(df_eval, i, split) for i in df_eval.index), path)


def build_image_prompt(history, variant):
    """RI prompt to send with the case's combined picture: "text_image" (history + picture)."""
    prompt = (IMAGE_TEMPLATES[variant]
              .replace("{{FEATURE_DICTIONARY_JSON}}", FEATURE_DICT_TEXT)
              .replace("{{HISTORY_JSON}}", history_to_json(history)))
    assert "{{" not in prompt, "unfilled placeholder left in prompt"
    return prompt


def image_case_record(df_eval, i, split, variant):
    """One case for an image variant: the RI case record, with the variant's prompt and the picture to send.

    `image` is the combined picture's path relative to the model_inputs folder (images/combined/<case_id>_combined.png).
    """
    record = case_record(df_eval, i, split)
    row = df_eval.loc[i]
    history = df_eval.loc[i - row["obs_index"] : i]
    record["prompt_variant"] = variant
    record["image"] = image_relpath(record["case_id"], "combined")
    record["prompt"] = build_image_prompt(history, variant)
    return record


def write_image_cases(df_eval, path, split, variant):
    """Write every case of df_eval for one image variant to path as JSON Lines (.gz: compressed)."""
    return write_records((image_case_record(df_eval, i, split, variant) for i in df_eval.index), path)


def build_identify_prompt(history, variant):
    """Storm-identification prompt for the history; variant is "no_location" or "with_location"."""
    features = IDENTIFY_VARIANTS[variant]
    dictionary = {f: {**FEATURE_DICT, **LOCATION_DICT}[f] for f in features}
    prompt = (IDENTIFY_TEMPLATE
              .replace("{{FEATURE_DICTIONARY_JSON}}", json.dumps(dictionary, indent=2, ensure_ascii=False))
              .replace("{{HISTORY_JSON}}", history_to_json(history, features)))
    assert "{{" not in prompt, "unfilled placeholder left in prompt"
    return prompt


def identify_case_record(df_eval, i, split, variant):
    """One probe case (row i of df_eval): the case's key and metadata (the true answer) and its prompt."""
    row = df_eval.loc[i]
    history = df_eval.loc[i - row["obs_index"] : i]
    assert (history["sid"] == row["sid"]).all() and len(history) == row["obs_index"] + 1
    return {
        "case_id": case_id(row),
        "split": split,
        "probe": f"identify_{variant}",
        "sid": row["sid"],
        "name": row["name"],
        "season": int(row["season"]),
        "basin": row["basin"],
        "iso_time": row["iso_time"],
        "obs_index": int(row["obs_index"]),
        "hours_since_start": _clean(row["hours_since_start"]),
        "storm_group": row["storm_group"],
        "prompt": build_identify_prompt(history, variant),
    }


def write_identify_cases(df_eval, path, split, variant):
    """Write every probe case of df_eval to path as JSON Lines. A path ending in .gz is written compressed."""
    return write_records((identify_case_record(df_eval, i, split, variant) for i in df_eval.index), path)


def _first_json_object(text):
    """The first JSON object in text, ignoring anything around it. Raises ValueError if there is none."""
    for match in re.finditer(r"\{", text):
        try:
            candidate, _ = json.JSONDecoder().raw_decode(text, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    raise ValueError("no JSON object found")


BASIN_CODES = {"NA", "EP", "WP", "NI", "SI", "SP", "SA"}
# Storm-type words some models put before the name ("TROPICAL STORM SONIA"); removed so the name alone is compared.
NAME_PREFIXES = sorted(["SUPER TYPHOON", "SUPER CYCLONE", "SUPER CYCLONIC STORM", "EXTREMELY SEVERE CYCLONIC STORM",
                        "VERY SEVERE CYCLONIC STORM", "SEVERE CYCLONIC STORM", "CYCLONIC STORM", "SEVERE TROPICAL CYCLONE",
                        "TROPICAL CYCLONE", "TROPICAL STORM", "TROPICAL DEPRESSION", "HURRICANE", "TYPHOON", "CYCLONE"],
                       key=len, reverse=True)                    # longest first, so the whole prefix is removed


def name_key(name):
    """A storm name for comparison: upper case, without hyphens or spaces ("Kong-rey" == "KONG REY")."""
    return str(name).upper().replace("-", "").replace(" ", "")


def parse_identify_response(text):
    """Parse a storm-identification answer and check it obeys the output rules. Raises ValueError if not."""
    out = _first_json_object(text)
    if out.get("basin") == "CP":           # the prompt counts the Central Pacific as part of EP
        out["basin"] = "EP"
    if set(out) != {"storm_name", "season", "basin", "confidence", "reason"}:
        raise ValueError(f"unexpected keys: {list(out)}")
    name, season, basin, conf, reason = (out[k] for k in ["storm_name", "season", "basin", "confidence", "reason"])
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"bad storm_name: {name!r}")
    if season is not None and (isinstance(season, bool) or not isinstance(season, int)):
        raise ValueError(f"bad season: {season!r}")
    if basin not in BASIN_CODES | {"unknown"}:
        raise ValueError(f"bad basin: {basin!r}")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        raise ValueError(f"bad confidence: {conf!r}")
    if not isinstance(reason, str):
        raise ValueError(f"bad reason: {reason!r}")
    name = name.strip().upper()
    for prefix in NAME_PREFIXES:
        if name.startswith(prefix + " ") and len(name) > len(prefix) + 1:
            name = name[len(prefix) + 1:].strip()
            break
    return {"storm_name": "unknown" if name == "UNKNOWN" else name,
            "season": season, "basin": basin, "confidence": conf, "reason": reason}


def parse_response(text):
    """Parse the model's JSON answer and check it obeys the output rules. Raises ValueError if not.

    Reads the first JSON object in the text (any text around it is ignored) and accepts its two keys in either order.
    """
    out = _first_json_object(text)
    if set(out) != {"reason", "ri_probability"}:
        raise ValueError(f"unexpected keys: {list(out)}")
    if not isinstance(out["reason"], str):
        raise ValueError(f"bad reason: {out['reason']!r}")
    p = out["ri_probability"]
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 <= p <= 1:
        raise ValueError(f"bad ri_probability: {p!r}")
    return {"reason": out["reason"], "ri_probability": p}


def response_text(response):
    """The answer text of one saved API reply: an OpenAI chat completion or an Anthropic message (thinking skipped)."""
    if "choices" in response:
        return response["choices"][0]["message"]["content"] or ""
    return "".join(block["text"] for block in response["content"] if block["type"] == "text")


def read_answers(path, parse):
    """Read a results file (one {"case_id", "response"} per line, .jsonl.gz or .jsonl) and parse every answer.

    Returns a DataFrame with case_id, model, parse_ok, parse_error and the parsed fields (missing when unparseable).
    """
    rows = []
    for record in read_records(path):
        row = {"case_id": record["case_id"], "model": record["response"]["model"]}
        try:
            row.update(parse(response_text(record["response"])))
            row["parse_ok"], row["parse_error"] = True, None
        except ValueError as err:
            row["parse_ok"], row["parse_error"] = False, str(err)
        rows.append(row)
    answers = pd.DataFrame(rows)
    assert answers["case_id"].is_unique, f"{path}: a case_id appears twice"
    return answers
