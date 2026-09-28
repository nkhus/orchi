"""The shipped issue forms are valid and give every readiness checklist item a field."""
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "skills/orchi/assets/github/ISSUE_TEMPLATE"
READINESS = ROOT / "skills/orchi/references/readiness.md"
FIELD_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes"}

# Checklist item number -> (field id, phrase the field's label or description must contain).
TASK_FIELDS = {
    1: ("outcome", "reviewable result"),
    2: ("purpose", "consume"),
    3: ("prerequisites", '"none"'),
    4: ("outcome", "native sub-issue"),
    5: ("sources", "inspected while planning"),
    6: ("surfaces", "routes, migrations, tables"),
    7: ("constraints", "non-goals"),
    8: ("scenarios", "failure scenarios"),
    9: ("acceptance", "exact checks or commands"),
    10: ("docs", "documentation routing"),
    11: ("questions", "affects this task's approach"),
}
EPIC_FIELDS = {
    1: ("scope", "out of scope"),
    2: ("sources", "requirement/decision ids"),
    3: ("current", "files, symbols, behavior"),
    4: ("design", "no architecture change"),
    5: ("surfaces", "documentation"),
    6: ("failure", "inputs and outputs, risks"),
    7: ("branch", "blocked-by"),
    8: ("exit", "mapped to requirements"),
    9: ("questions", "affects the approach"),
    10: ("branch", "tasks in execution order as native sub-issues"),
}


def load(name):
    return yaml.safe_load((TEMPLATES / f"orchi-{name}.yml").read_text())


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
])
def test_every_readiness_item_has_a_template_field(name, title, mapping):
    assert checklist(title) == sorted(mapping), "update the mapping when the checklist changes"
    fields = {item["id"]: item for item in load(name)["body"] if item["type"] != "markdown"}
    for number, (field, phrase) in mapping.items():
        attributes = fields[field]["attributes"]
        text = (attributes["label"] + " " + attributes.get("description", "")).casefold()
        assert phrase in text, f"{title} item {number} is not covered by field {field}"


def test_templates_point_to_the_readiness_reference():
    assert "Task readiness checklist in Orchi's readiness reference" in load("task")["body"][0]["attributes"]["value"]
    intro = load("epic")["body"][0]["attributes"]["value"]
    assert "Epic readiness checklist in Orchi's readiness reference" in intro and "Deferred until #<n>" in intro
