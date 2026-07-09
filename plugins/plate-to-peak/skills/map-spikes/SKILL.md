---
name: map-spikes
description: Turn a Dexcom Clarity CSV export + a meal diary into an interactive meal-to-glucose-spike chart with follow-up questions for unexplained spikes. Trigger phrases: "map my spikes", "make my glucose chart", "what spiked me", "run plate to peak", "analyse my CGM data".
---

Map meals to glucose spikes: parse the CGM export deterministically, parse the
meal diary leniently, attribute spikes with the shipped Python scripts (never by
eyeballing), render the chart artifact, then ask about unexplained spikes.

## Before anything

Read `plate-to-peak.memory.md` in this plugin folder. If the section between
`<!-- setup-start -->` and `<!-- setup-end -->` is empty, run the **setup**
skill first, then come back here.

Use the threshold and units from the setup cache (default 7.8 mmol/L).

## Inputs

1. **Glucose CSV** — a Dexcom Clarity export the user drops into the chat.
2. **Meal diary** — a document or pasted text. The floor per entry: food + rough
   time. See `assets/meal-diary-template.md`.

## Privacy

The CSV's metadata rows carry the person's name and date of birth. The parser
ignores them; never quote them back, never include them in any output. Nothing
leaves this Claude session — no uploads, no external calls.

## Step 1 — Parse the glucose CSV (deterministic)

Run the shipped parser; do not read the CSV yourself:

```
python lib/parse_clarity.py <csv-path> > parsed.json
```

Handles BOM, metadata rows, mmol/L vs mg/dL, `Low`/`High` sentinel values, and
sensor gaps. If it exits with "Unrecognised header", the export is not
Clarity-shaped (LibreView, or a localized Clarity): read the header yourself,
map columns to (timestamp, event type, glucose value), **show the user your
mapping and get a yes** before hand-building the same JSON shape
(`{"unit", "readings": [{"t", "mmol"}], "gaps"}`).

## Step 2 — Parse the meal diary (your job, leniently)

Read the diary. Produce one entry per meal: `{"time": "YYYY-MM-DDTHH:MM:SS", "food": "..."}`.

- Rough times are fine — "around 1pm" → 13:00.
- Relative dates ("Monday") resolve against the CSV's date range.
- An entry with **no placeable time**: set it aside; tell the user which entries
  you could not place and why. Do not guess a time silently.
- Do not invent, merge, or embellish foods. The diary's words are the labels.

## Step 3 — Attribute spikes (deterministic)

Write `{"readings": <from parsed.json>, "meals": <step 2>, "threshold": <from setup>}`
to a file, then:

```
python lib/attribute.py input.json > attribution.json
```

Each meal comes back with `status` (`ok` / `ambiguous` / `insufficient_data`),
`baseline`, `peak`, `delta`, `spiked`, `notable_rise`. For `ambiguous` meals
(two meals share one peak), adjudicate yourself with a stated reason — e.g.
"the 12:30 cake is 20 minutes before the peak, the 11:00 soup 110 minutes; cake
owns it" — and say so in the summary. Never change a `spiked` verdict.

## Step 4 — Orphan spikes: ask, don't guess

`attribution.json` includes `orphans` — spikes with no meal logged before them.
For each, ask the user, one at a time:

> Your glucose hit **{mmol} mmol/L around {time}**, but there's nothing in the
> diary before it. Did you eat or drink something then?

If they answer, append the meal to the step-2 list and **re-run step 3**.
If they don't know, leave it — an honest unexplained spike beats a guessed one.

## Step 5 — Render the artifact

```
python lib/chart_data.py combined.json > payload.json
```

(where combined.json = `{"parsed": ..., "attribution": ..., "threshold": ...}`).
Take `assets/chart-template.jsx`, replace the `DATA` placeholder (marked
`/*__PAYLOAD__*/`) with the payload JSON, and render it as a React artifact.

Then give a short readout, ranked by peak:

- which meals crossed the threshold (red),
- which rose sharply but stayed under (amber),
- the pattern, in one or two sentences, in plain language
  ("white bread at lunch spikes you; the same bread with eggs at breakfast doesn't").

Clinical honesty: name the meals behind real spikes; never blame a meal the data
doesn't support; say plainly when the sensor was silent.
