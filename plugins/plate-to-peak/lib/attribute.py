# ABOUTME: Deterministic spike attribution - maps diary meals to glucose peaks in a causal window.
# ABOUTME: Success bar: finger the meals behind real spikes, never falsely blame; small bumps may pass.
import json
import sys
from datetime import datetime, timedelta

FMT = "%Y-%m-%dT%H:%M:%S"
CADENCE_MIN = 5  # expected reading spacing; used to judge window coverage


def _dt(s):
    return datetime.strptime(s, FMT)


def attribute(readings, meals, threshold=7.8, window=(15, 90), delta_notable=2.0):
    rts = [(_dt(r["t"]), r["mmol"]) for r in readings]
    results = []
    expected_points = (window[1] - window[0]) / CADENCE_MIN

    for meal in meals:
        res = dict(meal)
        t = _dt(meal["time"])
        w0, w1 = t + timedelta(minutes=window[0]), t + timedelta(minutes=window[1])
        in_win = [(rt, g) for rt, g in rts if w0 <= rt <= w1]

        if len(in_win) < expected_points / 2:
            res.update(status="insufficient_data", baseline=None, peak=None,
                       peak_time=None, delta=None, spiked=False, notable_rise=False)
            results.append(res)
            continue

        baseline = None
        for lookback in (15, 30):
            before = [(rt, g) for rt, g in rts if t - timedelta(minutes=lookback) <= rt <= t]
            if before:
                baseline = min(before, key=lambda p: abs((p[0] - t).total_seconds()))[1]
                break

        peak_t, peak = max(in_win, key=lambda p: p[1])
        delta = round(peak - baseline, 1) if baseline is not None else None
        spiked = peak >= threshold
        res.update(
            status="ok", baseline=baseline, peak=peak, peak_time=peak_t.strftime(FMT),
            delta=delta, spiked=spiked,
            notable_rise=bool(delta is not None and delta >= delta_notable and not spiked),
        )
        results.append(res)

    # Overlap rule: when one peak reading is claimed by several meals, the meal
    # nearest before the peak owns it; the others are flagged for LLM adjudication.
    claims = {}
    for r in results:
        if r.get("peak_time"):
            claims.setdefault(r["peak_time"], []).append(r)
    for claimants in claims.values():
        if len(claimants) > 1:
            owner = max(claimants, key=lambda r: _dt(r["time"]))
            for r in claimants:
                if r is not owner:
                    r["status"] = "ambiguous"

    return {"meals": results, "orphans": find_orphans(rts, meals, threshold, window)}


def find_orphans(rts, meals, threshold=7.8, window=(15, 90)):
    """Spikes >= threshold with no meal logged in their causal lookback window."""
    meal_times = [_dt(m["time"]) for m in meals]
    orphans = []
    for rt, g in rts:
        if g < threshold:
            continue
        lo, hi = rt - timedelta(minutes=30), rt + timedelta(minutes=30)
        neighbourhood = [g2 for rt2, g2 in rts if lo <= rt2 <= hi]
        if g < max(neighbourhood):
            continue  # not the local maximum
        if any(rt - timedelta(minutes=window[1]) <= mt <= rt - timedelta(minutes=window[0])
               for mt in meal_times):
            continue  # a logged meal explains this peak
        if orphans and rt - _dt(orphans[-1]["time"]) < timedelta(minutes=45):
            continue  # same plateau/event as the previous orphan
        orphans.append({"time": rt.strftime(FMT), "mmol": g})
    return orphans


if __name__ == "__main__":
    payload = json.load(open(sys.argv[1]))  # {"readings": [...], "meals": [...], "threshold": 7.8}
    print(json.dumps(
        attribute(payload["readings"], payload["meals"],
                  threshold=payload.get("threshold", 7.8)),
        indent=1,
    ))
