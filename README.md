# Plate to Peak

Map your meals to your glucose spikes. Bring two things — a **Dexcom Clarity
CSV export** and a **meal diary** (what you ate + roughly when) — and Claude
draws you an interactive chart: your glucose curve, your meals as dots, red
where a meal pushed you over your threshold. When it finds a spike with no
meal logged, it asks: *"did you eat something here?"*

Built by [Sam Beattie](https://sambt.dev) with Dr Lelde's metabolic-health
community as first users.

## Privacy

Everything runs inside **your** Claude. No server, no upload, no account.
The Clarity export's name and date-of-birth rows are ignored by the parser
and never appear in any output.

## Install (Claude Cowork)

1. In the left sidebar, click **Connectors**.
2. Click **Manage connectors**.
3. Click **Add a personal plugin**.
4. Choose **Add marketplace from GitHub** and enter: `sambt94/plate-to-peak`
5. Install the **plate-to-peak** plugin from the marketplace.

**In Claude Code:**

```
/plugin marketplace add sambt94/plate-to-peak
/plugin install plate-to-peak@plate-to-peak
```

## Use

First run: say **"set up plate to peak"** — a two-minute wizard covers getting
your CSV out of Clarity, the meal-diary floor (food + rough time), and your
threshold. After that:

1. Export a CSV from [Dexcom Clarity](https://clarity.dexcom.eu) (same login as your phone app).
2. Drop the CSV and your meal diary into the chat.
3. Say **"map my spikes."**

## What it needs from a meal diary

The floor: date, rough time, food name. One line per meal.

```
2026-06-28
08:30  Huel shake
13:00  Chicken salad, bread
19:45  Salmon, rice, broccoli
```

## Roadmap

- Smarter meal logging (nutrition lookup, cookbook integration)
- Activity/sleep overlay (Oura)
- Libre/LibreView first-class support
- Live CGM connection

## Design notes

- **No hosted infrastructure.** Your files + your Claude. The deterministic
  parts (CSV parsing, spike attribution) are shipped Python scripts — Claude
  runs them rather than eyeballing your data.
- **Absolute threshold** (default 7.8 mmol/L) decides "spiked"; the rise from
  baseline (delta) is always shown so a sharp climb that stays under the line
  is visible too.
- **Honest gaps.** Sensor warm-up and signal loss render as gaps, and meals
  falling in them get "no verdict", never a guess.

## License

MIT — see [LICENSE](./LICENSE).
