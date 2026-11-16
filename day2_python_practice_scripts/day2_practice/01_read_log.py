"""Exercise 1 - Read a log file and count lines.
Idea of the day: a test starts by reading what the network wrote."""
from pathlib import Path

lines = Path("sample_mme.log").read_text().splitlines()
print("Total lines:", len(lines))

attach_requests = [l for l in lines if "Attach Request" in l]
print("Attach Requests:", len(attach_requests))
print("First line:", lines[0])

# TRY: count the lines that contain 'Reject'. Then count 'WARN'.
