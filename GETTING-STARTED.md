# Getting started with Plate to Peak

Plate to Peak lives inside Claude. You give it two things — your glucose export
and a short note of what you ate — and it draws you a chart of which meals pushed
your sugar up. Everything runs on your own computer, inside your own Claude.
Nothing is uploaded anywhere.

You set it up once (about five minutes). After that it's just "drop a file and ask."

## What you need

- The **Claude desktop app** (the one with Cowork). If you use Claude in a web
  browser, download the desktop app first.
- Your **glucose data as a CSV file** from Dexcom Clarity. The setup will show you
  how to export it.
- A **meal diary**: literally what you ate and roughly when. A note on your phone
  is fine.

## Step 1 — Add Plate to Peak to Claude (once)

1. Open the Claude desktop app.
2. Go to **Settings**, then find the section for adding plugins or extensions
   (it may be called **Capabilities** or **Connectors**).
3. Choose to **add a plugin from GitHub** (sometimes worded "add a marketplace").
4. Paste this: `sambt94/plate-to-peak`
5. When it appears, click **Install**, then make sure it's switched **on**.

That is the only technical part, and you only ever do it once.

## Step 2 — Set it up (first time)

Start a new chat and type:

> **set up plate to peak**

The first thing Claude offers is a **demo on sample data** — say yes and you'll
see a full chart in about ten seconds, before you've exported anything. It's a
made-up person, so it's also a safe way to show the tool to someone else.

When you're ready for your own data, Claude shows you how to export your glucose
CSV from Dexcom Clarity. Just answer as you go — it's two questions.

## Step 3 — Get your chart

1. Export your glucose CSV from Dexcom Clarity (the setup step shows you where).
2. Drag the CSV into the chat, and paste or attach your meal notes.
3. Type:

   > **map my spikes**

Claude reads your data and draws your chart: your glucose line across the days,
with a dot on each meal. Red dots are meals that pushed you over your target. If
it finds a spike with no meal noted, it asks "did you eat something here?" — answer
if you remember, and it fills the gap in.

## What your meal notes should look like

As simple as this — a date, a rough time, and what you ate:

```
28 June
08:30  porridge with berries
13:00  chicken salad, bread
19:45  salmon, rice, broccoli
```

That is enough to map meals to spikes. More detail is welcome, but do not let
detail stop you writing anything down.

## Your data stays yours

Plate to Peak runs entirely inside your Claude. No account, no server, nothing
uploaded. The name and date of birth in the Dexcom file are ignored — Claude
never reads them back and never puts them on the chart.

## If something does not work

- Tell Claude what you see ("it said it couldn't find a file"). It can usually
  sort it out in the chat.
- Or send Sam a screenshot and he'll get it sorted.
