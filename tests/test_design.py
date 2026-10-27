"""The design track's wording agrees across planning, readiness, the forms, and the skills; text, not behavior."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_planning_sets_design_depth_and_only_the_user_chooses_a_direction():
    planning, plan = prose("orchi-core/references/planning.md"), prose("orchi-plan/SKILL.md")
    for depth in ("| None |", "| Brief |", "| Epic |"):
        assert depth in planning
    assert "Plan a standalone `design` Epic (labels `Epic` and `design`) for a designer crew, outside any Initiative" in planning
    assert "labelled `needs-planning`" in planning and "blocked by the design Epic" in planning
    assert "Only the user chooses a direction and approves a comp or a generated asset, at every autonomy level." in planning
    assert "planning.md#user-interface-design" in plan and "run `/impeccable shape` with the user now" in plan


def test_ui_readiness_items_have_form_fields():
    readiness = prose("orchi-core/references/readiness.md")
    assert readiness.count("planning.md#user-interface-design") == 2
    for form in ("orchi-task.yml", "orchi-epic.yml"):
        text = (SKILLS / "orchi-core/assets/github/ISSUE_TEMPLATE" / form).read_text()
        assert "id: ui" in text and "label: UI design" in text


def test_designer_crew_role_routing_and_mode_agree():
    pool, entry, design = prose("orchi-core/references/pool.md"), prose("orchi/SKILL.md"), prose("orchi-design/SKILL.md")
    assert "| Designer | `orchi-design` | One standalone `design` Epic, with the user |" in pool
    assert '"Take #n" on a `delivery-ready` Epic labelled `design` | Designer | `orchi-design`' in pool
    assert "the user still answers a researcher and a designer" in pool
    assert "an autonomy level never chooses a direction or approves a comp" in pool
    assert "A `design` Epic stays standalone" in pool
    assert "(researcher, planner, designer, dev lead)" in entry and "for a researcher or designer, and for a question marked `(user)`" in entry
    assert "Only the user chooses a direction and approves a comp or a generated asset, at every autonomy level" in design
    assert "you never pick for them" in design and "Continue with [orchi-deliver](../orchi-deliver/SKILL.md)" in design
    assert "Ask the user directly in both modes" in design and "Adopt Orchi's claim" in design
    assert "asks for orchi-design by name" in design


def test_exploration_records_product_truth_for_init():
    exploration, design = prose("orchi-core/references/exploration.md"), prose("orchi-design/SKILL.md")
    assert "| Product | For a product with a user interface" in exploration
    assert "The first design Epic's `init` writes `PRODUCT.md` from it and asks only what is missing." in exploration
    assert "How screens should look is not settled here" in exploration
    assert "id: product" in (SKILLS / "orchi-core/assets/github/ISSUE_TEMPLATE/orchi-exploration.yml").read_text()
    assert "starting from the Product section of the Exploration" in design


def test_delivery_routes_ui_tasks_to_the_designer_and_audits_ui_changes():
    readme = " ".join((SKILLS / "orchi-core/roles/README.md").read_text().split())
    review, deliver = prose("orchi-core/references/review-delivery.md"), prose("orchi-deliver/SKILL.md")
    assert "every Task that builds against a surface brief or an approved comp" in readme
    assert "a direction, a comp, or a generated asset goes to the user whatever they delegated" in readme
    assert "start `orchi-designer` in Audit mode on it beside the reviewer" in review
    assert "`orchi-designer` in Audit mode" in deliver


def test_design_outputs_that_bind_later_work_pass_the_user():
    designer, readme = prose("orchi-core/roles/orchi-designer.md"), " ".join((SKILLS / "orchi-core/roles/README.md").read_text().split())
    design, planning = prose("orchi-design/SKILL.md"), prose("orchi-core/references/planning.md")
    assert "Never write or replace `DESIGN.md`" in designer
    assert "commit a produced asset only when the Issue links that asset as approved" in designer
    assert "fix every primary finding, because the design workflow fails on one" in designer
    assert "the `DESIGN.md` sections it follows when `DESIGN.md` exists" in designer
    assert "**Recheck (Audit mode):**" in designer
    assert "write or replace `DESIGN.md` from the built surfaces with the user (`/impeccable document`)" in design
    assert "`git add -f` for both" in design
    assert "`impeccable-documenter` serves `document`, which runs with the user" in readme
    assert "Commit the brief on the work's branch, which planning creates now" in planning
    assert "In auto mode, Orchi may answer `shape` questions" not in planning
    assert "the branch of work at design depth brief" in prose("orchi-plan/SKILL.md")
    assert "for a `decision` `ESCALATE`" in prose("orchi-work/SKILL.md")
    assert "surface briefs and approved comps in `.impeccable/surfaces/`" in prose("orchi-core/references/knowledge.md")
