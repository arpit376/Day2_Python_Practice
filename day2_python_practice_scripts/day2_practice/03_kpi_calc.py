"""Exercise 3 - Turn parsed events into KPIs (success rate, mean, p95)."""
import math, re, statistics
from datetime import datetime
from pathlib import Path

PAT = re.compile(r"^(\S+ \S+) \[MME\] NAS Attach (Request|Complete|Reject) imsi=(\d+)")
FMT = "%Y-%m-%d %H:%M:%S.%f"
started, setup_ms, ok, fail = {}, [], 0, 0

for line in Path("sample_mme.log").read_text().splitlines():
    m = PAT.match(line)
    if not m:
        continue
    ts, msg, imsi = datetime.strptime(m[1], FMT), m[2], m[3]
    if msg == "Request":
        started[imsi] = ts
    elif msg == "Complete":
        ok += 1
        setup_ms.append((ts - started[imsi]).total_seconds() * 1000)
    else:
        fail += 1

attempts = ok + fail
print(f"Attach success rate: {ok}/{attempts} = {100 * ok / attempts:.1f}%")
print(f"Mean setup time    : {statistics.mean(setup_ms):.0f} ms")
# nearest-rank p95: the value below which 95% of attaches fall
p95 = sorted(setup_ms)[math.ceil(0.95 * len(setup_ms)) - 1]
print(f"p95 setup time     : {p95:.0f} ms")

# TRY: print the slowest attach. Why does the mean hide it better than the p95?
