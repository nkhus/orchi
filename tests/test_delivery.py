"""Delivery course corrections and verification verdicts agree across the skills, roles, and templates."""
from pathlib import Path

from orchi_core import installation

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
WRITERS = ("orchi-implementer", "orchi-fixer", "orchi-designer")


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_writers_are_continued_instead_of_restarted():
    deliver, roles = prose("orchi-deliver/SKILL.md"), prose("orchi-core/roles/README.md")
    assert "## Continue a writer" in (SKILLS / "orchi-core/roles/README.md").read_text()
    assert "with `SendMessage` to the agent ID its start returned" in roles
    assert deliver.count("(../orchi-core/roles/README.md#continue-a-writer)") == 3
    assert "restart that writer" not in deliver and "restarting its writer" not in deliver
    for writer in WRITERS:
        text = prose(f"orchi-core/roles/{writer}.md")
        assert "When continued" in text and "the new work is one more commit" in text


def test_two_misses_change_course_and_initiatives_step_back():
    deliver, execution = prose("orchi-deliver/SKILL.md"), prose("orchi-core/references/execution.md")
    assert "do not send it a longer version of the same brief" in execution
    assert deliver.count("(../orchi-core/references/execution.md#change-course)") == 3
    assert "## Step back between Epics" in (SKILLS / "orchi-core/references/review-delivery.md").read_text()
    assert "[step back](../orchi-core/references/review-delivery.md#step-back-between-epics), then reclassify" in deliver


def test_declined_work_is_checked_before_proposing():
    planning = prose("orchi-core/references/planning.md")
    assert "Issues closed as not planned" in planning and "A request parked for later is not declined." in planning
    for skill in ("orchi-plan", "orchi-explore"):
        assert "(../orchi-core/references/planning.md#declined-work)" in prose(f"{skill}/SKILL.md")


def test_verdicts_reach_the_pr_template():
    testing = prose("orchi-core/references/testing.md")
    for verdict in ("Established", "Limited", "Not established"):
        assert f"**{verdict}:**" in testing
    assert "established, limited, or not established" in installation.PR_TEMPLATE
    assert "[verdict](testing.md#verdicts)" in prose("orchi-core/references/github.md")


def test_researcher_clones_only_outside_the_repository_and_never_runs_them():
    researcher = prose("orchi-core/roles/orchi-researcher.md")
    assert "into a new temporary directory outside the repository" in researcher
    assert "never run, build, or install anything from it" in researcher
