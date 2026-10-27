"""Shared fixtures: a fake Node.js and npx, so installations never reach npm."""
import os
import shutil
from pathlib import Path

import pytest

# Answers `node --version` and passes everything else, such as npm's own scripts, to the real node.
FAKE_NODE = """#!/bin/sh
if [ "$#" = 1 ] && [ "$1" = "--version" ]; then echo "${FAKE_NODE_VERSION:-v22.18.0}"; exit 0; fi
[ -n "$REAL_NODE" ] && exec "$REAL_NODE" "$@"
exit 127
"""

# Emulates `npx --yes impeccable@<version> install ...`: writes the skill and one agent into the current
# directory (Orchi runs it from the installation root) and logs the arguments.
FAKE_NPX = """#!/bin/sh
echo "$@" >> "$FAKE_NPX_LOG"
[ -n "$FAKE_NPX_FAIL" ] && { echo "$FAKE_NPX_FAIL" >&2; exit 1; }
version=""
for arg in "$@"; do
  case "$arg" in impeccable@*) version="${arg#impeccable@}" ;; esac
done
mkdir -p .claude/skills/impeccable .claude/agents
printf -- '---\\nname: impeccable\\nversion: %s\\n---\\nFake Impeccable\\n' "$version" > .claude/skills/impeccable/SKILL.md
printf -- '---\\nname: impeccable-documenter\\n---\\n' > .claude/agents/impeccable-documenter.md
"""


@pytest.fixture(autouse=True)
def fake_node(tmp_path_factory, monkeypatch):
    """Put a fake node and npx first on PATH; the returned log lists each npx call."""
    bin_dir = tmp_path_factory.mktemp("fake-bin")
    for name, script in (("node", FAKE_NODE), ("npx", FAKE_NPX)):
        path = bin_dir / name
        path.write_text(script)
        path.chmod(0o755)
    monkeypatch.setenv("REAL_NODE", shutil.which("node") or "")
    log = bin_dir / "npx.log"
    log.touch()
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    monkeypatch.setenv("FAKE_NPX_LOG", str(log))
    monkeypatch.delenv("FAKE_NPX_FAIL", raising=False)
    monkeypatch.delenv("FAKE_NODE_VERSION", raising=False)
    return log


def npx_calls(log: Path) -> list[str]:
    return [line for line in log.read_text().splitlines() if line]
