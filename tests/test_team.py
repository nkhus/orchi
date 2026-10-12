"""The team roles, the worker protocol, and their GitHub label agree with each other."""
from pathlib import Path

from orchi_core import agents, installation

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_hubs_are_typed_and_worker_skills_can_be_invoked_by_message():
    for name in ("orchi-planner", "orchi-orchestrator"):
        assert name in agents.SKILLS
        text = (SKILLS / name / "SKILL.md").read_text()
        assert "disable-model-invocation: true" in text and "../orchi/references/team.md" in text
        assert "including after any compaction" in " ".join(text.split())
    for name in ("orchi-explore", "orchi-plan", "orchi-deliver"):
        text = (SKILLS / name / "SKILL.md").read_text()
        assert "disable-model-invocation" not in text
        assert f"asks for {name} by name" in text
        assert f"Invoke the {name} skill with:" in prose("orchi/references/team.md")


def test_worker_limit_and_dispatch_claim_match():
    team, orchestrator, deliver = prose("orchi/references/team.md"), prose("orchi-orchestrator/SKILL.md"), prose("orchi-deliver/SKILL.md")
    assert "The listed workers are the limit: hubs give work to free workers without asking the user first" in team
    assert "at most three" not in team and "at most five" not in orchestrator
    assert "While a listed development worker is free, dispatch" in orchestrator
    assert "`Dispatched to <worker> by <orchestrator> on <date>`" in team
    assert "`Dispatched to <this session's title> by <that orchestrator>` is yours" in deliver
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
    for event in ("rework", "merged", "clear"):
        assert f"#<n> {event}" in team and f"#<n> {event}" in orchestrator and f"#<n> {event}" in deliver
    assert "A development worker keeps its work until its PR is merged" in team
    assert "no uncommitted changes and no commits that are neither merged nor pushed" in team
    assert "`git switch --detach origin/<default>`" in team
    assert "`<id> clearing`" in team and "`<id> not cleared: <reason>`" in team
    assert "Nobody archives or deletes a team session." in team
    assert "a question for the user keeps it waiting, not finished" in team
    assert all("incomplete" not in text for text in (orchestrator, team, deliver))
    for hub in (orchestrator, prose("orchi-planner/SKILL.md")):
        assert "rename, archive, or delete a session" in hub and "Keep this session's title" in hub


def test_lessons_are_proposals_with_one_home():
    review = prose("orchi/references/review-delivery.md")
    assert "## Lessons" in (SKILLS / "orchi/references/review-delivery.md").read_text()
    assert "Only propose: never change instructions, checklists, or checks on your own." in review
    assert "without an observed event it is not a lesson" in review
    assert "review-delivery.md#lessons" in prose("orchi-deliver/SKILL.md")
    assert "review-delivery.md#lessons" in prose("orchi/references/team.md")
    assert "retro" in installation.LABELS


def test_only_work_that_passed_planning_is_dispatched():
    team, orchestrator, planner = prose("orchi/references/team.md"), prose("orchi-orchestrator/SKILL.md"), prose("orchi-planner/SKILL.md")
    assert "delivery-ready" in installation.LABELS
    assert "dispatches an open, unclaimed Issue labelled `delivery-ready`" in team
    assert "dispatch an Issue without `delivery-ready`" in orchestrator
    assert "adds the `delivery-ready` label to the top item" in team
    assert "add `delivery-ready` (planning workers do)" in planner
    assert "An Initiative goes to one development worker" in team
    assert "for `check`, confirm the blocker's result reached the target first" in team
    assert "confirm a `check` blocker first" in orchestrator and "held back" in orchestrator


def test_accepted_lessons_have_an_owner_in_a_team():
    team, review = prose("orchi/references/team.md"), prose("orchi/references/review-delivery.md")
    assert "(in a team, the orchestrator) files each lesson the user accepts" in review
    assert "files the ones the user accepts" in team
    assert "search closed `retro` Issues for the same failure" in review


def test_planning_workers_report_what_the_planner_handles():
    team, planner = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md")
    for event in ("started", "needs the user", "planned", "declined"):
        assert f"<id> {event}" in team and f"`{event}" in planner
    assert "`Planning by <worker>`" in team
    for skill in ("orchi-explore", "orchi-plan"):
        text = prose(f"{skill}/SKILL.md")
        assert "--report-to" in text and "Planning workers" in text and "../orchi/references/team.md" in text
    assert "orchi-plan](../orchi-plan/SKILL.md) `#<n> --report-to <planner>` in this session" in prose("orchi-explore/SKILL.md")
    assert "you never explore or plan yourself" in planner


def test_results_are_routed_by_who_asked():
    team, planner, orchestrator = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md"), prose("orchi-orchestrator/SKILL.md")
    assert "`Requested by: <orchestrator>`" in team
    assert "`Requested by:` the orchestrator" in planner and "`Requested by: <this session's title>`" in orchestrator
    assert "Work the user requested stays with the planner" in team
    assert "message the orchestrator `ready: #<n>[, #<m>]`" in planner
    assert "tell the user the work is ready" in planner


def test_orchestrator_explains_why_work_cannot_be_taken():
    team, orchestrator = prose("orchi/references/team.md"), prose("orchi-orchestrator/SKILL.md")
    assert "the orchestrator says why: being planned (and by whom), not planned, tracked but not labelled (planned outside the team), claimed, or blocked" in team
    assert "say why in one line" in orchestrator and "not planned (no `delivery-ready`)" in orchestrator
    assert "`Queued for delivery at the user's request`" in team and "queued for delivery at the user's request" in orchestrator


def test_hubs_start_each_other():
    team, planner, orchestrator = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md"), prose("orchi-orchestrator/SKILL.md")
    assert "Either hub may be started first" in team and "type the other hub's command in that hub's session" in team
    assert "type `/orchi-orchestrator` in its session" in planner and "type `/orchi-planner` in its session" in orchestrator


def test_follow_ups_carry_the_line_that_routes_them_back():
    deliver, team = prose("orchi-deliver/SKILL.md"), prose("orchi/references/team.md")
    assert "`Requested by: <that orchestrator>`" in deliver
    assert "`Requested by: <orchestrator>`" in team.split("## Follow-ups")[1]


def test_planning_requests_are_claimed_before_their_worker_starts():
    team, planner = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md")
    assert "Before starting a worker for a request that is an Issue, the planner claims it" in team
    assert "claim it and give it to a free planning worker" in planner
    assert "for tracked work without `delivery-ready`, runs the readiness gate on it" in team
    assert "closes the source Exploration" in team
    assert "`<id> declined: parked`" in team and "as not planned with the user's reason" in team


def test_queued_claims_and_cancellations_are_explicit():
    team, planner, orchestrator = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md"), prose("orchi-orchestrator/SKILL.md")
    assert "`Planning queued for <worker> by <planner> on <date>`" in team
    assert "Remove each `Planning queued for …` claim of yours that lapsed" in planner
    assert "or its conversation is empty (the message was lost)" in team
    assert "`Delivery cancelled at the user's request`" in team and "`Delivery cancelled at the user's request`" in orchestrator
    assert "a team planning worker runs the readiness gate on it unless it is `delivery-ready`" in prose("orchi-plan/SKILL.md")


def test_team_sessions_keep_their_titles_and_are_listed_in_instructions():
    team = prose("orchi/references/team.md")
    assert "Orchi never renames a session" in team and "The repository's instructions list the team" in team
    assert "gives no work until it is there" in team
    assert "nobody pastes a command, and no hub creates a session" in team
    assert "`You are <worker>. Invoke the orchi-deliver skill with:" in team
    assert "Each worker session works in its own linked worktree" in team
    assert "a session served over Remote Control, or one that is pinned or open on screen, cannot be cleared" in team
    for text in (team, prose("orchi-deliver/SKILL.md"), prose("orchi-planner/SKILL.md"), prose("orchi-orchestrator/SKILL.md")):
        assert "orchi-worker #" not in text and "orchi-planning <" not in text and "Name this session" not in text


def test_clearing_is_confirmed_before_new_work():
    team, planner, orchestrator = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md"), prose("orchi-orchestrator/SKILL.md")
    assert "If the tool refuses, it replies `<id> not cleared: <reason>`; otherwise it replies `<id> clearing`" in team
    assert "checks that the worker's conversation is empty before giving it work" in team
    assert "once its conversation is empty" in planner and "once its conversation is empty" in orchestrator
    assert "holds no claim but whose conversation is not empty" in team
    for hub in (planner, orchestrator):
        assert "start one planning worker" not in hub and "start a development worker" not in hub and "is not running" not in hub


def test_epic_merges_by_message_need_a_recorded_grant():
    team, deliver = prose("orchi/references/team.md"), prose("orchi-deliver/SKILL.md")
    assert "`Epic merges into the Initiative branch granted by the user on <date>`" in team
    assert "Use `--merge-epics` from a message only when the Initiative carries the user's grant comment" in deliver


def test_idle_workers_are_cleared_once_and_queued_work_survives():
    team, planner, orchestrator = prose("orchi/references/team.md"), prose("orchi-planner/SKILL.md"), prose("orchi-orchestrator/SKILL.md")
    assert "unless it replied `clearing` since your last check" in planner and "unless it replied `clearing` since your last check" in orchestrator
    assert "as plain `clear`" in team and "it works in a linked worktree" in team
    assert "the hub tells the user to continue it with that worker instead" in team
    assert "when none is free, comment that it is queued" in orchestrator


def test_hubs_rebrief_workers_that_lost_their_role():
    assert "its hub sends the same work message again" in prose("orchi/references/team.md")
