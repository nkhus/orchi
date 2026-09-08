"""Git-visible atomic publication. Deployment and hosted PR creation remain external."""
from __future__ import annotations

from .common import integration_base, require


def handoff(engine) -> dict:
    state = engine.state()
    require(state["phase"] == "READY_TO_PUBLISH" and state["final"]["approved"], "APPROVAL_REQUIRED", "Final human acceptance is required")
    base = integration_base(state)
    require(engine.repo.resolve(engine.policy.canonical_ref) == base, "CANONICAL_MOVED", "Synchronize and revalidate before publishing")
    return {"canonical_ref": engine.policy.canonical_ref, "expected_parent": base,
            "origin_baseline": state["baseline"], "candidate": state["final"]["commit"],
            "tree": engine.repo.tree(state["final"]["commit"]), "mode": engine.policy.publication_mode,
            "action": "Publish through the operator's local Git or existing PR/MR workflow, then record-publication. No remote PR or deployment is created by this handoff.",
            "acceptance": "Exact checked tree and approved integration base are mandatory. Queue recomposition with additional code requires synchronization and new final approval."}


def record(engine, commit: str) -> dict:
    with engine.store.transaction("initiative.published") as state:
        require(state["phase"] == "READY_TO_PUBLISH" and state["final"]["approved"], "APPROVAL_REQUIRED", "Final approval missing")
        commit = engine.repo.resolve(commit)
        canonical = engine.repo.resolve(engine.policy.canonical_ref)
        require(engine.repo.is_ancestor(commit, canonical), "PUBLICATION_NOT_VISIBLE", "Reported publication is not in canonical history")
        candidate, base = state["final"]["commit"], integration_base(state)
        require(engine.repo.tree(commit) == engine.repo.tree(candidate), "WRONG_PUBLISHED_TREE", "Published code/docs differ from the approved candidate")
        parents = engine.repo.git("rev-list", "--parents", "-n", "1", commit).decode().split()[1:]
        mode = engine.policy.publication_mode
        expected = [base, candidate] if mode == "merge" else [base]
        require(parents == expected, "WRONG_PUBLICATION_PARENT", "Published parents differ from the policy-approved boundary")
        if mode == "exact":
            require(commit == candidate, "WRONG_PUBLICATION_COMMIT", "Exact mode requires the signed candidate, not an equivalent-tree commit")
        state.update(phase="PUBLISHED", published_commit=commit,
                     publication={"commit": commit, "candidate": candidate, "mode": mode, "observed_canonical": canonical,
                                  "integration_base": base, "deployment": "not-implied"})
        return {"status": "published", **state["publication"]}


def publish_local(engine) -> dict:
    """Operator-only CAS publication to a branch not checked out in any worktree."""
    info = handoff(engine)
    require(info["mode"] in {"exact", "merge"}, "HOST_PUBLICATION_REQUIRED", "Create the squash commit in the operator's Git workflow and record it")
    checked_out = engine.repo.git("worktree", "list", "--porcelain").decode().splitlines()
    require("branch " + info["canonical_ref"] not in checked_out, "TARGET_CHECKED_OUT",
            "Detach the target branch from worktrees before atomic ref publication, or perform a normal operator merge and record-publication")
    candidate = info["candidate"]
    if info["mode"] == "merge":
        candidate = engine.repo.git("commit-tree", info["tree"], "-p", info["expected_parent"], "-p", info["candidate"],
                                    data=b"Orchi atomic initiative merge\n").decode().strip()
    # A concurrent upstream publication cannot be overwritten: Git compares old-oid.
    engine.repo.git("update-ref", info["canonical_ref"], candidate, info["expected_parent"])
    return record(engine, candidate)
