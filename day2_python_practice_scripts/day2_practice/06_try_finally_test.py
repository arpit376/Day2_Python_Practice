"""Exercise 6 - A complete mini test: setup, check, always clean up, write a result."""
import json, re
from pathlib import Path

def collect_artefacts():
    print("  [finally] collecting logs...")

def teardown():
    print("  [finally] stopping processes, lab left clean")

def run_test(imsi, expect_success):
    result = {"test": "attach_" + imsi[-3:], "status": "FAIL", "reason": ""}
    try:
        print("Provision subscriber", imsi)
        log = Path("sample_mme.log").read_text()
        completed = re.search(rf"Attach Complete imsi={imsi}", log) is not None
        assert completed == expect_success, f"attach outcome was {completed}, expected {expect_success}"
        result["status"] = "PASS"
    except AssertionError as e:
        result["reason"] = str(e)
    finally:
        collect_artefacts()
        teardown()
    return result

results = [run_test("001010123456001", True),    # should pass
           run_test("001010123456003", True)]    # attach was rejected -> fails
Path("summary.json").write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))

# TRY: make the second test pass by changing what you expect. Does finally still run?
