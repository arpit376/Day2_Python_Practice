# OmniX Labs — Day 2 LTE Verification Suite

This README covers the prerequisites and initial machine setup required before running the Day 2 multi-UE LTE verification suite.

The verification suite is designed to run **after** the LTE network has been started with:

```bash
bash /opt/oai-4g/run_multi_ue.sh 3
```

It checks active UE namespaces, MME attach events, UE IPv4 bearer addresses, and user-plane connectivity. It also saves run artefacts and KPI reports.

---

## 1. System prerequisites

Use an Ubuntu machine where the OAI LTE and Open5GS environment is already installed and configured.

| Requirement | Purpose |
|---|---|
| Ubuntu Linux | Host operating system for the LTE lab |
| Python 3.10 or later | Runs the verification script and its type annotations |
| `pip` | Installs the Python dependencies |
| `pandas` | Computes attach and ping KPIs |
| `matplotlib` | Generates `kpi_plot.png` |
| `iproute2` | Provides `ip` and network namespace commands |
| `iputils-ping` | Provides the `ping` command |
| `sudo` access | Reads protected logs and inspects UE namespaces/interfaces |
| Active OAI/Open5GS LTE setup | Supplies the eNB, UE, MME and SMF processes/logs |

The LTE network itself must be operational before running the verification script.

---

## 2. Install system packages

Refresh the package index:

```bash
sudo apt update
```

Install Python, pip, virtual-environment support, and the networking utilities:

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    iproute2 \
    iputils-ping
```

Check the installed versions:

```bash
python3 --version
python3 -m pip --version
```

**Python version:** The supplied code uses syntax such as `str | None`, which requires Python 3.10 or later. If `python3 --version` reports an older version, install/use Python 3.10+ before proceeding.

---

## 3. Create the project directories

Create the directory structure:

```bash
sudo mkdir -p /opt/oai-4g/lte-tests/{libs,suites,data,env,results}
sudo touch /opt/oai-4g/lte-tests/libs/__init__.py
```

The expected structure is:

```text
/opt/oai-4g/lte-tests/
├── env/
│   └── lab_config.py
├── libs/
│   ├── __init__.py
│   ├── results.py
│   ├── parse_logs.py
│   └── kpi.py
├── suites/
├── data/
├── results/
└── verify_multi_ue.py
```

Place the source files in the paths shown above. Refer to `Day2_LTE_Verification_Code.md` for the complete, copy-and-paste-ready code.

---

## 4. Set file and directory permissions

The verification script must be executable:

```bash
sudo chmod +x /opt/oai-4g/lte-tests/verify_multi_ue.py
```

Ensure the lab user can read the source files and write run results. Replace `$USER` with the intended Linux account if necessary:

```bash
sudo chown -R "$USER":"$USER" /opt/oai-4g/lte-tests
sudo chmod -R u+rwX /opt/oai-4g/lte-tests
```

Check the script permission:

```bash
ls -l /opt/oai-4g/lte-tests/verify_multi_ue.py
```

The output should show an executable bit, for example:

```text
-rwxr-xr-x
```

Check that the results directory is writable:

```bash
test -w /opt/oai-4g/lte-tests/results \
    && echo "[PASS] Results directory is writable" \
    || echo "[FAIL] Results directory is not writable"
```

> **Permission note:** The ownership command above changes ownership only under `/opt/oai-4g/lte-tests`. Do not recursively change ownership of `/opt/oai-4g`, `/var/log/open5gs`, or other system directories just to make this test work. The script uses `sudo` for protected log and namespace operations where configured.

---

## 5. Install Python dependencies using a virtual environment

A Python virtual environment is recommended on Ubuntu. It avoids modifying the system-managed Python installation and prevents common `externally-managed-environment` errors.

Create the environment:

```bash
python3 -m venv /opt/oai-4g/lte-tests/.venv
```

Activate it:

```bash
source /opt/oai-4g/lte-tests/.venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the required packages:

```bash
python -m pip install pandas matplotlib
```

Verify the imports:

```bash
python -c "import pandas, matplotlib; print('pandas:', pandas.__version__); print('matplotlib:', matplotlib.__version__)"
```

Expected result: both package versions are printed without an import error.

### Activate the environment before each lab run

Whenever you open a new terminal, activate the virtual environment again:

```bash
source /opt/oai-4g/lte-tests/.venv/bin/activate
```

Then run the verification script using the virtual-environment Python:

```bash
python /opt/oai-4g/lte-tests/verify_multi_ue.py
```

To leave the virtual environment:

```bash
deactivate
```

### Alternative: install packages for the system Python

If your environment is managed by an administrator and system-wide installation is explicitly permitted, use the distribution packages:

```bash
sudo apt install -y python3-pandas python3-matplotlib
```

Then run:

```bash
python3 -c "import pandas, matplotlib; print('Dependencies OK')"
```

Avoid `sudo pip install` and avoid using `--break-system-packages` on a normal Ubuntu installation. Prefer the virtual-environment method above.

---

## 6. Verify log paths and permissions

The default paths are defined in `env/lab_config.py`:

```python
MME_LOG = "/var/log/open5gs/mme.log"
SMF_LOG = "/var/log/open5gs/smf.log"
ENB_LOG = "/opt/oai-4g/logs/enb.log"
UE_LOG_DIR = "/opt/oai-4g/logs"
RESULTS_DIR = "/opt/oai-4g/lte-tests/results"
```

Check that the expected log files exist:

```bash
sudo ls -l \
    /var/log/open5gs/mme.log \
    /var/log/open5gs/smf.log \
    /opt/oai-4g/logs/enb.log
```

Check the UE log directory:

```bash
sudo ls -ld /opt/oai-4g/logs
```

The script attempts to read protected MME and SMF logs through `sudo cat` if direct reading raises `PermissionError`. If `sudo` requires a password, enter it when prompted. For unattended operation, configure an appropriately restricted sudo policy with the system administrator rather than granting unrestricted passwordless sudo.

The configured paths must match the actual paths used by your lab deployment. Edit `env/lab_config.py` if your logs are stored elsewhere.

---

## 7. Run pre-flight checks

Run these checks before starting the verification:

```bash
# Python version
python --version

# Required Python packages
python -c "import pandas, matplotlib; print('[PASS] Python dependencies available')"

# Network namespace utility
ip netns list

# Ping utility
ping -V

# Verification script
test -x /opt/oai-4g/lte-tests/verify_multi_ue.py \
    && echo "[PASS] Verification script is executable" \
    || echo "[FAIL] Verification script is not executable"

# Results directory
test -w /opt/oai-4g/lte-tests/results \
    && echo "[PASS] Results directory is writable" \
    || echo "[FAIL] Results directory is not writable"
```

An empty `ip netns list` output is acceptable before starting the LTE network. Active UE namespaces are required when the verification script is executed.

---

## 8. Start the network and run verification

### Terminal 1 — Start the LTE network

For example, start three UEs:

```bash
cd /opt/oai-4g
bash /opt/oai-4g/run_multi_ue.sh 3
```

Wait until the requested UEs have attached and the deployment script returns control to the terminal.

### Terminal 2 — Activate Python environment and verify

```bash
source /opt/oai-4g/lte-tests/.venv/bin/activate
python /opt/oai-4g/lte-tests/verify_multi_ue.py
```

To require exactly three active UE namespaces:

```bash
python /opt/oai-4g/lte-tests/verify_multi_ue.py --expected-ues 3
```

To skip ICMP ping checks:

```bash
python /opt/oai-4g/lte-tests/verify_multi_ue.py --skip-ping
```

The verification script is intended to be non-destructive: it checks the running network and does not tear down the UE namespaces or radio stack.

### Stop the LTE network when finished

After completing experiments, stop the network using the deployment script:

```bash
bash /opt/oai-4g/run_multi_ue.sh stop
```

---

## 9. Where results are stored

Each verification run creates a timestamped directory:

```text
/opt/oai-4g/lte-tests/results/
└── run_YYYYMMDD_HHMMSS/
    ├── summary.json
    ├── kpi_plot.png
    ├── enb.log
    ├── mme.log
    ├── smf.log
    └── ue1.log ...
```

View the latest run:

```bash
latest_run=$(ls -td /opt/oai-4g/lte-tests/results/run_* 2>/dev/null | head -n 1)
echo "$latest_run"
```

View its KPI summary:

```bash
cat "$latest_run/summary.json"
```

The summary and plot are generated when KPI computation is reached. Log snapshots are collected in the script's `finally` block, but missing or inaccessible configured log files may affect artefact collection.

---

## 10. Troubleshooting

| Error or symptom | Recommended action |
|---|---|
| `python3: command not found` | Install Python using `sudo apt install python3`. |
| `No module named pip` | Install pip using `sudo apt install python3-pip`. |
| `No module named pandas` | Activate `.venv`, then run `python -m pip install pandas matplotlib`. |
| `externally-managed-environment` | Use the virtual-environment procedure in Section 5. |
| `Permission denied` when executing the script | Run `sudo chmod +x /opt/oai-4g/lte-tests/verify_multi_ue.py`. |
| Results directory is not writable | Check ownership and permissions using Section 4. |
| `No active ueX_ns namespaces found` | Start the LTE network using `run_multi_ue.sh` before running verification. |
| MME/SMF log read fails | Confirm the log paths and `sudo` access. |
| `ping: command not found` | Install `iputils-ping`. |
| Ping reports packet loss | Check UE routing, UPF connectivity, host forwarding/firewall rules, and external ICMP reachability. |
| Python syntax error around `str \| None` | Use Python 3.10 or later. |

---

## 11. Important implementation notes

1. `MAX_SETUP_MS_THRESHOLD` is defined in the configuration, but the supplied verification script does not currently enforce this threshold.
2. The MME timestamp parser currently prefixes timestamps with the year `2026`. Update the parser if the log year or timestamp format differs.
3. The script derives IMSIs from `BASE_IMSI_PREFIX` and `BASE_MSIN_START`. These values must match the subscriber configuration used by the LTE lab.
4. The script expects UE namespaces named `ue1_ns` through `ue6_ns`, a UE interface named `oaitun_ue1`, and UE IPv4 addresses in the `10.45.0.x` range. Adjust the code if your deployment uses different names or addressing.
5. The ping test uses `8.8.8.8` by default. ICMP traffic must be permitted and the target must be reachable from the UE data network for the ping assertion to pass.
6. The example terminal output in the lab guide is illustrative. Actual attach times, IP addresses, and RTT values depend on the deployment.

For the complete source code, refer to **`Day2_LTE_Verification_Code.md`**. For the detailed lab workflow and explanation of the checks, refer to **`Day2_Python_Verification_Lab_Guide.md`**.
