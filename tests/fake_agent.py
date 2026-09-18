"""Synthetic process fixture. Not a production model adapter or model-quality evaluation."""
import json
import os
from pathlib import Path
import time

p = json.loads(Path(os.environ["ORCHI_PACKET"]).read_text())
out = Path(os.environ["ORCHI_OUTPUT"])
phase = os.environ["ORCHI_PHASE"]
if phase == "prepare":
    value = {"packet_fingerprint": p["fingerprint"], "understood_goal": p["task"]["goal"],
             "fixed_decisions": p["task"]["decisions"], "acceptance_ids": list(p["task"]["acceptance"]), "questions": []}
else:
    start = time.time()
    time.sleep(0.35)
    tid = p["task"]["id"]
    values = {"left": ("src/left.py", "VALUE = 1\n"), "right": ("src/right.py", "VALUE = 2\n"), "api": ("src/api.py", "ANSWER = 3\n")}
    name, content = values[tid]
    Path(name).write_text(content)
    (out.parent / "timing.json").write_text(json.dumps({"start": start, "end": time.time()}))
    value = {"status": "completed", "summary": "Synthetic worker applied the planned edit", "extra_reads": [], "deviations": []}
out.write_text(json.dumps(value))
