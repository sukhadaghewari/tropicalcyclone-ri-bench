<task>
You are assisting with a research study on tropical cyclone rapid intensification (RI).

You will receive a picture of satellite images of ONE storm, ordered chronologically from oldest to newest. The last image represents the current time, t. No other information about the storm is given.

Estimate the probability of the following event:

usa_wind(t+24h) - usa_wind(t) >= 30 kt

`usa_wind` is the storm's maximum sustained wind speed, in knots (kt). Only usa_wind at t and exactly t+24h determine whether RI occurs. Reaching an increase of 30 kt or more before t+24h and then weakening below that increase by t+24h does not count as RI. An increase of less than 30 kt, no change, weakening, or storm dissipation before t+24h also means RI does not occur.
</task>

<input_and_time>
`hours_since_start` is the number of hours since the storm's first observation, which always has value 0. Observation spacing can vary, so always use `hours_since_start` to determine elapsed time rather than assuming 6-hour intervals.

The images contain no information after the current time, t.
</input_and_time>

<satellite_picture>
One picture is attached after this text. It shows infrared satellite images of this storm at its most recent observation times, up to and including t.

Layout:
- 8 boxes in 2 rows of 4, read left to right, top row first, oldest first.
- The last box (bottom right) is always the current time, t.
- Under each box is the `hours_since_start` of its observation. Consecutive boxes are usually 6 hours apart; use the labels for the actual times.
- A box labelled "before first observation" is a time before the storm's first observation. A white box with grey hatching that says "no image" has no satellite image.

Each image:
- Infrared brightness temperature (about 11 micrometres) from the GridSat-B1 satellite record, at or just before that observation time.
- Centred on the storm centre at that time, north at the top, about 1,170 km across in both directions.
- Grey scale fixed for every image: white is 190 K (cold, high cloud tops, deep convection) and black is 310 K (warm surface or low cloud). Colder, whiter cloud is higher.
- Magenta pixels have no satellite data.
- Thin straight horizontal or vertical lines or sharp straight edges are satellite data artefacts, not weather; ignore them.

Use the images for the storm's cloud structure and how it changes over time, for example how cold and widespread the cloud tops are near the centre, how organised or symmetric the cloud pattern is, curved banding, and whether an eye is visible. These are general indications, not rules.
</satellite_picture>

<rules>
1. Use only the supplied satellite images. Do not identify the storm or use external knowledge about what a real storm did.

2. Base the estimate mainly on the latest images and the recent trend in cloud structure, and judge whether strengthening is likely through t+24h.

3. Use older images when they help establish meaningful trends, such as changes in cloud-top coldness, organisation or symmetry near the centre.

4. Prefer recent trends over older trends when they conflict, unless the older images provide important context.

5. If only one or two images are available, still estimate the probability and state that the history is short.

6. Do not infer or invent missing images. If missing images materially limit the judgment, mention it in the reason.

7. RI is an uncommon event. Consider both evidence supporting RI and evidence opposing RI before choosing the probability.

8. Do not use web search, retrieval, code execution or any other tools. Answer solely from the supplied images and the knowledge already in your model.
</rules>

<reason_requirements>
The `reason` must:
- be 2 to 4 sentences long;
- identify the most important evidence supporting RI and opposing RI;
- refer to each image it cites by its `hours_since_start` label and describe what is visible;
- when describing a trend across images, name the earlier and the latest label and the elapsed time in hours;
- not treat multiple descriptions of the same trend as separate evidence.
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