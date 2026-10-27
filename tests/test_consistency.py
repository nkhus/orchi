"""Text, not behavior: the skills, roles, and references agree where a session follows one and not the other."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_reviewer_role_carries_the_standards_and_context_checks():
    reviewer = prose("orchi-core/roles/orchi-reviewer.md")
    for phrase in ("`ENGINEERING.md`", "the gate integrity list", "the map still covers the changed code",
                   "`docs/work/`", "Exceptions:", "acceptance test that asserts it", "the working folder holds only the plan's `README.md`"):
        assert phrase in reviewer, phrase
    assert "Core documentation" not in reviewer


def test_delivery_steps_match_the_review_and_knowledge_references():
    deliver = prose("orchi-deliver/SKILL.md")
    assert "the review's Exceptions" in deliver and "every review finding with its resolution or `unresolved`" in deliver
    assert "run `knowledge.py lint`, plus `work` when the target is `main`" in deliver
    assert "move the rest of the working folder into current documentation except the plan's `README.md`" in deliver
    assert "Delete the working folder in its own commit" in deliver
    assert "Core" not in deliver.replace("orchi-core", "")
    assert "ask the user once whether to apply the branch ruleset" in deliver
    assert "the delivering session (`orchi-deliver`) asks the user once" in prose("orchi-core/references/standards.md")


def test_orchi_picks_up_a_requested_plan_once_unblocked():
    assert "open `needs-planning` Issues that say `Requested by:` this session once their blockers are closed" in prose(
        "orchi/SKILL.md")
    assert "the weekly drift Issue, wait for the user" in prose("orchi-core/references/pool.md")


def test_an_exploration_with_several_items_hands_its_folder_to_the_first():
    assert "the folder goes to the first in delivery order" in prose("orchi-core/references/knowledge.md")
    assert "by commit permalink" in prose("orchi-core/references/exploration.md")
    assert "the branch of its first item in delivery order" in prose("orchi-plan/SKILL.md")


def test_research_answers_reach_the_crew_in_full():
    assert "followed by the role's full report: checks, red evidence, or the answer with its sources" in prose("orchi-work/SKILL.md")
    assert "The exception is a worker's `done`, which carries the role's full report" in prose(
        "orchi-core/references/pool.md")
    assert "build a prototype yourself on `prototype/<slug>`" in prose("orchi-explore/SKILL.md")


def test_references_agree_on_branches_labels_pr_sections_and_readiness():
    github = prose("orchi-core/references/github.md")
    for phrase in ("`design` for an Epic a designer runs", "`explore/card-payments`", "`task/<slug>` from the Epic branch",
                   "`prototype/<slug>`, never merged", "**Exceptions:**", "documentation, design, and standards check workflows"):
        assert phrase in github, phrase
    assert "branches that merge into the Epic branch" in prose("orchi-core/references/execution.md")
    assert "items 1–11, 13, and 14 of the Epic readiness checklist" in prose("orchi-design/SKILL.md")
    assert "`impeccable-manual-edit-applier` serves Impeccable's live mode" in prose("orchi-core/roles/README.md")


def test_flows_do_not_stall_and_keep_user_only_questions():
    pool, entry, deliver = prose("orchi-core/references/pool.md"), prose("orchi/SKILL.md"), prose("orchi-deliver/SKILL.md")
    assert "for an Initiative Orchi checks that every native blocker is closed as completed" in pool
    assert "a `design` Epic has none yet" in prose("orchi-core/references/readiness.md")
    assert "and that Orchi takes it from here" in prose("orchi-plan/SKILL.md")
    assert "An Epic labelled `design` → report `#<n> declined: a design Epic goes to a designer crew`" in deliver
    assert "to choose a design direction or approve a comp or a generated asset; to apply the branch ruleset" in pool
    assert "a researcher still leaves the exploration's direction to the user" in pool
    assert "its Exceptions section says `None`" in pool
    assert "and whether its PR was merged (then send `#<n> merged`)" in entry
    assert "the pool has no liveness check between wakes" in pool
    assert "Orchi on `crew-<k> ready`, a crew on each `worker-<n> ready`" in pool
    assert "the session it names has stopped" in deliver and "the session it names has stopped" in prose(
        "orchi-core/references/execution.md")
    assert "only `orchi-plan` closes the Exploration" in prose("orchi-standards/SKILL.md")
    assert "it commits and pushes the installation to `main`" in prose("orchi-core/references/exploration.md")


def test_orchi_is_the_only_command_the_user_types():
    import re
    import yaml
    for skill in ("orchi-explore", "orchi-plan", "orchi-standards", "orchi-design", "orchi-deliver", "orchi-work"):
        text = (SKILLS / skill / "SKILL.md").read_text()
        meta = yaml.safe_load(text.split("---", 2)[1])
        assert meta["user-invocable"] is False, skill
        if skill != "orchi-work":
            assert "--report-to <Orchi session>" in meta["argument-hint"] and "[--report-to" not in meta["argument-hint"], skill
            assert "tell the user that work starts with `/orchi`, and stop" in prose(f"{skill}/SKILL.md"), skill
    for path in SKILLS.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".yml", ".py"}:
            assert not re.search(r"(?<![\w./-])/orchi-(explore|plan|standards|design|deliver|work)\b", path.read_text()), path
    assert "The user types only `/orchi`" in prose("orchi-core/SKILL.md")
