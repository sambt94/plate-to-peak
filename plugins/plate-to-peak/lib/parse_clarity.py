# ABOUTME: Parses a Dexcom Clarity CSV export into a glucose series + data-gap list.
# ABOUTME: Handles BOM, metadata rows, mmol/mg units, Low/High sentinels; patient info is ignored.
import csv
import json
import sys
from datetime import datetime, timedelta

LOW_MMOL = 2.1   # Dexcom "Low" = below readable range
HIGH_MMOL = 22.2  # Dexcom "High" = above readable range
GAP_MINUTES = 20  # cadence is ~5 min; a longer silence is a hole (warm-up / signal loss)
FMT = "%Y-%m-%dT%H:%M:%S"


def parse_clarity_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise ValueError("Empty file - not a Dexcom Clarity export?")
    header = [h.lower() for h in rows[0]]
    try:
        ts_col = next(i for i, h in enumerate(header) if h.startswith("timestamp"))
        type_col = next(i for i, h in enumerate(header) if "event type" in h)
        glucose_col = next(i for i, h in enumerate(header) if "glucose value" in h)
    except StopIteration:
        raise ValueError("Unrecognised header - not a Dexcom Clarity export?")
    unit = "mg/dL" if "mg/dl" in header[glucose_col] else "mmol/L"

    readings = []
    for row in rows[1:]:
        if len(row) <= max(ts_col, type_col, glucose_col):
            continue
        if row[type_col].strip() != "EGV":
            continue  # metadata (patient info, device, alerts) never enters the output
        ts = row[ts_col].strip()
        val = row[glucose_col].strip()
        if not ts or not val:
            continue
        if val.lower() == "low":
            mmol = LOW_MMOL
        elif val.lower() == "high":
            mmol = HIGH_MMOL
        else:
            try:
                g = float(val)
            except ValueError:
                continue
            mmol = round(g / 18.0, 1) if unit == "mg/dL" else g
        readings.append({"t": ts, "mmol": mmol})

    readings.sort(key=lambda r: r["t"])
    gaps = []
    for a, b in zip(readings, readings[1:]):
        if datetime.strptime(b["t"], FMT) - datetime.strptime(a["t"], FMT) > timedelta(minutes=GAP_MINUTES):
            gaps.append({"start": a["t"], "end": b["t"]})
    return {"unit": unit, "readings": readings, "gaps": gaps}


if __name__ == "__main__":
    print(json.dumps(parse_clarity_csv(sys.argv[1]), indent=1))
