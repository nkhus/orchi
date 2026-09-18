"""Deterministic CLI protocol fixture. Never launches a model or supplies real approval."""
import json
import os
from pathlib import Path
import sys

prompt = sys.stdin.read()
assert "assigned Orchi packet worker" in prompt
packet = json.loads(Path(os.environ["ORCHI_PACKET"]).read_text())
phase = os.environ["ORCHI_PHASE"]
provider = os.environ["ORCHI_TEST_PROVIDER"]
failure = os.environ.get("ORCHI_TEST_FAILURE")
output = Path(os.environ["ORCHI_OUTPUT"])
(output.parent / (phase + ".argv.json")).write_text(json.dumps(sys.argv[1:]))
if failure == "process":
    sys.exit(1)
if phase == "prepare":
    value = {"packet_fingerprint": packet["fingerprint"], "understood_goal": packet["task"]["goal"],
             "fixed_decisions": packet["task"]["decisions"], "acceptance_ids": list(packet["task"]["acceptance"]), "questions": []}
    if failure == "write-in-prepare":
        Path("src/left.py").write_text("VALUE = 999\n")
    if failure == "fingerprint":
        value["packet_fingerprint"] = "wrong"
    if failure == "questions":
        value["questions"] = ["An essential decision is missing"]
else:
    target, content = {"left": ("src/left.py", "VALUE = 1\n"), "right": ("src/right.py", "VALUE = 2\n")}[packet["task"]["id"]]
    Path(target).write_text(content)
    value = {"status": "completed", "summary": "Synthetic planned edit", "extra_reads": [], "deviations": []}
if failure == "schema":
    value = {"status": "completed"}
if provider == "codex":
    output.write_text(json.dumps(value))
elif failure == "text":
    print("Finished successfully!")
elif provider == "claude":
    print(json.dumps({"type": "result", "subtype": "error_max_turns" if failure == "model" else "success",
                      "is_error": failure == "model", "structured_output": value}))
else:
    print(json.dumps(value))
