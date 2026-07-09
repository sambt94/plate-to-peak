# ABOUTME: Assembles the chart artifact's data payload from parsed readings + attribution results.
# ABOUTME: Converts ISO timestamps to minutes-from-window-start; the artifact's JS does the rest.
import json
import sys
from datetime import datetime

FMT = "%Y-%m-%dT%H:%M:%S"


def build_payload(parsed, attribution, threshold=7.8):
    readings = parsed["readings"]
    t0 = datetime.strptime(readings[0]["t"], FMT)

    def x(iso):
        return int((datetime.strptime(iso, FMT) - t0).total_seconds() // 60)

    return {
        "startISO": readings[0]["t"],
        "threshold": threshold,
        "series": [{"x": x(r["t"]), "mmol": r["mmol"]} for r in readings],
        "gaps": [{"x1": x(g["start"]), "x2": x(g["end"])} for g in parsed["gaps"]],
        "meals": [
            {
                "x": x(m["time"]), "food": m["food"], "peak": m["peak"], "delta": m["delta"],
                "spiked": m["spiked"], "notableRise": m["notable_rise"], "status": m["status"],
            }
            for m in attribution["meals"]
        ],
        "orphans": [{"x": x(o["time"]), "mmol": o["mmol"]} for o in attribution["orphans"]],
    }


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))  # {"parsed": ..., "attribution": ..., "threshold": 7.8}
    print(json.dumps(build_payload(data["parsed"], data["attribution"],
                                   threshold=data.get("threshold", 7.8)), indent=1))
