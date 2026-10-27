"""Text, not behavior: the skills, roles, and references agree where a session follows one and not the other."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def prose(path):
    return " ".join((SKILLS / path).read_text().split())


def test_reviewer_role_carries_the_standards_and_context_checks():
    reviewer = prose("orchi-core/roles/orchi-reviewer.md")
    for phrase in ("`ENGINEERING.md`", "`standards.py ratchet`", "`knowledge.py stale --since <target>`",
                   "`docs/work/`", "Exceptions:", "acceptance test that asserts it", "(`knowledge.py work`)"):
        assert phrase in reviewer, phrase
    assert "Core documentation" not in reviewer


def test_delivery_steps_match_the_review_and_knowledge_references():
    deliver = prose("orchi-deliver/SKILL.md")
    assert "Exceptions from the review" in deliver and "its Exceptions filled" in deliver
    assert "`stale --since <target>`, and `behavior`, plus `work` when the target is `main`" in deliver
    assert "move the rest of the working folder into current documentation and delete it" in deliver
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
    assert "followed by the role's full report, sources included" in prose("orchi-work/SKILL.md")
    assert "a worker's `research` or `retrieve` answer, which carries the role's full report" in prose(
        "orchi-core/references/pool.md")
    assert "Start `orchi-researcher` subagents for research questions and option lenses" in prose("orchi-explore/SKILL.md")


def test_references_agree_on_branches_labels_pr_sections_and_readiness():
    github = prose("orchi-core/references/github.md")
    for phrase in ("`design` for an Epic a designer runs", "`explore/card-payments`", "`task/<slug>` from the Epic branch",
                   "`prototype/<slug>`, never merged", "**Exceptions:**", "documentation, design, and standards check workflows"):
        assert phrase in github, phrase
    assert "branches that merge into the Epic branch" in prose("orchi-core/references/execution.md")
    assert "items 1–11, 13, and 14 of the Epic readiness checklist" in prose("orchi-design/SKILL.md")
    assert "`impeccable-manual-edit-applier` serves Impeccable's live mode" in prose("orchi-core/roles/README.md")
