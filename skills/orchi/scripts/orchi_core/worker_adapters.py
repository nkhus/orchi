"""Provider command construction and strict output normalization; no workflow authority."""
from __future__ import annotations

import json
from pathlib import Path

from .agents import AGENTS
from .common import require


def invocation(adapter: dict, phase: str, task_text: str, schema: dict,
               schema_path: Path, output: Path, input_dir: Path) -> tuple[list[str], bytes]:
    kind = adapter["kind"]
    executable = adapter.get("executable", AGENTS[kind]["executable"])
    prepare = phase == "prepare"
    prompt = (
        "You are an assigned Orchi packet worker, not a coordinator. Do not invoke Orchi setup, claim, run, or operator commands.\n"
        + ("Read the exact task packet. Do not edit files or run commands. Return readiness with its exact fingerprint, "
           "fixed decisions and acceptance IDs. Describe the goal in your own words; report substantive questions instead of guessing.\n"
           if prepare else
           "Implement the exact task in this checkout. Preparation has passed. Do not commit or edit Core docs/proposals. "
           "Use only delegated local choices. Run assigned checks. Report all additional reads and deviations. "
           "If required tools or permissions are unavailable, return blocked; do not report unperformed work as completed.\n")
        + "Follow relevant repository instructions, subject to the packet worker role above.\n"
        + task_text
    )
    if kind == "codex":
        argv = [executable, "--ask-for-approval", "never", "exec", "--sandbox",
                "read-only" if prepare else "workspace-write", "--ephemeral", "--json",
                "--output-schema", str(schema_path), "-o", str(output)]
    elif kind == "claude":
        tools = "Read,Glob,Grep" if prepare else "Read,Glob,Grep,Edit,Write,Bash"
        allowed = ["Read", "Glob", "Grep"] if prepare else adapter.get("allowed_tools", ["Read", "Glob", "Grep", "Edit", "Write"])
        argv = [executable, "-p", "--output-format", "json", "--json-schema", json.dumps(schema),
                "--no-session-persistence", "--permission-mode", "dontAsk", "--tools", tools,
                "--allowedTools", ",".join(allowed), "--disable-slash-commands",
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--add-dir", str(input_dir)]
    else:
        tools = "view,glob,grep" if prepare else "view,glob,grep,edit,create,apply_patch,bash,read_bash,list_bash,stop_bash,write_bash"
        allowed = ["read"] if prepare else adapter.get("allowed_tools", ["read", "write"])
        # Piped stdin invokes noninteractive mode without putting the task packet in argv.
        # Silent text output avoids mistaking provider JSONL events for Orchi's JSON result.
        argv = [executable, "--output-format", "text", "--silent", "--stream", "off",
                "--no-ask-user", "--no-auto-update", "--disable-builtin-mcps",
                "--available-tools", tools, "--allow-tool", ",".join(allowed),
                "--add-dir", str(input_dir)]
        if prepare:
            argv += ["--deny-tool", "write,shell"]
        prompt += "\nReturn exactly one JSON object, without Markdown or commentary, matching this JSON Schema:\n" + json.dumps(schema)
    if adapter.get("model"):
        argv += ["--model", adapter["model"]]
    if kind == "codex":
        argv.append("-")
    return argv, prompt.encode()


def structured_result(kind: str, stdout: str) -> dict:
    try:
        result = json.loads(stdout)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{kind} did not return one JSON result; inspect the worker observation") from exc
    require(isinstance(result, dict), "INVALID_WORKER_RESULT", "Expected a JSON object")
    if kind == "claude":
        require(result.get("type") == "result" and result.get("subtype") == "success" and result.get("is_error") is False,
                "WORKER_MODEL_FAILED", "Claude reported an error or incomplete turn; inspect the worker observation")
        result = result.get("structured_output")
        require(isinstance(result, dict), "INVALID_WORKER_RESULT", "Claude omitted structured_output")
    return result
