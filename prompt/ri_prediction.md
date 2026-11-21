<task>
You are assisting with a research study on tropical cyclone rapid intensification (RI).

You will receive a JSON array of observation objects for ONE storm, ordered chronologically from oldest to newest. The last object represents the current time, t.

Estimate the probability of the following event:

usa_wind(t+24h) - usa_wind(t) >= 30 kt

Only usa_wind at t and exactly t+24h determine whether RI occurs. Reaching an increase of 30 kt or more before t+24h and then weakening below that increase by t+24h does not count as RI. An increase of less than 30 kt, no change, weakening, or storm dissipation before t+24h also means RI does not occur.
</task>

<input_and_time>
Each object contains `hours_since_start` and the meteorological features defined below.

`hours_since_start` is the number of hours since the first observation, which always has value 0. Observation spacing can vary, so always use `hours_since_start` to determine elapsed time rather than assuming 6-hour intervals.

Every value describes conditions at that object's observation time or earlier. The supplied history contains no information after the current time, t.

Each `usa_wind_delta_tminusNh` feature is:

usa_wind at that object's time minus usa_wind exactly N hours earlier.

The earlier measurement used for a delta does not need to appear as another object in the supplied history.

A missing value is represented by JSON `null` or by an absent key. Missing does not mean zero.

A storm history containing only one or two observations is valid and normal.
</input_and_time>

<feature_dictionary>
The JSON below defines the meaning, type, and unit of every meteorological feature. Treat its definitions and units as authoritative; the physical tendencies it mentions are general guidance, not rules.

{{FEATURE_DICTIONARY_JSON}}
</feature_dictionary>

<unit_conventions>
Use the units in the feature dictionary.

Important conversions:
- `usa_wind` and `usa_wind_delta_*`: knots (kt)
- `wind_shear_annulus_ms`: metres per second (m/s)
- 1 m/s = 1.944 kt
- `sea_surface_temp_200km_mean`: kelvin (K), with deg C = K - 273.15
- `sea_level_pressure_200km_mean`: pascals (Pa), with hPa = Pa / 100
- `dist2land`: kilometres (km)
</unit_conventions>

<rules>
1. Use only the supplied storm history and feature definitions. Do not identify the storm or use external knowledge about what a real storm did.

2. Base the estimate mainly on the latest conditions and recent trends. Give substantial weight to `usa_wind` and the available `usa_wind_delta_*` features, and use environmental and structural features to judge whether strengthening is likely to continue through t+24h.

3. Use older observations when they help establish meaningful trends, such as changes in intensity, convection, vertical wind shear, ocean conditions, atmospheric moisture, or proximity to land.

4. Prefer recent trends over older trends when they conflict, unless the older history provides important context.

5. If only one or two observations are available, still estimate the probability and state that the observational history is short.

6. Do not infer or invent missing values. If missing information materially limits the judgment, mention it in the reason.

7. RI is an uncommon event. Consider both evidence supporting RI and evidence opposing RI before choosing the probability.

8. Do not use web search, retrieval, code execution or any other tools. Answer solely from the supplied data and the knowledge already in your model.
</rules>

<reason_requirements>
The `reason` must:
- be 2 to 4 sentences long;
- identify the most important evidence supporting RI and opposing RI;
- mention only features that materially affect the judgment;
- use the exact feature name for every feature mentioned;
- include the value and unit for every non-null feature mentioned;
- when describing a trend across observations, report the earlier value, the latest value, and the elapsed time in hours, determined from hours_since_start;
- not treat multiple representations of the same physical trend as separate evidence;
- not repeat feature definitions.

If a missing feature materially affects the judgment, write it as `feature_name=null`.
</reason_requirements>

<output_format>
Return exactly one valid JSON object and nothing else:

{
  "reason": "...",
  "ri_probability": 0.00
}

Use exactly these two keys in this order.

`ri_probability` must be a JSON number from 0 to 1, not a percentage or quoted string.
</output_format>

<storm_history>
{{HISTORY_JSON}}
</storm_history>
