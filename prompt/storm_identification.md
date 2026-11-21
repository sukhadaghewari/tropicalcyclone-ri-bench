<task>
You are assisting with a research study on tropical cyclones.

You will receive a JSON array of observation objects for ONE real, historical tropical cyclone, ordered chronologically from oldest to newest. The last object is the most recent observation available.

Identify the storm: give its official name, its season and its basin, as far as you can tell from the supplied data.
</task>

<input_and_time>
Each object contains `hours_since_start` and the meteorological features defined below.

`hours_since_start` is the number of hours since the first observation, which always has value 0. It is not a calendar date. Observation spacing can vary, so use `hours_since_start` to determine elapsed time.

Each `usa_wind_delta_tminusNh` feature is usa_wind at that object's time minus usa_wind exactly N hours earlier.

A missing value is represented by JSON `null`. Missing does not mean zero.
</input_and_time>

<feature_dictionary>
The JSON below defines the meaning, type, and unit of every feature.

{{FEATURE_DICTIONARY_JSON}}
</feature_dictionary>

<rules>
1. Do not use web search, retrieval, code execution or any other tools. Answer solely from the supplied data and the knowledge already in your model.

2. If you cannot identify the storm, say so: use "unknown" rather than guessing. A confident wrong answer is worse than "unknown".

3. Storm names are reused across years and basins, so the name alone is not enough; give the season and basin too.

4. The season is the year of the storm's tropical cyclone season. In the Northern Hemisphere this is the calendar year. In the Southern Hemisphere the season runs from July to June and is labelled by the year in which it ends (for example, a storm in December 2015 belongs to season 2016).

5. Some storms never received a name. If you believe the storm was unnamed, use "UNNAMED" as its name.
</rules>

<output_format>
Return exactly one valid JSON object and nothing else:

{
  "storm_name": "...",
  "season": 2000,
  "basin": "...",
  "confidence": 0.00,
  "reason": "..."
}

- `storm_name`: the official name in capital letters, "UNNAMED", or "unknown".
- `season`: the season as a JSON integer, or `null` if unknown.
- `basin`: the basin the storm is in at the last observation: one of "NA" (North Atlantic), "EP" (Eastern and Central North Pacific, east of 180°), "WP" (Western North Pacific), "NI" (North Indian), "SI" (South Indian), "SP" (South Pacific), "SA" (South Atlantic), or "unknown".
- `confidence`: your probability, from 0 to 1, that both `storm_name` and `season` are correct. Use 0 when `storm_name` is "unknown".
- `reason`: one or two sentences on what in the data led to your answer.
</output_format>

<storm_history>
{{HISTORY_JSON}}
</storm_history>
