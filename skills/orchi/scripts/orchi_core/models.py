"""Strict authoring contracts for initiatives, epics, tasks, and verification."""
from __future__ import annotations
import re
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
from .common import path, core_target, protected, require

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ID = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$", max_length=80)]
Commit = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
SHA256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Check(Model):
    argv: list[Text] = Field(min_length=1)
    timeout_seconds: int = Field(default=120, ge=1, le=3600)
    resources: list[ID] = []


class Policy(Model):
    canonical_ref: str = "refs/heads/main"
    public_key: Text
    checks: dict[ID, Check] = Field(min_length=1)
    baseline_checks: list[ID] = []
    final_checks: list[ID] = Field(min_length=1)
    publication_mode: Literal["exact", "squash", "merge"] = "exact"
    verification_strategy: Literal["cumulative", "scoped"] = "cumulative"
    integration_checks: list[ID] = []
    sync_checks: list[ID] = []
    max_integration_retries: int = Field(default=8, ge=1, le=64)
    resource_directory: str | None = None
    resource_wait_seconds: int = Field(default=120, ge=1, le=3600)
    allow_unresolved_requirements: bool = False
    allow_unrealized_architecture: bool = False
    max_workers: int = Field(default=4, ge=1, le=32)
    max_attempts_per_task: int = Field(default=3, ge=1, le=10)
    max_attempts_per_epic: int = Field(default=48, ge=1, le=1000)
    max_attempts_total: int = Field(default=200, ge=1, le=10000)
    max_review_rounds: int = Field(default=3, ge=1, le=5)
    max_packet_bytes: int = Field(default=96000, ge=1024, le=1_000_000)
    lease_seconds: int = Field(default=3600, ge=10, le=86400)
    max_process_seconds: int = Field(default=900, ge=1, le=7200)
    max_output_bytes: int = Field(default=2_000_000, ge=1024, le=20_000_000)

    @model_validator(mode="after")
    def consistent(self):
        require(self.canonical_ref.startswith("refs/heads/") and ".." not in self.canonical_ref,
                "INVALID_REF", "Use an explicit local canonical branch ref")
        require(set(self.baseline_checks + self.final_checks + self.integration_checks + self.sync_checks) <= set(self.checks), "UNKNOWN_CHECK", "Policy check not registered")
        require(self.lease_seconds >= 2 * self.max_process_seconds, "INVALID_POLICY", "Lease must cover preparation and execution")
        require(self.verification_strategy != "scoped" or bool(self.integration_checks),
                "INVALID_POLICY", "Scoped integration requires operator-selected integration checks")
        if self.resource_directory is not None:
            from pathlib import Path
            require(Path(self.resource_directory).is_absolute(), "INVALID_POLICY", "Resource directory must be absolute")
        require(not any(c.resources for c in self.checks.values()) or self.resource_directory is not None,
                "INVALID_POLICY", "Shared check resources require an explicit common resource directory")
        return self


class RoadmapEpic(Model):
    id: ID
    title: Text
    outcome: Text
    depends_on: list[ID] = []
    contributes_to: list[ID] = Field(min_length=1)
    risks: list[Text] = []
    realizes: list[Text] = []
    # Deliberately no tasks/design/files: future execution detail has no place here.


class IntentRef(Model):
    revision: int = Field(ge=1)
    digest: SHA256


class IntentManifest(Model):
    format: Literal["orchi-intent"] = "orchi-intent"
    initiative_id: ID
    revision: int = Field(ge=1)
    documents: dict[Text, SHA256] = Field(min_length=3)
    requirements: dict[ID, Text] = Field(min_length=1)
    architecture: list[Text] = Field(min_length=1)
    # Removed requirements retain an accepted, durable disposition; IDs are never reused.
    resolved_requirements: dict[ID, Text] = {}

    @model_validator(mode="after")
    def consistent(self):
        require(not (self.requirements.keys() & self.resolved_requirements.keys()),
                "DUPLICATE_REQUIREMENT", "Active and resolved requirement IDs must be disjoint")
        require(len(set(self.architecture)) == len(self.architecture), "DUPLICATE_TARGET", "Architecture references must be unique")
        return self


class Initiative(Model):
    format: Literal["orchi-initiative"] = "orchi-initiative"
    id: ID
    outcome: Text
    result_kind: Literal["software", "knowledge", "investigation"] = "software"
    delivery: Literal["atomic"] = "atomic"
    intent: IntentRef
    epics: list[RoadmapEpic] = Field(min_length=1)

    @model_validator(mode="after")
    def roadmap_valid(self):
        seen = set()
        for e in self.epics:
            require(e.id not in seen and set(e.depends_on) <= seen,
                    "INVALID_ROADMAP", "Roadmap must be unique and topologically ordered")
            require(len(set(e.depends_on)) == len(e.depends_on) and
                    len(set(e.contributes_to)) == len(e.contributes_to) and
                    len(set(e.realizes)) == len(e.realizes), "DUPLICATE_REFERENCE", e.id)
            seen.add(e.id)
        # Requirement and architecture coverage are validated against the exact Intent bundle.
        return self


class Source(Model):
    kind: Literal["knowledge", "code", "dependency"]
    path: Text
    reason: Text
    view: Literal["current", "target"] | None = None
    producer: ID | None = None
    contract: str = ""
    delivery: Literal["inline", "on-demand"] = "inline"
    consistency: Literal["fixed", "snapshot"] = "fixed"

    @model_validator(mode="after")
    def valid(self):
        if self.kind == "knowledge":
            require(self.view is not None, "KNOWLEDGE_VIEW_REQUIRED", "Knowledge sources must select current or target")
            document = self.path.split("#", 1)[0]
            if self.view == "current":
                core_target(document)
            else:
                path(document)
                require(document.startswith("intent/") and document.endswith(".md") or
                        bool(re.fullmatch(r"req-[a-z0-9]+(?:[-.][a-z0-9]+)*", document)),
                        "INVALID_TARGET_SOURCE", self.path)
        else:
            path(self.path)
            require(self.view is None, "INVALID_SOURCE_VIEW", "Only knowledge sources have authority views")
            require(not self.path.startswith(("initiatives/", "changes/", "history/", "docs/", "intent/")), "SOURCE_SCOPE", self.path)
        require((self.kind == "dependency") == (self.producer is not None), "INVALID_SOURCE", "Dependency sources need a producer only")
        require(self.kind != "dependency" or bool(self.contract.strip()), "MISSING_CONTRACT", self.path)
        return self


class DesignRef(Model):
    path: Text
    content_hash: SHA256

    @field_validator("path")
    @classmethod
    def design_path(cls, value):
        path(value)
        require(bool(re.fullmatch(r"design/[1-9][0-9]*\.md", value)),
                "INVALID_DESIGN_PATH", "Use design/<accepted-plan-revision>.md")
        return value


class Edit(Model):
    path: Text
    action: Literal["create", "modify", "delete"]
    how: Text

    @field_validator("path")
    @classmethod
    def writable(cls, value):
        path(value)
        require(not protected(value), "PROTECTED_PATH", value)
        return value


class VerificationCase(Model):
    criterion: ID
    scenario: Text
    expected: Text
    checks: list[ID] = Field(min_length=1)


class ScopeRule(Model):
    """An accepted directory envelope, not a wildcard permission to change semantics."""
    directory: Text
    actions: list[Literal["create", "modify", "delete"]] = Field(min_length=1)
    choices: list[Text] = Field(min_length=1)

    @field_validator("directory")
    @classmethod
    def bounded_directory(cls, value):
        path(value)
        require(not protected(value + "/scope-probe"), "PROTECTED_PATH", value)
        return value


class Task(Model):
    id: ID
    kind: Literal["implementation", "investigation"] = "implementation"
    executor: Literal["agent", "human", "pair"] = "agent"
    write_scope: list[ScopeRule] = []
    max_scope_additions: int = Field(default=8, ge=0, le=100)
    goal: Text
    acceptance: dict[ID, Text] = Field(min_length=1)
    depends_on: list[ID] = []
    current_state: Text
    approach: Text
    decisions: list[Text] = Field(min_length=1)
    invariants: list[Text] = Field(min_length=1)
    allowed_choices: list[Text]
    failure_modes: list[Text]
    edits: list[Edit] = []
    context: list[Source] = []
    read_paths: list[Text] = []
    exclusive_resources: list[Text] = []
    verification: list[VerificationCase] = Field(min_length=1)
    escalation: list[Text] = Field(min_length=1)
    open_questions: list[Text]  # explicit [] required

    @model_validator(mode="after")
    def complete(self):
        require(not self.open_questions, "UNRESOLVED_DESIGN", self.id)
        require(bool(self.edits) if self.kind == "implementation" else not self.edits and not self.write_scope,
                "INVALID_TASK_KIND", "Implementation needs edits; investigations cannot write product files")
        require(all(set(rule.choices) <= set(self.allowed_choices) for rule in self.write_scope),
                "UNDELEGATED_CHOICE", "Every scope rule must reference explicitly allowed local choices")
        require({v.criterion for v in self.verification} == set(self.acceptance), "INCOMPLETE_ACCEPTANCE", self.id)
        require(len({e.path for e in self.edits}) == len(self.edits), "DUPLICATE_PATH", self.id)
        for p in self.read_paths:
            path(p)
            require(not p.startswith(("docs/", "intent/", "initiatives/", "history/", "changes/")), "SOURCE_SCOPE", "Use a view-explicit knowledge source: " + p)
        require(len(set(self.depends_on)) == len(self.depends_on) and self.id not in self.depends_on, "INVALID_DEPENDENCIES", self.id)
        for source in self.context:
            require(source.producer is None or source.producer in self.depends_on, "MISSING_DEPENDENCY", self.id)
        return self


class EpicPlan(Model):
    format: Literal["orchi-epic"] = "orchi-epic"
    initiative_id: ID
    epic_id: ID
    based_on: Commit
    goal: Text
    shared_design: Text
    design: DesignRef
    intent_digest: SHA256
    acceptance: dict[ID, Text] = Field(min_length=1)
    acceptance_checks: dict[ID, list[ID]] = Field(min_length=1)
    mode: Literal["implementation", "knowledge-only"] = "implementation"
    tasks: list[Task]

    @model_validator(mode="after")
    def dag(self):
        require((self.mode == "implementation") == bool(self.tasks), "INVALID_EPIC_MODE", "Implementation epics require tasks; knowledge-only epics have none")
        require(set(self.acceptance) == set(self.acceptance_checks) and all(self.acceptance_checks.values()), "INCOMPLETE_ACCEPTANCE", self.epic_id)
        seen = set()
        for t in self.tasks:
            require(t.id not in seen and set(t.depends_on) <= seen, "INVALID_TASK_DAG", "Tasks must be unique and topologically ordered")
            seen.add(t.id)
        return self


class KnowledgeEdit(Model):
    target: Text
    action: Literal["replace", "retire", "revalidate"]
    content: str | None = None
    artifacts: list[Text] = []
    checks: list[ID] = Field(min_length=1)
    reason: Text

    @model_validator(mode="after")
    def valid(self):
        core_target(self.target)
        for p in self.artifacts:
            path(p)
            require(not p.startswith(("initiatives/", "changes/", "history/", "docs/")), "INVALID_ARTIFACT", p)
        require((self.action == "replace") == (self.content is not None), "INVALID_KNOWLEDGE_EDIT", self.target)
        if self.content is not None:
            require(bool(self.content.strip()), "EMPTY_KNOWLEDGE", self.target)
        return self


class Disposition(Model):
    path: Text
    targets: list[Text]
    reason: Text

    @model_validator(mode="after")
    def valid(self):
        path(self.path)
        for t in self.targets:
            core_target(t)
        return self


class Checkpoint(Model):
    format: Literal["orchi-checkpoint"] = "orchi-checkpoint"
    epic_id: ID
    based_on: Commit
    report: Text
    entries: list[KnowledgeEdit]
    dispositions: list[Disposition]


class RequirementDisposition(Model):
    requirement_id: ID
    disposition: Literal["satisfied", "changed", "unresolved"]
    reason: Text
    checks: list[ID] = []
    core_targets: list[Text] = []


class ArchitectureDisposition(Model):
    target: Text
    disposition: Literal["realized", "deviated", "unchanged", "not-applicable", "unresolved"]
    reason: Text
    artifacts: list[Text] = []
    core_targets: list[Text] = []
    checks: list[ID] = []


class Finalization(Model):
    format: Literal["orchi-finalization"] = "orchi-finalization"
    initiative_id: ID
    based_on: Commit
    intent_digest: SHA256
    report: Text
    entries: list[KnowledgeEdit]
    requirements: list[RequirementDisposition] = Field(min_length=1)
    architecture: list[ArchitectureDisposition] = Field(min_length=1)

    @model_validator(mode="after")
    def unique(self):
        require(len({r.requirement_id for r in self.requirements}) == len(self.requirements),
                "DUPLICATE_REQUIREMENT", "One final disposition per requirement")
        require(len({a.target for a in self.architecture}) == len(self.architecture),
                "DUPLICATE_TARGET", "One final disposition per architecture node")
        for r in [*self.requirements, *self.architecture]:
            for t in r.core_targets:
                core_target(t)
        for a in self.architecture:
            for p in a.artifacts:
                path(p)
                require(not protected(p), "INVALID_ARTIFACT", p)
        return self


class Readiness(Model):
    packet_fingerprint: Text
    understood_goal: Text
    fixed_decisions: list[Text] = Field(min_length=1)
    acceptance_ids: list[ID] = Field(min_length=1)
    questions: list[Text]


class DocumentationProposal(Model):
    target: Text
    content: Text
    reason: Text

    @field_validator("target")
    @classmethod
    def target_path(cls, value):
        return core_target(value)


class WorkerResult(Model):
    status: Literal["completed", "blocked"]
    summary: Text
    extra_reads: list[Text] = []
    deviations: list[Text] = []
    observations: list[Text] = []
    documentation_proposals: list[DocumentationProposal] = []

    @field_validator("extra_reads")
    @classmethod
    def paths(cls, values):
        for p in values:
            path(p)
        return values


class Finding(Model):
    path: Text
    criterion: Text
    root_cause: Text
    consequence: Text
    evidence: Text
    disposition: Literal["blocker", "unsubstantiated", "advisory", "resolved"]
    task_ids: list[ID] = []

    @field_validator("path")
    @classmethod
    def valid_path(cls, value):
        return path(value)


class ReviewReport(Model):
    request_id: Text
    reviewer: Text
    complete: bool
    covered_paths: list[Text]
    findings: list[Finding]
    summary: Text


class ScopeRequest(Model):
    edit: Edit
    choice: Text
    reason: Text
    change_kind: Literal["local", "design", "target"] = "local"


class SyncResolution(Model):
    path: Text
    action: Literal["replace", "delete", "take-file"]
    content: str | None = None
    commit: Commit | None = None
    mode: Literal["100644", "100755"] = "100644"
    reason: Text

    @model_validator(mode="after")
    def valid(self):
        path(self.path)
        require((self.action == "replace") == (self.content is not None), "INVALID_RESOLUTION", self.path)
        require((self.action == "take-file") == (self.commit is not None), "INVALID_RESOLUTION", self.path)
        return self


class SyncKnowledge(Model):
    target: Text
    action: Literal["update", "revalidate", "retire", "use-upstream"]
    reason: Text
    content: str | None = None
    artifacts: list[Text] = []
    checks: list[ID] = []

    @model_validator(mode="after")
    def valid(self):
        core_target(self.target)
        require((self.action == "update") == (self.content is not None), "INVALID_KNOWLEDGE_EDIT", self.target)
        for p in self.artifacts:
            path(p)
            require(not protected(p), "INVALID_ARTIFACT", p)
        return self


class SyncProposal(Model):
    format: Literal["orchi-sync"] = "orchi-sync"
    based_on: Commit
    upstream: Commit
    reason: Text
    target_assessment: Text
    target_revision_required: bool = False
    resolutions: list[SyncResolution] = []
    knowledge: list[SyncKnowledge] = []
    checks: list[ID] = []

    @model_validator(mode="after")
    def unique(self):
        require(len({r.path for r in self.resolutions}) == len(self.resolutions), "DUPLICATE_PATH", "Sync resolutions")
        require(len({r.target for r in self.knowledge}) == len(self.knowledge), "DUPLICATE_TARGET", "Sync knowledge decisions")
        return self


class CompactTask(Model):
    id: ID
    goal: Text
    edits: list[Edit] = []
    checks: list[ID] = Field(min_length=1)
    kind: Literal["implementation", "investigation"] = "implementation"
    executor: Literal["agent", "human", "pair"] = "agent"
    context: list[Source] = []
    depends_on: list[ID] = []
    allowed_choices: list[Text] = []
    write_scope: list[ScopeRule] = []


class ChangeBrief(Model):
    format: Literal["orchi-brief"] = "orchi-brief"
    id: ID
    request: Annotated[str, StringConstraints(min_length=1)]
    outcome: Text
    result_kind: Literal["software", "knowledge", "investigation"] = "software"
    requirements: dict[ID, Text] = Field(min_length=1)
    architecture: Text
    design: Text
    decisions: list[Text] = Field(min_length=1)
    invariants: list[Text] = Field(min_length=1)
    checks: list[ID] = Field(min_length=1)
    tasks: list[CompactTask] = []

    @model_validator(mode="after")
    def stable_requirements(self):
        require(bool(self.request.strip()), "INVALID_REQUEST", "Preserve a nonempty original request")
        require(all(k.startswith("req-") for k in self.requirements), "INVALID_REQUIREMENT", "Use stable req- identifiers")
        return self


CONTRACTS = {c.__name__: c for c in (Policy, Initiative, IntentManifest, EpicPlan, Task, Checkpoint, Finalization, Readiness, WorkerResult, ReviewReport, ScopeRequest, SyncProposal, ChangeBrief)}
