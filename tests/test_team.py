"""The team roles, the worker protocol, and their GitHub label agree with each other."""
from pathlib import Path

from orchi_core import agents, installation

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_team_roles_are_explicit_entry_skills():
    for name in ("orchi-planner", "orchi-orchestrator"):
        assert name in agents.SKILLS
        text = (SKILLS / name / "SKILL.md").read_text()
        assert "disable-model-invocation: true" in text and "../orchi/references/team.md" in text
        assert "including after any compaction" in " ".join(text.split())


def test_worker_limit_and_dispatch_claim_match():
    team, orchestrator, deliver = prose("orchi/references/team.md"), prose("orchi-orchestrator/SKILL.md"), prose("orchi-deliver/SKILL.md")
    assert "At most five workers" in team and "without asking the user" in team
    assert "five unless the repository's instructions say otherwise" in orchestrator
    assert "`Dispatched to orchi-worker #<n> · <repo> by orchi-orchestrator · <repo> on <date>`" in team
    assert "`Dispatched to orchi-worker #<n> … by <that orchestrator>` is yours" in deliver
    assert "merge into main without the user's word" in orchestrator


def test_worker_events_use_the_names_the_orchestrator_handles():
    deliver, orchestrator = prose("orchi-deliver/SKILL.md"), prose("orchi-orchestrator/SKILL.md")
    assert "--report-to" in deliver
    for event in ("started", "PR ready", "needs the user", "follow-up", "done"):
        assert f"#<n> {event}" in deliver and f"`{event}" in orchestrator


def test_needs_planning_label_is_installed():
    assert "needs-planning" in installation.LABELS and "Exploration" in installation.LABELS


def test_orchestrator_events_to_workers_and_retirement_agree():
    team, orchestrator, deliver = prose("orchi/references/team.md"), prose("orchi-orchestrator/SKILL.md"), prose("orchi-deliver/SKILL.md")
    for event in ("incomplete", "rework", "merged"):
        assert f"#<n> {event}" in team and f"#<n> {event}" in orchestrator and f"#<n> {event}" in deliver
    assert "A worker lives until its PR is merged" in team
    assert "no uncommitted or unpushed changes" in team and "It never deletes a session." in team
    assert "archive a worker whose PR is still open" in orchestrator and "delete a session" in orchestrator


def test_lessons_are_proposals_with_one_home():
    review = prose("orchi/references/review-delivery.md")
    assert "## Lessons" in (SKILLS / "orchi/references/review-delivery.md").read_text()
    assert "Only propose: never change instructions, checklists, or checks on your own." in review
    assert "without an observed event it is not a lesson" in review
    assert "review-delivery.md#lessons" in prose("orchi-deliver/SKILL.md")
    assert "review-delivery.md#lessons" in prose("orchi/references/team.md")
    assert "retro" in installation.LABELS
