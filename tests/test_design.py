"""The design track's wording agrees across planning, readiness, the forms, and the skills; text, not behavior."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_planning_sets_design_depth_and_only_the_user_chooses_a_direction():
    planning, plan = prose("orchi/references/planning.md"), prose("orchi-plan/SKILL.md")
    for depth in ("| None |", "| Brief |", "| Epic |"):
        assert depth in planning
    assert "Plan a `design` Epic (labels `Epic` and `design`) for a designer crew" in planning
    assert "labelled `needs-planning`" in planning and "blocked by the design Epic" in planning
    assert "Only the user chooses a direction and approves a comp or a generated asset, at every autonomy level." in planning
    assert "planning.md#user-interface-design" in plan and "run `/impeccable shape` with the user now" in plan


def test_ui_readiness_items_have_form_fields():
    readiness = prose("orchi/references/readiness.md")
    assert readiness.count("planning.md#user-interface-design") == 2
    for form in ("orchi-task.yml", "orchi-epic.yml"):
        text = (SKILLS / "orchi/assets/github/ISSUE_TEMPLATE" / form).read_text()
        assert "id: ui" in text and "label: UI design" in text
