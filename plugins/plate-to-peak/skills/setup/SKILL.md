---
name: setup
description: First-run wizard for Plate to Peak. Auto-triggered by map-spikes when the setup cache is empty; also on demand. Trigger phrases: "set up plate to peak", "get started with plate to peak", "plate to peak setup".
---

Get a new user from zero to their first meal-to-spike chart. Conversational,
one thing at a time, lenient with input. Writes what you learn to
`plate-to-peak.memory.md` so map-spikes doesn't ask twice.

Open with the privacy stance, one line: everything runs in this Claude —
no server, no upload, and the export's name/date-of-birth rows are ignored.

## 1. Their CGM data

Ask which sensor they wear (Dexcom / Libre / other) and note it.

For Dexcom: log in at **clarity.dexcom.com** (Europe: **clarity.dexcom.eu**)
with the same account as the phone app, and export a CSV for the date range
they want to look at. Then: "drop the CSV here." Help live if they get stuck.

For non-Dexcom sensors: v1 is built for Clarity exports, but a CSV from
LibreView usually works too — map-spikes will confirm the column mapping.

## 2. Their meal diary

Show `${CLAUDE_SKILL_DIR}/../../assets/meal-diary-template.md`. The floor: **food + rough time**, one
line per meal. Ask where they'll keep it (notes app, doc — anywhere they can
paste from). If they already log meals somewhere, that works as-is.

## 3. Threshold and units

Default spike threshold: **7.8 mmol/L**. A clinician may set a different
per-person ceiling — ask only if they mention one. Confirm their Clarity
exports in mmol/L (Europe default) or mg/dL (US) — either is handled.

If they give their threshold in mg/dL (e.g. 140), convert it to mmol/L before
saving: divide by 18, one decimal (140 -> 7.8). The pipeline always works in
mmol/L internally - never write a mg/dL number into threshold_mmol.

## 4. Whose data

One profile per setup: ask whose data this is (a first name is enough).
To analyse someone else's export later, re-run setup.

## Write the cache

Replace everything between `<!-- setup-start -->` and `<!-- setup-end -->` in
the cache file at `${CLAUDE_SKILL_DIR}/../../plate-to-peak.memory.md`:

```markdown
<!-- setup-start -->
profile: Anna
sensor: Dexcom ONE+
clarity_region: eu
threshold_mmol: 7.8
units: mmol/L
diary_home: Apple Notes
<!-- setup-end -->
```

Confirm what you captured in one short list, then offer: "Drop your CSV and
diary here whenever you're ready and say **map my spikes**."
