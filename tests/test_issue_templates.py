"""The shipped issue forms are valid and give every readiness checklist item a field."""
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "skills/orchi/assets/github/ISSUE_TEMPLATE"
READINESS = ROOT / "skills/orchi/references/readiness.md"
FIELD_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes"}

# Checklist item number -> (field id, phrases the field's label or description must contain).
TASK_FIELDS = {
    1: ("outcome", ("reviewable result",)),
    2: ("context", ("current behavior", "path:line", "consume")),
    3: ("prerequisites", ('"none"',)),
    4: ("outcome", ("native sub-issue",)),
    5: ("requirements", ("numbered requirements", "individually verifiable")),
    6: ("vision", ("routes, migrations, tables", "why this approach")),
    7: ("decisions", ("who decided", "quote the user's answers")),
    8: ("sources", ("inspected while planning",)),
    9: ("constraints", ("non-goals",)),
    10: ("scenarios", ("failure scenarios", "reproduction command")),
    11: ("acceptance", ("mapped to the requirements", "exact checks or commands", "seams where new tests go")),
    12: ("docs", ("documentation routing",)),
    13: ("questions", ("affects this task's approach",)),
}
EPIC_FIELDS = {
    1: ("scope", ("out of scope",)),
    2: ("sources", ("requirement/decision ids", "parent initiative")),
    3: ("current", ("why this outcome is needed", "files, symbols, behavior")),
    4: ("requirements", ("numbered requirements", "traceable")),
    5: ("design", ("no architecture change", "why this approach", "test seams")),
    6: ("decisions", ("who decided", "quote the user's answers")),
    7: ("surfaces", ("documentation",)),
    8: ("failure", ("inputs and outputs, risks",)),
    9: ("branch", ("blocked-by",)),
    10: ("exit", ("mapped to requirements", "verification")),
    11: ("questions", ("affects the approach",)),
    12: ("branch", ("tasks in execution order as native sub-issues",)),
}
INITIATIVE_FIELDS = {
    1: ("request", ("distinct from later decisions",)),
    2: ("outcome", ("exclusions",)),
    3: ("requirements", ("numbered requirements", "observable at completion")),
    4: ("decisions", ("who decided", "quote the user's answers")),
    5: ("epics", ("delivers each requirement", "dependency between epics")),
    6: ("completion", ("integration branch", "final verification")),
    7: ("plan", ("docs/initiatives/",)),
}

def load(name):
    return yaml.safe_load((TEMPLATES / f"orchi-{name}.yml").read_text())


def flat(text):
    """Collapse whitespace so rewrapped template prose still matches."""
    return " ".join(text.split())


def checklist(title):
    section = READINESS.read_text().split(f"## {title}\n", 1)[1].split("\n## ", 1)[0]
    return [int(number) for number in re.findall(r"^(\d+)\. ", section, flags=re.M)]


@pytest.mark.parametrize("name, label", [("task", "Task"), ("epic", "Epic"), ("initiative", "Initiative")])
def test_templates_are_valid_issue_forms(name, label):
    form = load(name)
    assert form["name"] == f"Orchi {label}" and form["description"] and form["labels"] == [label]
    ids = [item["id"] for item in form["body"] if item["type"] != "markdown"]
    assert len(ids) == len(set(ids))
    for item in form["body"]:
        assert item["type"] in FIELD_TYPES
        assert item["type"] == "markdown" or item["attributes"]["label"]
    text = (TEMPLATES / f"orchi-{name}.yml").read_text()
    assert ".github/AGENTS.md" not in text and "docs/system" not in text


@pytest.mark.parametrize("name, title, mapping", [
    ("task", "Task readiness checklist", TASK_FIELDS),
    ("epic", "Epic readiness checklist", EPIC_FIELDS),
    ("initiative", "Initiative readiness checklist", INITIATIVE_FIELDS),
])
def test_every_readiness_item_has_a_template_field(name, title, mapping):
    assert checklist(title) == sorted(mapping), "update the mapping when the checklist changes"
    fields = {item["id"]: item for item in load(name)["body"] if item["type"] != "markdown"}
    for number, (field, phrases) in mapping.items():
        attributes = fields[field]["attributes"]
        text = flat(attributes["label"] + " " + attributes.get("description", "")).casefold()
        for phrase in phrases:
            assert phrase in text, f"{title} item {number} is not covered by field {field}: {phrase!r}"


def test_templates_point_to_the_readiness_reference():
    assert "Task readiness checklist in Orchi's readiness reference" in flat(load("task")["body"][0]["attributes"]["value"])
    intro = flat(load("epic")["body"][0]["attributes"]["value"])
    assert "Epic readiness checklist in Orchi's readiness reference" in intro and "Deferred until #<n>" in intro
    assert "Initiative readiness checklist in Orchi's readiness reference" in flat(
        load("initiative")["body"][0]["attributes"]["value"])


@pytest.mark.parametrize("name", ["task", "epic", "initiative"])
def test_templates_address_agent_owners(name):
    intro = flat(load(name)["body"][0]["attributes"]["value"])
    assert "agent owner" in intro and "planning conversation" in intro
