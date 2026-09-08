"""Synthetic process fixture. Not a production model adapter or model-quality evaluation."""
import json
import os
from pathlib import Path
import time
import sys

p = json.loads(Path(os.environ["ORCHI_PACKET"]).read_text())
out = Path(os.environ["ORCHI_OUTPUT"])
phase = os.environ["ORCHI_PHASE"]
if phase == "prepare":
    value = {"packet_fingerprint": p["fingerprint"], "understood_goal": p["task"]["goal"],
             "fixed_decisions": p["task"]["decisions"], "acceptance_ids": list(p["task"]["acceptance"]), "questions": []}
else:
    start = time.time()
    if "--parallel-barrier" in sys.argv:
        barrier = Path(sys.argv[sys.argv.index("--parallel-barrier") + 1])
        barrier.mkdir(parents=True, exist_ok=True)
        (barrier / p["task"]["id"]).touch()
        deadline = time.monotonic() + 15
        while len(list(barrier.iterdir())) < 2:
            if time.monotonic() >= deadline:
                raise RuntimeError("Independent workers did not execute concurrently")
            time.sleep(0.02)
        time.sleep(0.1)
    else:
        time.sleep(0.35)
    tid = p["task"]["id"]
    values = {"left": ("src/left.py", "VALUE = 1\n"), "right": ("src/right.py", "VALUE = 2\n"), "api": ("src/api.py", "ANSWER = 3\n")}
    name, content = values[tid]
    Path(name).write_text(content)
    (out.parent / "timing.json").write_text(json.dumps({"start": start, "end": time.time()}))
    value = {"status": "completed", "summary": "Synthetic worker applied the planned edit", "extra_reads": [], "deviations": []}
out.write_text(json.dumps(value))
