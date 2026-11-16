"""Exercise 7 (optional) - The same KPI idea in pandas, with a plot saved as PNG."""
import re
import pandas as pd

rows = []
for line in open("sample_mme.log"):
    m = re.match(r"^(\S+ \S+) \[MME\] NAS Attach (Request|Complete|Reject) imsi=(\d+)", line)
    if m:
        rows.append({"ts": pd.to_datetime(m[1]), "msg": m[2], "imsi": m[3]})

df = pd.DataFrame(rows)
req = df[df.msg == "Request"].set_index("imsi").ts
done = df[df.msg == "Complete"].set_index("imsi").ts
setup = ((done - req.loc[done.index]).dt.total_seconds() * 1000).rename("setup_ms")
print(setup.describe()[["count", "mean", "max"]])
print("p95 (ms):", round(setup.quantile(0.95, interpolation="higher")))

try:
    import matplotlib; matplotlib.use("Agg")
    setup.plot(kind="bar", title="Attach setup time (ms)").get_figure().savefig("setup_time.png")
    print("Saved setup_time.png")
except ImportError:
    print("matplotlib not installed - skipping the plot")

# TRY: add a column that flags attaches slower than 500 ms.
