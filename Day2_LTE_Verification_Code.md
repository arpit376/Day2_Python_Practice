# OmniX Labs --- Day 2 LTE Verification: Code Setup

This file contains the complete setup commands and source code for the
Day 2 multi-UE LTE verification suite. Each file is presented separately
so it can be copied and pasted directly into the corresponding path.

> Run the commands in a terminal with the required permissions. The
> commands create the project directories and write each source file.

## 1. Create the project structure

``` bash
sudo mkdir -p /opt/oai-4g/lte-tests/{libs,suites,data,env,results}
sudo touch /opt/oai-4g/lte-tests/libs/__init__.py
```

## 2. `env/lab_config.py`

**Destination:** `/opt/oai-4g/lte-tests/env/lab_config.py`

``` python
MME_LOG = "/var/log/open5gs/mme.log"
SMF_LOG = "/var/log/open5gs/smf.log"
ENB_LOG = "/opt/oai-4g/logs/enb.log"
UE_LOG_DIR = "/opt/oai-4g/logs"
RESULTS_DIR = "/opt/oai-4g/lte-tests/results"

BASE_IMSI_PREFIX = "20893"
BASE_MSIN_START = 100001111
PING_TARGET = "8.8.8.8"
PING_COUNT = 3
MAX_SETUP_MS_THRESHOLD = 2000.0
```

Create it:

``` bash
sudo tee /opt/oai-4g/lte-tests/env/lab_config.py > /dev/null <<'EOF'
MME_LOG = "/var/log/open5gs/mme.log"
SMF_LOG = "/var/log/open5gs/smf.log"
ENB_LOG = "/opt/oai-4g/logs/enb.log"
UE_LOG_DIR = "/opt/oai-4g/logs"
RESULTS_DIR = "/opt/oai-4g/lte-tests/results"

BASE_IMSI_PREFIX = "20893"
BASE_MSIN_START = 100001111
PING_TARGET = "8.8.8.8"
PING_COUNT = 3
MAX_SETUP_MS_THRESHOLD = 2000.0
EOF
```

## 3. `libs/results.py`

**Destination:** `/opt/oai-4g/lte-tests/libs/results.py`

``` python
from dataclasses import dataclass, asdict


@dataclass
class AttachResult:
    ue_id: int
    imsi: str
    namespace: str
    success: bool
    ip_address: str | None = None
    setup_ms: float | None = None
    reject_cause: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PingResult:
    ue_id: int
    imsi: str
    namespace: str
    target: str
    transmitted: int
    received: int
    loss_pct: float
    avg_rtt_ms: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)
```

Create it:

``` bash
sudo tee /opt/oai-4g/lte-tests/libs/results.py > /dev/null <<'EOF'
from dataclasses import dataclass, asdict


@dataclass
class AttachResult:
    ue_id: int
    imsi: str
    namespace: str
    success: bool
    ip_address: str | None = None
    setup_ms: float | None = None
    reject_cause: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PingResult:
    ue_id: int
    imsi: str
    namespace: str
    target: str
    transmitted: int
    received: int
    loss_pct: float
    avg_rtt_ms: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)
EOF
```

## 4. `libs/parse_logs.py`

**Destination:** `/opt/oai-4g/lte-tests/libs/parse_logs.py`

``` python
import datetime
import re

TS_RE = re.compile(r"^(?P<ts>\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})")
ATTACH_REQ_RE = re.compile(r"\[(?P<imsi>\d{15})\]\s+Attach request")
ATTACH_COMPLETE_RE = re.compile(r"\[(?P<imsi>\d{15})\]\s+Attach complete")
ATTACH_REJECT_RE = re.compile(
    r"Attach reject.*IMSI\[(?P<imsi>\d{15})\].*cause\[(?P<cause>\d+)\]", re.IGNORECASE
)
SMF_IP_RE = re.compile(r"UE IMSI\[(?P<imsi>\d{15})\].*IPv4\[(?P<ip>10\.45\.0\.\d+)\]")
PING_LOSS_RE = re.compile(
    r"(?P<tx>\d+)\s+packets transmitted,\s+(?P<rx>\d+)\s+received,\s+(?P<loss>[\d.]+)%\s+packet loss"
)
PING_RTT_RE = re.compile(
    r"rtt min/avg/max/mdev = [\d.]+/(?P<avg>[\d.]+)/[\d.]+/[\d.]+\s+ms"
)


def parse_mme_attach_events(mme_lines: list[str], target_imsis: set[str]) -> dict[str, dict]:
    """Extract Attach Request/Complete timestamps and Reject causes per IMSI."""
    events: dict[str, dict] = {
        imsi: {"outcome": "UNKNOWN", "setup_ms": None, "reject_cause": None}
        for imsi in target_imsis
    }
    req_times: dict[str, datetime.datetime] = {}

    for line in mme_lines:
        ts_match = TS_RE.search(line)
        ts = None
        if ts_match:
            ts = datetime.datetime.strptime("2026/" + ts_match.group("ts"), "%Y/%m/%d %H:%M:%S.%f")

        if m := ATTACH_REQ_RE.search(line):
            imsi = m.group("imsi")
            if imsi in events and ts is not None:
                req_times[imsi] = ts

        elif m := ATTACH_COMPLETE_RE.search(line):
            imsi = m.group("imsi")
            if imsi in events:
                events[imsi]["outcome"] = "COMPLETE"
                if ts is not None and imsi in req_times:
                    delta_ms = (ts - req_times[imsi]).total_seconds() * 1000.0
                    events[imsi]["setup_ms"] = round(max(1.0, delta_ms), 2)

        elif m := ATTACH_REJECT_RE.search(line):
            imsi = m.group("imsi")
            if imsi in events:
                events[imsi]["outcome"] = "REJECT"
                events[imsi]["reject_cause"] = int(m.group("cause"))

    return events


def parse_smf_ips(smf_lines: list[str], target_imsis: set[str]) -> dict[str, str]:
    """Extract latest assigned 10.45.0.x IPv4 per IMSI from Open5GS SMF log."""
    assigned: dict[str, str] = {}
    for line in smf_lines:
        if m := SMF_IP_RE.search(line):
            imsi = m.group("imsi")
            if imsi in target_imsis:
                assigned[imsi] = m.group("ip")
    return assigned
```

Create it:

``` bash
sudo tee /opt/oai-4g/lte-tests/libs/parse_logs.py > /dev/null <<'EOF'
import datetime
import re

TS_RE = re.compile(r"^(?P<ts>\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})")
ATTACH_REQ_RE = re.compile(r"\[(?P<imsi>\d{15})\]\s+Attach request")
ATTACH_COMPLETE_RE = re.compile(r"\[(?P<imsi>\d{15})\]\s+Attach complete")
ATTACH_REJECT_RE = re.compile(
    r"Attach reject.*IMSI\[(?P<imsi>\d{15})\].*cause\[(?P<cause>\d+)\]", re.IGNORECASE
)
SMF_IP_RE = re.compile(r"UE IMSI\[(?P<imsi>\d{15})\].*IPv4\[(?P<ip>10\.45\.0\.\d+)\]")
PING_LOSS_RE = re.compile(
    r"(?P<tx>\d+)\s+packets transmitted,\s+(?P<rx>\d+)\s+received,\s+(?P<loss>[\d.]+)%\s+packet loss"
)
PING_RTT_RE = re.compile(
    r"rtt min/avg/max/mdev = [\d.]+/(?P<avg>[\d.]+)/[\d.]+/[\d.]+\s+ms"
)


def parse_mme_attach_events(mme_lines: list[str], target_imsis: set[str]) -> dict[str, dict]:
    """Extract Attach Request/Complete timestamps and Reject causes per IMSI."""
    events: dict[str, dict] = {
        imsi: {"outcome": "UNKNOWN", "setup_ms": None, "reject_cause": None}
        for imsi in target_imsis
    }
    req_times: dict[str, datetime.datetime] = {}

    for line in mme_lines:
        ts_match = TS_RE.search(line)
        ts = None
        if ts_match:
            ts = datetime.datetime.strptime("2026/" + ts_match.group("ts"), "%Y/%m/%d %H:%M:%S.%f")

        if m := ATTACH_REQ_RE.search(line):
            imsi = m.group("imsi")
            if imsi in events and ts is not None:
                req_times[imsi] = ts

        elif m := ATTACH_COMPLETE_RE.search(line):
            imsi = m.group("imsi")
            if imsi in events:
                events[imsi]["outcome"] = "COMPLETE"
                if ts is not None and imsi in req_times:
                    delta_ms = (ts - req_times[imsi]).total_seconds() * 1000.0
                    events[imsi]["setup_ms"] = round(max(1.0, delta_ms), 2)

        elif m := ATTACH_REJECT_RE.search(line):
            imsi = m.group("imsi")
            if imsi in events:
                events[imsi]["outcome"] = "REJECT"
                events[imsi]["reject_cause"] = int(m.group("cause"))

    return events


def parse_smf_ips(smf_lines: list[str], target_imsis: set[str]) -> dict[str, str]:
    """Extract latest assigned 10.45.0.x IPv4 per IMSI from Open5GS SMF log."""
    assigned: dict[str, str] = {}
    for line in smf_lines:
        if m := SMF_IP_RE.search(line):
            imsi = m.group("imsi")
            if imsi in target_imsis:
                assigned[imsi] = m.group("ip")
    return assigned
EOF
```

## 5. `libs/kpi.py`

**Destination:** `/opt/oai-4g/lte-tests/libs/kpi.py`

``` python
import json
from pathlib import Path
import pandas as pd


def compute_and_save_kpis(
    attach_records: list[dict], ping_records: list[dict], run_dir: Path
) -> dict:
    """Compute attach & user-plane KPIs with pandas, write summary.json and PNG plot."""
    df_attach = pd.DataFrame(attach_records)
    df_ping = pd.DataFrame(ping_records)

    attempts = len(df_attach)
    successes = int(df_attach["success"].sum()) if attempts else 0
    success_rate = round((successes / attempts) * 100.0, 2) if attempts else 0.0

    valid_setup = df_attach["setup_ms"].dropna() if "setup_ms" in df_attach else pd.Series(dtype=float)
    mean_setup_ms = round(float(valid_setup.mean()), 2) if not valid_setup.empty else None
    p95_setup_ms = round(float(valid_setup.quantile(0.95)), 2) if not valid_setup.empty else None

    valid_rtt = df_ping["avg_rtt_ms"].dropna() if "avg_rtt_ms" in df_ping else pd.Series(dtype=float)
    mean_rtt_ms = round(float(valid_rtt.mean()), 2) if not valid_rtt.empty else None
    p95_rtt_ms = round(float(valid_rtt.quantile(0.95)), 2) if not valid_rtt.empty else None

    summary = {
        "total_ues_tested": attempts,
        "attached_ues": successes,
        "attach_success_rate_pct": success_rate,
        "mean_attach_setup_ms": mean_setup_ms,
        "p95_attach_setup_ms": p95_setup_ms,
        "mean_ping_rtt_ms": mean_rtt_ms,
        "p95_ping_rtt_ms": p95_rtt_ms,
        "attach_details": attach_records,
        "ping_details": ping_records,
    }

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    # Generate KPI bar chart if matplotlib is installed
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        labels = [f"UE{r['ue_id']}" for r in attach_records]

        setup_vals = [r["setup_ms"] or 0.0 for r in attach_records]
        axes[0].bar(labels, setup_vals, color="#1f77b4")
        axes[0].set_title("Attach Setup Time (ms)")
        axes[0].set_ylabel("Milliseconds")

        rtt_vals = [r["avg_rtt_ms"] or 0.0 for r in ping_records]
        axes[1].bar(labels, rtt_vals, color="#2ca02c")
        axes[1].set_title("User-Plane Ping RTT (ms)")
        axes[1].set_ylabel("Milliseconds")

        plt.tight_layout()
        plt.savefig(run_dir / "kpi_plot.png", dpi=150)
        plt.close(fig)
    except ImportError:
        pass

    return summary
```

Create it:

``` bash
sudo tee /opt/oai-4g/lte-tests/libs/kpi.py > /dev/null <<'EOF'
import json
from pathlib import Path
import pandas as pd


def compute_and_save_kpis(
    attach_records: list[dict], ping_records: list[dict], run_dir: Path
) -> dict:
    """Compute attach & user-plane KPIs with pandas, write summary.json and PNG plot."""
    df_attach = pd.DataFrame(attach_records)
    df_ping = pd.DataFrame(ping_records)

    attempts = len(df_attach)
    successes = int(df_attach["success"].sum()) if attempts else 0
    success_rate = round((successes / attempts) * 100.0, 2) if attempts else 0.0

    valid_setup = df_attach["setup_ms"].dropna() if "setup_ms" in df_attach else pd.Series(dtype=float)
    mean_setup_ms = round(float(valid_setup.mean()), 2) if not valid_setup.empty else None
    p95_setup_ms = round(float(valid_setup.quantile(0.95)), 2) if not valid_setup.empty else None

    valid_rtt = df_ping["avg_rtt_ms"].dropna() if "avg_rtt_ms" in df_ping else pd.Series(dtype=float)
    mean_rtt_ms = round(float(valid_rtt.mean()), 2) if not valid_rtt.empty else None
    p95_rtt_ms = round(float(valid_rtt.quantile(0.95)), 2) if not valid_rtt.empty else None

    summary = {
        "total_ues_tested": attempts,
        "attached_ues": successes,
        "attach_success_rate_pct": success_rate,
        "mean_attach_setup_ms": mean_setup_ms,
        "p95_attach_setup_ms": p95_setup_ms,
        "mean_ping_rtt_ms": mean_rtt_ms,
        "p95_ping_rtt_ms": p95_rtt_ms,
        "attach_details": attach_records,
        "ping_details": ping_records,
    }

    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    # Generate KPI bar chart if matplotlib is installed
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        labels = [f"UE{r['ue_id']}" for r in attach_records]

        setup_vals = [r["setup_ms"] or 0.0 for r in attach_records]
        axes[0].bar(labels, setup_vals, color="#1f77b4")
        axes[0].set_title("Attach Setup Time (ms)")
        axes[0].set_ylabel("Milliseconds")

        rtt_vals = [r["avg_rtt_ms"] or 0.0 for r in ping_records]
        axes[1].bar(labels, rtt_vals, color="#2ca02c")
        axes[1].set_title("User-Plane Ping RTT (ms)")
        axes[1].set_ylabel("Milliseconds")

        plt.tight_layout()
        plt.savefig(run_dir / "kpi_plot.png", dpi=150)
        plt.close(fig)
    except ImportError:
        pass

    return summary
EOF
```

## 6. `verify_multi_ue.py`

**Destination:** `/opt/oai-4g/lte-tests/verify_multi_ue.py`

``` python
#!/usr/bin/env python3
"""
Day 2 Post-Deployment Verification Suite for run_multi_ue.sh.

Run AFTER `bash /opt/oai-4g/run_multi_ue.sh <N>`:
  python3 /opt/oai-4g/lte-tests/verify_multi_ue.py
  python3 /opt/oai-4g/lte-tests/verify_multi_ue.py --expected-ues 3
"""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from env.lab_config import (
    BASE_IMSI_PREFIX,
    BASE_MSIN_START,
    ENB_LOG,
    MME_LOG,
    PING_COUNT,
    PING_TARGET,
    RESULTS_DIR,
    SMF_LOG,
    UE_LOG_DIR,
)
from libs.kpi import compute_and_save_kpis
from libs.parse_logs import (
    PING_LOSS_RE,
    PING_RTT_RE,
    parse_mme_attach_events,
    parse_smf_ips,
)
from libs.results import AttachResult, PingResult


def run_cmd(cmd: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    """Execute command with explicit timeout (never hang on a stalled process)."""
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)


def discover_active_namespaces() -> list[int]:
    """Find active ue1_ns..ue6_ns namespaces created by run_multi_ue.sh."""
    proc = run_cmd(["ip", "netns", "list"], timeout=5)
    ue_ids = []
    for line in proc.stdout.splitlines():
        m = re.match(r"^ue([1-6])_ns\b", line.strip())
        if m:
            ue_ids.append(int(m.group(1)))
    return sorted(ue_ids)


def read_log_lines(path: str) -> list[str]:
    """Read log file directly or via sudo if owned by open5gs."""
    p = Path(path)
    try:
        return p.read_text(errors="replace").splitlines()
    except PermissionError:
        proc = run_cmd(["sudo", "cat", path], timeout=10)
        return proc.stdout.splitlines()


def check_ue_interface_ip(ns_name: str) -> str | None:
    """Verify oaitun_ue1 is UP inside ueX_ns and return its assigned IPv4."""
    proc = run_cmd(
        ["sudo", "ip", "netns", "exec", ns_name, "ip", "-4", "-o", "addr", "show", "oaitun_ue1"],
        timeout=5,
    )
    if proc.returncode != 0:
        return None
    m = re.search(r"inet\s+(10\.45\.0\.\d+)/\d+", proc.stdout)
    return m.group(1) if m else None


def run_ue_ping(ue_id: int, imsi: str, ns_name: str, target: str, count: int) -> PingResult:
    """Execute user-plane ping inside the UE's isolated namespace and parse RTT/loss."""
    proc = run_cmd(
        ["sudo", "ip", "netns", "exec", ns_name, "ping", "-c", str(count), "-W", "2", target],
        timeout=count * 3 + 5,
    )
    output = proc.stdout + "\n" + proc.stderr
    loss_m = PING_LOSS_RE.search(output)
    rtt_m = PING_RTT_RE.search(output)

    if not loss_m:
        return PingResult(
            ue_id=ue_id,
            imsi=imsi,
            namespace=ns_name,
            target=target,
            transmitted=count,
            received=0,
            loss_pct=100.0,
            avg_rtt_ms=None,
        )

    return PingResult(
        ue_id=ue_id,
        imsi=imsi,
        namespace=ns_name,
        target=target,
        transmitted=int(loss_m.group("tx")),
        received=int(loss_m.group("rx")),
        loss_pct=float(loss_m.group("loss")),
        avg_rtt_ms=float(rtt_m.group("avg")) if rtt_m else None,
    )


def collect_artefacts(run_dir: Path, ue_ids: list[int]) -> None:
    """Collect eNB, MME, SMF, and per-UE logs into results/<timestamp>/ before exit."""
    run_dir.mkdir(parents=True, exist_ok=True)
    for src, dst_name in [(ENB_LOG, "enb.log"), (MME_LOG, "mme.log"), (SMF_LOG, "smf.log")]:
        lines = read_log_lines(src)
        if lines:
            (run_dir / dst_name).write_text("\n".join(lines[-500:]) + "\n")

    for ue_id in ue_ids:
        ue_log = Path(UE_LOG_DIR) / f"ue{ue_id}.log"
        if ue_log.exists():
            shutil.copy2(ue_log, run_dir / f"ue{ue_id}.log")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Day 2 Python Test Driver: Verify live multi-UE setup after run_multi_ue.sh"
    )
    parser.add_argument(
        "--expected-ues",
        type=int,
        default=None,
        help="Optional expected count of attached UEs (e.g., 2 or 3)",
    )
    parser.add_argument(
        "--skip-ping",
        action="store_true",
        help="Verify control-plane attach & IP allocation only without ICMP ping",
    )
    args = parser.parse_args()

    ts_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(RESULTS_DIR) / f"run_{ts_tag}"
    run_dir.mkdir(parents=True, exist_ok=True)

    ue_ids = discover_active_namespaces()
    attach_results: list[AttachResult] = []
    ping_results: list[PingResult] = []
    failures: list[str] = []

    try:
        # 1. Pre-check: verify run_multi_ue.sh has active UE namespaces & running modems
        assert ue_ids, (
            "No active ueX_ns namespaces found. Run `bash /opt/oai-4g/run_multi_ue.sh <N>` first."
        )
        if args.expected_ues is not None:
            assert len(ue_ids) == args.expected_ues, (
                f"Expected {args.expected_ues} active UEs, found {len(ue_ids)} ({ue_ids})"
            )

        enb_proc = run_cmd(["pgrep", "-f", "[l]te-softmodem"], timeout=5)
        assert enb_proc.returncode == 0, "OAI eNodeB (lte-softmodem) process is not running"

        ue_proc = run_cmd(["pgrep", "-f", "[l]te-uesoftmodem"], timeout=5)
        assert ue_proc.returncode == 0, "OAI UE (lte-uesoftmodem) process is not running"

        # 2. Map expected IMSIs (208930100001111 .. 208930100001116)
        imsi_map = {
            ue_id: f"{BASE_IMSI_PREFIX}{BASE_MSIN_START + ue_id - 1:010d}"
            for ue_id in ue_ids
        }
        target_imsis = set(imsi_map.values())

        # 3. Parse MME & SMF logs with regular expressions
        mme_events = parse_mme_attach_events(read_log_lines(MME_LOG), target_imsis)
        smf_ips = parse_smf_ips(read_log_lines(SMF_LOG), target_imsis)

        print("==================================================================")
        print(f" Day 2 Post-Run Verification ({len(ue_ids)} Active UE(s))")
        print("==================================================================")

        # 4. Assert Attach, IP allocation, and User-Plane traffic per UE
        for ue_id in ue_ids:
            imsi = imsi_map[ue_id]
            ns_name = f"ue{ue_id}_ns"
            mme_info = mme_events[imsi]
            ns_ip = check_ue_interface_ip(ns_name)
            smf_ip = smf_ips.get(imsi)

            attached_ok = (mme_info["outcome"] == "COMPLETE") and (ns_ip is not None)
            res = AttachResult(
                ue_id=ue_id,
                imsi=imsi,
                namespace=ns_name,
                success=attached_ok,
                ip_address=ns_ip or smf_ip,
                setup_ms=mme_info["setup_ms"],
                reject_cause=mme_info["reject_cause"],
            )
            attach_results.append(res)

            try:
                assert mme_info["outcome"] == "COMPLETE", (
                    f"UE{ue_id} ({imsi}): No Attach Complete in MME log (state={mme_info['outcome']})"
                )
                assert ns_ip is not None, (
                    f"UE{ue_id} ({imsi}): Attach done, but no IPv4 allocated on oaitun_ue1 in {ns_name}"
                )
                if smf_ip:
                    assert ns_ip == smf_ip, (
                        f"UE{ue_id} ({imsi}): Namespace IP {ns_ip} != SMF assigned IP {smf_ip}"
                    )
                print(
                    f"[PASS] Attach & Bearer | UE{ue_id} | IMSI={imsi} | "
                    f"IP={ns_ip} ({ns_name}) | Setup={res.setup_ms} ms"
                )
            except AssertionError as exc:
                failures.append(str(exc))
                print(f"[FAIL] Attach & Bearer | {exc}")

            if not args.skip_ping and attached_ok:
                p_res = run_ue_ping(ue_id, imsi, ns_name, PING_TARGET, PING_COUNT)
                ping_results.append(p_res)
                try:
                    assert p_res.loss_pct == 0.0, (
                        f"UE{ue_id} ({ns_name}): Ping to {PING_TARGET} had {p_res.loss_pct}% packet loss"
                    )
                    print(
                        f"[PASS] Data Plane Ping | UE{ue_id} | {ns_name} -> {PING_TARGET} | "
                        f"Loss=0% | Avg RTT={p_res.avg_rtt_ms} ms"
                    )
                except AssertionError as exc:
                    failures.append(str(exc))
                    print(f"[FAIL] Data Plane Ping | {exc}")

    except AssertionError as top_err:
        failures.append(str(top_err))
        print(f"[FAIL] Environment Pre-Check: {top_err}")

    finally:
        # Rule from Module 2.4: Collect artefacts and compute KPIs whether pass or fail
        collect_artefacts(run_dir, ue_ids)
        if attach_results:
            kpis = compute_and_save_kpis(
                [r.to_dict() for r in attach_results],
                [p.to_dict() for p in ping_results],
                run_dir,
            )
            print("------------------------------------------------------------------")
            print(" Run KPIs (pandas summary):")
            print(f"   Attach Success Rate : {kpis['attach_success_rate_pct']}% ({kpis['attached_ues']}/{kpis['total_ues_tested']})")
            print(f"   Mean Setup Time     : {kpis['mean_attach_setup_ms']} ms (p95: {kpis['p95_attach_setup_ms']} ms)")
            if kpis["mean_ping_rtt_ms"] is not None:
                print(f"   Mean Ping RTT       : {kpis['mean_ping_rtt_ms']} ms (p95: {kpis['p95_ping_rtt_ms']} ms)")
        print(f" Artefacts saved to    : {run_dir}")
        print("==================================================================")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
```

Create it:

``` bash
sudo tee /opt/oai-4g/lte-tests/verify_multi_ue.py > /dev/null <<'EOF'
#!/usr/bin/env python3
"""
Day 2 Post-Deployment Verification Suite for run_multi_ue.sh.

Run AFTER `bash /opt/oai-4g/run_multi_ue.sh <N>`:
  python3 /opt/oai-4g/lte-tests/verify_multi_ue.py
  python3 /opt/oai-4g/lte-tests/verify_multi_ue.py --expected-ues 3
"""
import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from env.lab_config import (
    BASE_IMSI_PREFIX,
    BASE_MSIN_START,
    ENB_LOG,
    MME_LOG,
    PING_COUNT,
    PING_TARGET,
    RESULTS_DIR,
    SMF_LOG,
    UE_LOG_DIR,
)
from libs.kpi import compute_and_save_kpis
from libs.parse_logs import (
    PING_LOSS_RE,
    PING_RTT_RE,
    parse_mme_attach_events,
    parse_smf_ips,
)
from libs.results import AttachResult, PingResult


def run_cmd(cmd: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    """Execute command with explicit timeout (never hang on a stalled process)."""
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)


def discover_active_namespaces() -> list[int]:
    """Find active ue1_ns..ue6_ns namespaces created by run_multi_ue.sh."""
    proc = run_cmd(["ip", "netns", "list"], timeout=5)
    ue_ids = []
    for line in proc.stdout.splitlines():
        m = re.match(r"^ue([1-6])_ns\b", line.strip())
        if m:
            ue_ids.append(int(m.group(1)))
    return sorted(ue_ids)


def read_log_lines(path: str) -> list[str]:
    """Read log file directly or via sudo if owned by open5gs."""
    p = Path(path)
    try:
        return p.read_text(errors="replace").splitlines()
    except PermissionError:
        proc = run_cmd(["sudo", "cat", path], timeout=10)
        return proc.stdout.splitlines()


def check_ue_interface_ip(ns_name: str) -> str | None:
    """Verify oaitun_ue1 is UP inside ueX_ns and return its assigned IPv4."""
    proc = run_cmd(
        ["sudo", "ip", "netns", "exec", ns_name, "ip", "-4", "-o", "addr", "show", "oaitun_ue1"],
        timeout=5,
    )
    if proc.returncode != 0:
        return None
    m = re.search(r"inet\s+(10\.45\.0\.\d+)/\d+", proc.stdout)
    return m.group(1) if m else None


def run_ue_ping(ue_id: int, imsi: str, ns_name: str, target: str, count: int) -> PingResult:
    """Execute user-plane ping inside the UE's isolated namespace and parse RTT/loss."""
    proc = run_cmd(
        ["sudo", "ip", "netns", "exec", ns_name, "ping", "-c", str(count), "-W", "2", target],
        timeout=count * 3 + 5,
    )
    output = proc.stdout + "\n" + proc.stderr
    loss_m = PING_LOSS_RE.search(output)
    rtt_m = PING_RTT_RE.search(output)

    if not loss_m:
        return PingResult(
            ue_id=ue_id,
            imsi=imsi,
            namespace=ns_name,
            target=target,
            transmitted=count,
            received=0,
            loss_pct=100.0,
            avg_rtt_ms=None,
        )

    return PingResult(
        ue_id=ue_id,
        imsi=imsi,
        namespace=ns_name,
        target=target,
        transmitted=int(loss_m.group("tx")),
        received=int(loss_m.group("rx")),
        loss_pct=float(loss_m.group("loss")),
        avg_rtt_ms=float(rtt_m.group("avg")) if rtt_m else None,
    )


def collect_artefacts(run_dir: Path, ue_ids: list[int]) -> None:
    """Collect eNB, MME, SMF, and per-UE logs into results/<timestamp>/ before exit."""
    run_dir.mkdir(parents=True, exist_ok=True)
    for src, dst_name in [(ENB_LOG, "enb.log"), (MME_LOG, "mme.log"), (SMF_LOG, "smf.log")]:
        lines = read_log_lines(src)
        if lines:
            (run_dir / dst_name).write_text("\n".join(lines[-500:]) + "\n")

    for ue_id in ue_ids:
        ue_log = Path(UE_LOG_DIR) / f"ue{ue_id}.log"
        if ue_log.exists():
            shutil.copy2(ue_log, run_dir / f"ue{ue_id}.log")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Day 2 Python Test Driver: Verify live multi-UE setup after run_multi_ue.sh"
    )
    parser.add_argument(
        "--expected-ues",
        type=int,
        default=None,
        help="Optional expected count of attached UEs (e.g., 2 or 3)",
    )
    parser.add_argument(
        "--skip-ping",
        action="store_true",
        help="Verify control-plane attach & IP allocation only without ICMP ping",
    )
    args = parser.parse_args()

    ts_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(RESULTS_DIR) / f"run_{ts_tag}"
    run_dir.mkdir(parents=True, exist_ok=True)

    ue_ids = discover_active_namespaces()
    attach_results: list[AttachResult] = []
    ping_results: list[PingResult] = []
    failures: list[str] = []

    try:
        # 1. Pre-check: verify run_multi_ue.sh has active UE namespaces & running modems
        assert ue_ids, (
            "No active ueX_ns namespaces found. Run `bash /opt/oai-4g/run_multi_ue.sh <N>` first."
        )
        if args.expected_ues is not None:
            assert len(ue_ids) == args.expected_ues, (
                f"Expected {args.expected_ues} active UEs, found {len(ue_ids)} ({ue_ids})"
            )

        enb_proc = run_cmd(["pgrep", "-f", "[l]te-softmodem"], timeout=5)
        assert enb_proc.returncode == 0, "OAI eNodeB (lte-softmodem) process is not running"

        ue_proc = run_cmd(["pgrep", "-f", "[l]te-uesoftmodem"], timeout=5)
        assert ue_proc.returncode == 0, "OAI UE (lte-uesoftmodem) process is not running"

        # 2. Map expected IMSIs (208930100001111 .. 208930100001116)
        imsi_map = {
            ue_id: f"{BASE_IMSI_PREFIX}{BASE_MSIN_START + ue_id - 1:010d}"
            for ue_id in ue_ids
        }
        target_imsis = set(imsi_map.values())

        # 3. Parse MME & SMF logs with regular expressions
        mme_events = parse_mme_attach_events(read_log_lines(MME_LOG), target_imsis)
        smf_ips = parse_smf_ips(read_log_lines(SMF_LOG), target_imsis)

        print("==================================================================")
        print(f" Day 2 Post-Run Verification ({len(ue_ids)} Active UE(s))")
        print("==================================================================")

        # 4. Assert Attach, IP allocation, and User-Plane traffic per UE
        for ue_id in ue_ids:
            imsi = imsi_map[ue_id]
            ns_name = f"ue{ue_id}_ns"
            mme_info = mme_events[imsi]
            ns_ip = check_ue_interface_ip(ns_name)
            smf_ip = smf_ips.get(imsi)

            attached_ok = (mme_info["outcome"] == "COMPLETE") and (ns_ip is not None)
            res = AttachResult(
                ue_id=ue_id,
                imsi=imsi,
                namespace=ns_name,
                success=attached_ok,
                ip_address=ns_ip or smf_ip,
                setup_ms=mme_info["setup_ms"],
                reject_cause=mme_info["reject_cause"],
            )
            attach_results.append(res)

            try:
                assert mme_info["outcome"] == "COMPLETE", (
                    f"UE{ue_id} ({imsi}): No Attach Complete in MME log (state={mme_info['outcome']})"
                )
                assert ns_ip is not None, (
                    f"UE{ue_id} ({imsi}): Attach done, but no IPv4 allocated on oaitun_ue1 in {ns_name}"
                )
                if smf_ip:
                    assert ns_ip == smf_ip, (
                        f"UE{ue_id} ({imsi}): Namespace IP {ns_ip} != SMF assigned IP {smf_ip}"
                    )
                print(
                    f"[PASS] Attach & Bearer | UE{ue_id} | IMSI={imsi} | "
                    f"IP={ns_ip} ({ns_name}) | Setup={res.setup_ms} ms"
                )
            except AssertionError as exc:
                failures.append(str(exc))
                print(f"[FAIL] Attach & Bearer | {exc}")

            if not args.skip_ping and attached_ok:
                p_res = run_ue_ping(ue_id, imsi, ns_name, PING_TARGET, PING_COUNT)
                ping_results.append(p_res)
                try:
                    assert p_res.loss_pct == 0.0, (
                        f"UE{ue_id} ({ns_name}): Ping to {PING_TARGET} had {p_res.loss_pct}% packet loss"
                    )
                    print(
                        f"[PASS] Data Plane Ping | UE{ue_id} | {ns_name} -> {PING_TARGET} | "
                        f"Loss=0% | Avg RTT={p_res.avg_rtt_ms} ms"
                    )
                except AssertionError as exc:
                    failures.append(str(exc))
                    print(f"[FAIL] Data Plane Ping | {exc}")

    except AssertionError as top_err:
        failures.append(str(top_err))
        print(f"[FAIL] Environment Pre-Check: {top_err}")

    finally:
        # Rule from Module 2.4: Collect artefacts and compute KPIs whether pass or fail
        collect_artefacts(run_dir, ue_ids)
        if attach_results:
            kpis = compute_and_save_kpis(
                [r.to_dict() for r in attach_results],
                [p.to_dict() for p in ping_results],
                run_dir,
            )
            print("------------------------------------------------------------------")
            print(" Run KPIs (pandas summary):")
            print(f"   Attach Success Rate : {kpis['attach_success_rate_pct']}% ({kpis['attached_ues']}/{kpis['total_ues_tested']})")
            print(f"   Mean Setup Time     : {kpis['mean_attach_setup_ms']} ms (p95: {kpis['p95_attach_setup_ms']} ms)")
            if kpis["mean_ping_rtt_ms"] is not None:
                print(f"   Mean Ping RTT       : {kpis['mean_ping_rtt_ms']} ms (p95: {kpis['p95_ping_rtt_ms']} ms)")
        print(f" Artefacts saved to    : {run_dir}")
        print("==================================================================")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
EOF
```

## 7. Install dependencies and set permissions

``` bash
python3 -c "import pandas, matplotlib" 2>/dev/null || pip3 install --quiet pandas matplotlib
sudo chmod +x /opt/oai-4g/lte-tests/verify_multi_ue.py
```

## 8. Run the verification

``` bash
# Start the LTE network with three UEs
bash /opt/oai-4g/run_multi_ue.sh 3

# In another terminal, run the verification suite
python3 /opt/oai-4g/lte-tests/verify_multi_ue.py

# Optional: require exactly three active UE namespaces
python3 /opt/oai-4g/lte-tests/verify_multi_ue.py --expected-ues 3

# Optional: skip ICMP ping checks
python3 /opt/oai-4g/lte-tests/verify_multi_ue.py --skip-ping
```

The verification script is non-destructive: it does not stop the active
LTE network. Stop the network manually when finished:

``` bash
bash /opt/oai-4g/run_multi_ue.sh stop
```
