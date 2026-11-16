"""Exercise 4 - Run a command from Python, like starting a core or eNodeB."""
import subprocess, sys

result = subprocess.run(
    [sys.executable, "-c", "print('core started'); print('listening on S1-MME')"],
    capture_output=True, text=True, timeout=10,
)
print("Return code:", result.returncode)
print("Output     :", result.stdout.strip())

bad = subprocess.run([sys.executable, "-c", "raise SystemExit(3)"], capture_output=True, text=True)
print("Failing command return code:", bad.returncode, "(non-zero means failure)")

try:
    subprocess.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)
except subprocess.TimeoutExpired:
    print("Timeout caught - a hung process must never hang the whole test run")

# TRY: replace the command with ['ls'] (or ['dir'] on Windows) and print the output.
