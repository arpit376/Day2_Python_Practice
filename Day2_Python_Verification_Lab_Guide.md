# OmniX Labs · Day 2 Python Verification Lab Guide (`verify_multi_ue.py`)

This guide walks through running the **Day 2 Python Test Driver**
(`/opt/oai-4g/lte-tests/verify_multi_ue.py`) to verify a live multi-UE
4G LTE network deployed via `/opt/oai-4g/run_multi_ue.sh`.

Unlike standalone attach tests that start and tear down the radio stack
on every cycle, `verify_multi_ue.py` operates **non-destructively**
against your active `ue1_ns`..`ue6_ns` network namespaces, asserting
control-plane attach completion, IPv4 bearer allocation, and end-to-end
user-plane connectivity, then archiving logs and `pandas` KPI reports.

------------------------------------------------------------------------

## 1. Project Architecture (`/opt/oai-4g/lte-tests/`)

Following standard test-automation separation of concerns, test logic,
configuration, and run outputs are organized into dedicated directories:

``` text
/opt/oai-4g/lte-tests/
├── env/
│   └── lab_config.py        # Environment constants (log paths, base IMSI, ping target, thresholds)
├── libs/
│   ├── results.py           # Typed @dataclass structures (AttachResult, PingResult)
│   ├── parse_logs.py        # Compiled named-group regex parsers for MME, SMF, and ping outputs
│   └── kpi.py               # pandas KPI computation, summary.json writer, and matplotlib plotter
├── verify_multi_ue.py       # Main Day 2 verification runner and artefact collector
└── results/                 # Timestamped per-run artefacts (never hardcoded into source)
```

------------------------------------------------------------------------

## 2. Prerequisites & One-Time Setup

Ensure `pandas` and `matplotlib` are available in your Python
environment:

``` bash
python3 -c "import pandas, matplotlib" 2>/dev/null || pip3 install --quiet pandas matplotlib
```

The script uses Python 3.10+ syntax (including `str | None` type unions
and built-in generic types).

------------------------------------------------------------------------

## 3. Step-by-Step Execution Workflow

### Step 1: Launch the Multi-UE 4G Network

Start between **1 and 6 UEs** using `run_multi_ue.sh`:

``` bash
cd /opt/oai-4g
bash /opt/oai-4g/run_multi_ue.sh 3
```

Wait until all requested UEs report `[+] UE X attached!` and your
terminal prompt returns.

### Step 2: Run the Python Verification Suite

Execute `verify_multi_ue.py` to inspect the live environment:

``` bash
python3 /opt/oai-4g/lte-tests/verify_multi_ue.py
```

**Illustrative expected output** (actual setup times and RTTs will
vary):

``` text
==================================================================
 Day 2 Post-Run Verification (3 Active UE(s))
==================================================================
[PASS] Attach & Bearer | UE1 | IMSI=208930100001111 | IP=10.45.0.2 (ue1_ns) | Setup=118.0 ms
[PASS] Data Plane Ping | UE1 | ue1_ns -> 8.8.8.8 | Loss=0% | Avg RTT=15.4 ms
[PASS] Attach & Bearer | UE2 | IMSI=208930100001112 | IP=10.45.0.3 (ue2_ns) | Setup=121.0 ms
[PASS] Data Plane Ping | UE2 | ue2_ns -> 8.8.8.8 | Loss=0% | Avg RTT=16.1 ms
[PASS] Attach & Bearer | UE3 | IMSI=208930100001113 | IP=10.45.0.4 (ue3_ns) | Setup=116.0 ms
[PASS] Data Plane Ping | UE3 | ue3_ns -> 8.8.8.8 | Loss=0% | Avg RTT=15.9 ms
------------------------------------------------------------------
 Run KPIs (pandas summary):
   Attach Success Rate : 100.0% (3/3)
   Mean Setup Time     : 118.33 ms (p95: 120.7 ms)
   Mean Ping RTT       : 15.8 ms (p95: 16.08 ms)
 Artefacts saved to    : /opt/oai-4g/lte-tests/results/run_20261116_161000
==================================================================
```

### Step 3: Tear Down When Finished

Because `verify_multi_ue.py` leaves your UEs attached so you can run
additional experiments, stop the network manually when your lab session
is complete:

``` bash
bash /opt/oai-4g/run_multi_ue.sh stop
```

------------------------------------------------------------------------

## 4. Command-Line Options

  ---------------------------------------------------------------------------------------------------------
  Command                                                               Description
  --------------------------------------------------------------------- -----------------------------------
  `python3 /opt/oai-4g/lte-tests/verify_multi_ue.py`                    Auto-discovers all active
                                                                        `ue1_ns`..`ue6_ns` namespaces,
                                                                        verifies attach + IP + ICMP ping,
                                                                        and saves KPIs.

  `python3 /opt/oai-4g/lte-tests/verify_multi_ue.py --expected-ues 4`   Fails if the number of active UE
                                                                        namespaces is not exactly `4`.

  `python3 /opt/oai-4g/lte-tests/verify_multi_ue.py --skip-ping`        Verifies control-plane attach and
                                                                        IPv4 bearer assignment without
                                                                        sending ICMP traffic.
  ---------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 5. What Gets Asserted Under the Hood

For each discovered UE (`UE1`..`UE6`), the script verifies:

1.  **Environment & Process Health:** `lte-softmodem` (eNodeB) and
    `lte-uesoftmodem` (UE) processes are running, and at least one
    `ueX_ns` namespace exists.
2.  **MME Control-Plane Attach (`mme.log`):** Regex extracts
    `[<IMSI>] Attach request` and `[<IMSI>] Attach complete` timestamps
    and asserts `outcome == "COMPLETE"`.
3.  **Bearer & IP Consistency (`smf.log` vs. `ueX_ns`):** Checks that
    `oaitun_ue1` inside `ueX_ns` has an active `10.45.0.x` IPv4 address.
    If an SMF IP entry is found, it checks that the two addresses match.
4.  **User-Plane Connectivity (`ping`):** Runs `ping -c 3 -W 2 8.8.8.8`
    inside `ueX_ns` and asserts `0.0%` packet loss.

------------------------------------------------------------------------

## 6. Inspecting Saved Run Artefacts

The `finally:` block attempts to archive a snapshot into
`/opt/oai-4g/lte-tests/results/run_<YYYYMMDD_HHMMSS>/`, including on
verification failures:

-   **`summary.json`** --- Machine-readable KPI metrics
    (`attach_success_rate_pct`, `mean_attach_setup_ms`,
    `p95_attach_setup_ms`, `mean_ping_rtt_ms`, `p95_ping_rtt_ms`) and
    per-UE result records. It is written when at least one attach result
    has been collected.
-   **`kpi_plot.png`** --- Dual bar chart comparing per-UE Attach Setup
    Time (ms) and User-Plane Ping RTT (ms), when matplotlib is installed
    and KPI generation completes.
-   **`enb.log`**, **`mme.log`**, **`smf.log`**,
    **`ue1.log`**..**`ueN.log`** --- Log snapshots captured at
    verification time, when the configured files are readable and
    available.

View the latest JSON summary:

``` bash
latest_run=$(ls -td /opt/oai-4g/lte-tests/results/run_* 2>/dev/null | head -n 1)
cat "$latest_run/summary.json"
```

------------------------------------------------------------------------

## 7. Important Implementation Notes

-   The configured `MAX_SETUP_MS_THRESHOLD` is currently a configuration
    value; the supplied verification script does not yet assert against
    it.
-   The MME timestamp parser currently prefixes timestamps with the year
    `2026`. If the log format or year differs, update
    `parse_mme_attach_events()` accordingly. For robust multi-day
    operation, use the actual log year or derive timestamps from the log
    source.
-   `collect_artefacts()` runs in `finally`, but an unreadable or
    missing log file can still raise an exception during collection.
    Confirm the configured paths and permissions before the lab run.
-   The sample output is illustrative, not a guaranteed result. External
    ICMP reachability to `8.8.8.8` is required for the ping assertion to
    pass.
