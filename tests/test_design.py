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


def test_designer_crew_role_routing_and_mode_agree():
    pool, entry, design = prose("orchi/references/pool.md"), prose("orchi-pm/SKILL.md"), prose("orchi-design/SKILL.md")
    assert "| Designer | `orchi-design` | One standalone `design` Epic, with the user |" in pool
    assert '"Take #n" on a `delivery-ready` Epic labelled `design` | Designer | `orchi-design`' in pool
    assert "the user still answers a researcher and a designer" in pool
    assert "an autonomy level never chooses a direction or approves a comp" in pool
    assert "A `design` Epic stays standalone" in pool
    assert "(researcher, planner, designer, dev lead)" in entry and "for a researcher or designer in any mode" in entry
    assert "Only the user chooses a direction and approves a comp or a generated asset, at every autonomy level" in design
    assert "you never pick for them" in design and "Continue with [orchi-deliver](../orchi-deliver/SKILL.md)" in design
    assert "Ask the user directly in both modes" in design and "adopt Orchi's claim" in design
    assert "asks for orchi-design by name" in design
