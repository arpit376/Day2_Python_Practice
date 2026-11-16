"""Exercise 2 - Pull fields out of a log line with a regular expression."""
import re
from pathlib import Path

PATTERN = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[MME\] "
    r"NAS (?P<msg>Attach \w+) imsi=(?P<imsi>\d{15})"
)

for line in Path("sample_mme.log").read_text().splitlines():
    m = PATTERN.match(line)
    if m:
        print(m.group("imsi"), "|", m.group("msg"), "|", m.group("ts"))

# TRY: also capture emm_cause=8 when it is present (hint: (?: emm_cause=(?P<cause>\d+))?)
