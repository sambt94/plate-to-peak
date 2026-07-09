---
name: setup
description: First-run wizard for Plate to Peak. Auto-triggered by map-spikes when the setup cache is empty; also on demand. Trigger phrases: "set up plate to peak", "get started with plate to peak", "plate to peak setup", "run plate to peak" (first time).
---

Get a new user to their first meal-to-spike chart. Conversational, one thing at
a time, lenient with input. Short: this wizard is TWO questions for most people.

Open with the privacy stance, one line: everything runs in this Claude —
no server, no upload, and the export's name/date-of-birth rows are ignored.

Resolve the plugin root first (same rule as map-spikes): in Claude Code,
`${CLAUDE_SKILL_DIR}/../..`; if that doesn't expand in your shell, find it once
with `find / -name "parse_clarity.py" -path "*plate-to-peak*" 2>/dev/null | head -1`
and take that file's grandparent directory. Call it `$ROOT`.

## Question 1 — Demo or their own data?

> Want to **see it work on sample data first** (ten seconds, nothing needed from
> you), or jump straight in with **your own glucose export**?

**If demo:** skip everything below. Hand the map-spikes skill the shipped demo
inputs — CSV `$ROOT/assets/demo/demo-clarity-export.csv`, diary
`$ROOT/assets/demo/demo-meal-diary.md`, threshold 7.8 — and run it end to end,
follow-up questions included (the demo has one unexplained spike; its diary note
explains it as a gym session, so use it to show how the "did you eat something
here?" loop works). Afterwards, offer: "That's the demo. Ready to try your own
export?" and come back here.

**If their own data:** carry on.

## Question 2 — Their glucose export

Plate to Peak works with **Dexcom Clarity CSV exports** (other sensors are on
the roadmap — don't offer them). Walk them through getting one, gently:

> Log in at **clarity.dexcom.com** (Europe: **clarity.dexcom.eu**) with the same
> account as your Dexcom phone app, and export a CSV for the date range you want
> to look at. Then drop the file here.

Help live if they get stuck. Both mmol/L and mg/dL exports are handled
automatically — no need to ask about units.

## Only if it comes up (don't ask proactively)

- **Threshold:** default **7.8 mmol/L**. If a clinician sets a different
  per-person ceiling, use theirs. If they give it in mg/dL (e.g. 140), convert:
  divide by 18, one decimal (140 -> 7.8). The pipeline always works in mmol/L —
  never store a mg/dL number as the threshold.
- **Meal diary:** if they ask what to log, show
  `$ROOT/assets/meal-diary-template.md`. The floor: food + rough time, one line
  per meal. Anywhere they can paste from is fine.
- **Whose data:** if they mention analysing someone else's export (a clinician
  running a client's data), just note the first name with the results. One
  person per run.

## Save the settings

Try to write what you learned between the `<!-- setup-start -->` and
`<!-- setup-end -->` markers in `$ROOT/plate-to-peak.memory.md`:

```markdown
<!-- setup-start -->
profile: Anna
threshold_mmol: 7.8
clarity_region: eu
<!-- setup-end -->
```

If the plugin folder is read-only in this environment, don't fight it: keep the
settings in the conversation and carry on. The wizard is two questions — asking
again next session costs nothing.

Close with: "Drop your CSV and meal notes here whenever you're ready and say
**map my spikes**."
