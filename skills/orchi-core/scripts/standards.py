#!/usr/bin/env python3
"""Check that ENGINEERING.md's declared checks run in CI, and that a change does not quietly weaken them."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime
import fnmatch
import json
from pathlib import Path
import re
import subprocess
import sys

DOCUMENT = "ENGINEERING.md"
WORKFLOWS = ".github/workflows"
BLOCKING = {"yes": 2, "weekly": 1, "no": 0}
THRESHOLD = re.compile(r"^(>=|<=)\s*(\d+(?:\.\d+)?)\s*%?$")
# Added lines that switch a check off for some code. Each pattern's name is the Rule an exception gives.
SUPPRESSIONS = {
    "eslint-disable": re.compile(r"eslint-disable"),
    "ts-ignore": re.compile(r"@ts-(?:ignore|expect-error|nocheck)"),
    "biome-ignore": re.compile(r"biome-ignore"),
    "prettier-ignore": re.compile(r"prettier-ignore"),
    "coverage-ignore": re.compile(r"(?:istanbul|c8|v8) ignore|pragma: no cover"),
    "noqa": re.compile(r"#\s*(?:ruff:\s*)?noqa"),
    "type-ignore": re.compile(r"#\s*(?:type|pyright|mypy):\s*ignore"),
    "fmt-off": re.compile(r"#\s*fmt:\s*(?:off|skip)"),
    "nosec": re.compile(r"#\s*nosec|nosemgrep|gitleaks:allow"),
    "test-skip": re.compile(r"\b(?:it|test|describe)\.(?:skip|only|todo|fixme)\b|\bx(?:it|describe|test)\(|"
                            r"pytest\.mark\.(?:skip|skipif|xfail)|pytest\.(?:skip|xfail)\(|@unittest\.skip"),
}
# Added lines in a declared configuration file that turn a rule off or widen what it ignores.
WEAKENING = re.compile(r"[\"'\s:=](?:off|warn|warning)[\"'\s,]|\b(?:ignores?|ignore_?\w*|excludes?|exclude_?\w*|skip\w*|"
                       r"disabled?|allow\w*|per-file-ignores|exempt)\b", re.I)
TEST_FILE = re.compile(r"(?:^|/)(?:tests?|__tests__|e2e|spec)/|(?:^|/)test_[^/]+\.py$|_test\.(?:py|go)$|"
                       r"\.(?:test|spec)\.[cm]?[jt]sx?$")
ASSERTION = re.compile(r"\bassert\w*\b|\bexpect\s*\(|\.should\b|\bself\.assert\w+\(")


@dataclass
class Finding:
    rule: str
    where: str
    detail: str

    def text(self) -> str:
        return f"{self.where}: {self.rule}: {self.detail}"


def cell(text: str) -> str:
    return text.strip().replace("`", "").strip()


def table(text: str, heading: str) -> list[dict[str, str]]:
    """The first Markdown table under `## <heading>`, as rows keyed by header."""
    section = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not section:
        return []
    lines = [line.strip() for line in section.group(1).splitlines()]
    rows = [line for line in lines if line.startswith("|")]
    if len(rows) < 2:
        return []
    header = [cell(part) for part in rows[0].strip("|").split("|")]
    result = []
    for line in rows[2:]:
        parts = [cell(part) for part in line.strip("|").split("|")]
        if any(parts):
            result.append(dict(zip(header, parts + [""] * (len(header) - len(parts)))))
    return result


def checks(text: str) -> list[dict[str, str]]:
    return table(text, "Checks")


def exceptions(text: str) -> list[dict[str, str]]:
    return table(text, "Exceptions")


def configs(row: dict[str, str]) -> list[str]:
    return [path.strip() for path in row.get("Config", "").split(",") if path.strip() not in {"", "-"}]


def normalize(text: str) -> str:
    return " ".join(text.split())


def workflow_jobs(root: Path) -> dict[str, dict]:
    """Jobs of every workflow: id -> its file, its text, its status check name, and whether the workflow is scheduled."""
    jobs: dict[str, dict] = {}
    folder = root / WORKFLOWS
    for path in sorted(folder.glob("*.y*ml")) if folder.is_dir() else []:
        lines = path.read_text(encoding="utf-8").splitlines()
        scheduled = any(re.match(r"^\s+schedule:", line) for line in lines)
        inside, indent, current = False, None, None
        for line in lines:
            if re.match(r"^jobs:\s*(#.*)?$", line):
                inside = True
                continue
            if inside and re.match(r"^\S", line):
                inside = False
            if not inside or not line.strip() or line.lstrip().startswith("#"):
                if current and inside:
                    jobs[current]["text"] += line + "\n"
                continue
            width = len(line) - len(line.lstrip())
            indent = width if indent is None else indent
            match = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(#.*)?$", line)
            if width == indent and match:
                current = match.group(1)
                jobs[current] = {"file": path.relative_to(root).as_posix(), "text": "", "name": current,
                                 "scheduled": scheduled}
            elif current:
                jobs[current]["text"] += line + "\n"
                named = re.match(r"^\s+name:\s*['\"]?(.+?)['\"]?\s*$", line)
                if named and width == indent + 2:
                    jobs[current]["name"] = named.group(1)
    return jobs


def expiry(row: dict[str, str]) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(row.get("Expires", ""))
    except ValueError:
        return None


def check(root: Path, today: datetime.date) -> dict:
    document = root / DOCUMENT
    if not document.is_file():
        return {"ok": True, "findings": [], "note": f"No {DOCUMENT}; nothing to check."}
    text = document.read_text(encoding="utf-8")
    rows, jobs, findings = checks(text), workflow_jobs(root), []
    if not rows:
        findings.append(Finding("checks", DOCUMENT, "no Checks table"))
    for row in rows:
        name, job, command = row.get("Check", ""), row.get("CI job", ""), normalize(row.get("Command", ""))
        blocking, threshold = row.get("Blocking", "").lower(), row.get("Threshold", "-")
        if blocking not in BLOCKING:
            findings.append(Finding("checks", DOCUMENT, f"{name}: Blocking must be yes, no, or weekly"))
        if threshold != "-" and not THRESHOLD.match(threshold):
            findings.append(Finding("checks", DOCUMENT, f"{name}: Threshold must be - or >= or <= a number"))
        if job not in jobs:
            findings.append(Finding("checks", DOCUMENT, f"{name}: no CI job `{job}` in {WORKFLOWS}/"))
        else:
            if command and command not in normalize(jobs[job]["text"]):
                findings.append(Finding("checks", jobs[job]["file"], f"{name}: job `{job}` does not run `{command}`"))
            if blocking == "weekly" and not jobs[job]["scheduled"]:
                findings.append(Finding("checks", jobs[job]["file"], f"{name}: job `{job}` is not scheduled"))
        for path in configs(row):
            if not (root / path).is_file():
                findings.append(Finding("checks", path, f"{name}: configuration file is not committed"))
    for row in exceptions(text):
        date = expiry(row)
        if date is None:
            findings.append(Finding("exceptions", row.get("Where", ""), f"{row.get('Rule', '')}: Expires is not a date"))
        elif date < today:
            findings.append(Finding("exceptions", row.get("Where", ""), f"{row.get('Rule', '')}: expired on {date}"))
    return {"ok": not findings, "findings": [f.text() for f in findings]}


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def base_document(root: Path, base: str) -> str | None:
    try:
        return git(root, "show", f"{base}:{DOCUMENT}")
    except subprocess.CalledProcessError:
        return None


@dataclass
class FileDiff:
    path: str
    deleted: bool = False
    created: bool = False
    added: list[str] | None = None
    removed: list[str] | None = None


def diff(root: Path, base: str) -> list[FileDiff]:
    text = git(root, "diff", "--unified=0", "--find-renames", f"{base}...HEAD")
    files: list[FileDiff] = []
    for line in text.splitlines():
        if line.startswith("diff --git "):
            files.append(FileDiff(line.split(" b/", 1)[-1], added=[], removed=[]))
        elif not files:
            continue
        elif line.startswith("deleted file mode"):
            files[-1].deleted = True
        elif line.startswith("new file mode"):
            files[-1].created = True
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("+"):
            files[-1].added.append(line[1:])
        elif line.startswith("-"):
            files[-1].removed.append(line[1:])
    return files


def threshold(value: str) -> tuple[str, float] | None:
    match = THRESHOLD.match(value or "")
    return (match.group(1), float(match.group(2))) if match else None


def loosened(old: str, new: str) -> bool:
    before, after = threshold(old), threshold(new)
    if before is None:
        return False
    if after is None or after[0] != before[0]:
        return True
    return after[1] < before[1] if before[0] == ">=" else after[1] > before[1]


def stem(path: str) -> str:
    name = Path(path).name
    name = re.sub(r"^test_|_test(?=\.)|\.(?:test|spec)(?=\.)", "", name)
    return name.split(".", 1)[0]


def gate_findings(base_text: str | None, head_text: str, files: list[FileDiff]) -> list[Finding]:
    findings: list[Finding] = []
    head_rows = {row.get("Check", ""): row for row in checks(head_text)}
    declared = {path for row in head_rows.values() for path in configs(row)}
    for name, old in ({row.get("Check", ""): row for row in checks(base_text)} if base_text else {}).items():
        new = head_rows.get(name)
        if new is None:
            findings.append(Finding("check removed", DOCUMENT, name))
            continue
        if BLOCKING.get(new.get("Blocking", "").lower(), 0) < BLOCKING.get(old.get("Blocking", "").lower(), 0):
            findings.append(Finding("non-blocking", DOCUMENT, f"{name}: {old.get('Blocking')} -> {new.get('Blocking')}"))
        if loosened(old.get("Threshold", "-"), new.get("Threshold", "-")):
            findings.append(Finding("threshold", DOCUMENT, f"{name}: {old.get('Threshold')} -> {new.get('Threshold')}"))
    deleted = {item.path for item in files if item.deleted}
    for item in files:
        if item.deleted:
            source_gone = any(stem(other) == stem(item.path) and not TEST_FILE.search(other) for other in deleted)
            if TEST_FILE.search(item.path) and not source_gone:
                findings.append(Finding("test deleted", item.path, "test file deleted without the code it covers"))
            continue
        if item.path.endswith(".md"):
            continue
        for line in item.added:
            for kind, pattern in SUPPRESSIONS.items():
                if pattern.search(line):
                    findings.append(Finding(kind, item.path, line.strip()))
        if item.path in declared and not item.created and base_text:
            findings += [Finding("config", item.path, line.strip()) for line in item.added if WEAKENING.search(line)]
        if TEST_FILE.search(item.path):
            lost = sum(bool(ASSERTION.search(line)) for line in item.removed) - sum(
                bool(ASSERTION.search(line)) for line in item.added)
            if lost > 0:
                findings.append(Finding("assertions removed", item.path, f"{lost} fewer assertions"))
    return findings


def covered(finding: Finding, waivers: list[dict[str, str]]) -> bool:
    for row in waivers:
        where, rule = row.get("Where", ""), row.get("Rule", "").lower()
        subject = finding.detail.split(":", 1)[0]
        if not (fnmatch.fnmatch(finding.where, where) or where == subject):
            continue
        if rule and (rule == finding.rule or rule in finding.detail.lower()):
            return True
    return False


def ratchet(root: Path, base: str) -> dict:
    document = root / DOCUMENT
    if not document.is_file():
        return {"ok": True, "findings": [], "exceptions": [], "note": f"No {DOCUMENT}; nothing to check."}
    head_text = document.read_text(encoding="utf-8")
    base_text = base_document(root, base)
    waivers = exceptions(head_text)
    found = [f for f in gate_findings(base_text, head_text, diff(root, base)) if not covered(f, waivers)]
    before = {tuple(sorted(row.items())) for row in exceptions(base_text or "")}
    changed = [row for row in waivers if tuple(sorted(row.items())) not in before]
    return {"ok": not found, "findings": [f.text() for f in found],
            "exceptions": [f"{row.get('Rule')} in {row.get('Where')} until {row.get('Expires')}: {row.get('Reason')}"
                           for row in changed]}


def ruleset(root: Path) -> dict:
    """A GitHub ruleset for the default branch that requires every blocking check."""
    document = root / DOCUMENT
    if not document.is_file():
        raise ValueError(f"No {DOCUMENT}")
    jobs = workflow_jobs(root)
    contexts = sorted({jobs[row["CI job"]]["name"] if row.get("CI job") in jobs else row.get("CI job", "")
                       for row in checks(document.read_text(encoding="utf-8"))
                       if row.get("Blocking", "").lower() == "yes" and row.get("CI job")})
    return {
        "name": "Orchi standards",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_linear_history"},
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 0, "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False, "require_last_push_approval": False,
                "required_review_thread_resolution": False, "allowed_merge_methods": ["squash"]}},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": False,
                "required_status_checks": [{"context": context} for context in contexts]}},
        ],
    }


def report(result: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("note"):
            print(result["note"])
        for line in result["findings"]:
            print(line)
        for line in result.get("exceptions", []):
            print("Exception: " + line)
        if result["ok"] and not result.get("note"):
            print("ok")
    return 0 if result["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    commands = parser.add_subparsers(dest="command", required=True)
    checked = commands.add_parser("check", help="Every declared check runs in CI, and no exception has expired")
    checked.add_argument("--today", type=datetime.date.fromisoformat, default=datetime.date.today(),
                         help=argparse.SUPPRESS)
    ratcheted = commands.add_parser("ratchet", help="The changes since --base weaken no check without an exception")
    ratcheted.add_argument("--base", required=True, help="Base commit or ref of the change")
    commands.add_parser("ruleset", help="Print the GitHub ruleset that requires every blocking check")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "check":
            return report(check(root, args.today), args.json)
        if args.command == "ratchet":
            return report(ratchet(root, args.base), args.json)
        print(json.dumps(ruleset(root), indent=2))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"standards.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
