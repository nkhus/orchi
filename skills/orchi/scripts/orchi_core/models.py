"""Strict authoring contracts for initiatives, epics, tasks, and verification."""
from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
from .common import path, core_target, protected, require

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ID = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$", max_length=80)]
Commit = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Check(Model):
    argv: list[Text] = Field(min_length=1)
    timeout_seconds: int = Field(default=120, ge=1, le=3600)


class Policy(Model):
    canonical_ref: str = "refs/heads/main"
    public_key: Text
    checks: dict[ID, Check] = Field(min_length=1)
    baseline_checks: list[ID] = []
    final_checks: list[ID] = Field(min_length=1)
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
        require(set(self.baseline_checks + self.final_checks) <= set(self.checks), "UNKNOWN_CHECK", "Policy check not registered")
        require(self.lease_seconds >= 2 * self.max_process_seconds, "INVALID_POLICY", "Lease must cover preparation and execution")
        return self


class RoadmapEpic(Model):
    id: ID
    title: Text
    outcome: Text
    depends_on: list[ID] = []
    contributes_to: list[ID] = Field(min_length=1)
    risks: list[Text] = []
    # Deliberately no tasks/design/files: future execution detail has no place here.


class Initiative(Model):
    format: Literal["orchi-initiative"] = "orchi-initiative"
    id: ID
    request: Text
    outcome: Text
    acceptance: dict[ID, Text] = Field(min_length=1)
    constraints: list[Text] = Field(min_length=1)
    direction: Text
    epics: list[RoadmapEpic] = Field(min_length=1)

    @model_validator(mode="after")
    def roadmap_valid(self):
        seen, covered = set(), set()
        for e in self.epics:
            require(e.id not in seen and set(e.depends_on) <= seen, "INVALID_ROADMAP", "Roadmap must be unique and topologically ordered")
            require(set(e.contributes_to) <= set(self.acceptance), "UNKNOWN_ACCEPTANCE", e.id)
            seen.add(e.id)
            covered.update(e.contributes_to)
        require(covered == set(self.acceptance), "INCOMPLETE_ROADMAP", "Every initiative criterion must have a contributing epic")
        return self


class Source(Model):
    kind: Literal["knowledge", "code", "dependency"]
    path: Text
    reason: Text
    producer: ID | None = None
    contract: str = ""

    @model_validator(mode="after")
    def valid(self):
        path(self.path)
        if self.kind == "knowledge":
            core_target(self.path)
        else:
            require(not self.path.startswith(("initiatives/", "changes/", "history/", "docs/")), "SOURCE_SCOPE", self.path)
        require((self.kind == "dependency") == (self.producer is not None), "INVALID_SOURCE", "Dependency sources need a producer only")
        require(self.kind != "dependency" or bool(self.contract.strip()), "MISSING_CONTRACT", self.path)
        return self


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


class Task(Model):
    id: ID
    goal: Text
    acceptance: dict[ID, Text] = Field(min_length=1)
    depends_on: list[ID] = []
    current_state: Text
    approach: Text
    decisions: list[Text] = Field(min_length=1)
    invariants: list[Text] = Field(min_length=1)
    allowed_choices: list[Text]
    failure_modes: list[Text]
    edits: list[Edit] = Field(min_length=1)
    context: list[Source] = Field(min_length=1)
    read_paths: list[Text] = []
    exclusive_resources: list[Text] = []
    verification: list[VerificationCase] = Field(min_length=1)
    escalation: list[Text] = Field(min_length=1)
    open_questions: list[Text]  # explicit [] required

    @model_validator(mode="after")
    def complete(self):
        require(not self.open_questions, "UNRESOLVED_DESIGN", self.id)
        require({v.criterion for v in self.verification} == set(self.acceptance), "INCOMPLETE_ACCEPTANCE", self.id)
        require(len({e.path for e in self.edits}) == len(self.edits), "DUPLICATE_PATH", self.id)
        for p in self.read_paths:
            path(p)
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
    artifacts: list[Text] = Field(min_length=1)
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


class Finalization(Model):
    format: Literal["orchi-finalization"] = "orchi-finalization"
    initiative_id: ID
    based_on: Commit
    report: Text
    entries: list[KnowledgeEdit]
    acceptance_checks: dict[ID, list[ID]] = Field(min_length=1)


class Readiness(Model):
    packet_fingerprint: Text
    understood_goal: Text
    fixed_decisions: list[Text] = Field(min_length=1)
    acceptance_ids: list[ID] = Field(min_length=1)
    questions: list[Text]


class WorkerResult(Model):
    status: Literal["completed", "blocked"]
    summary: Text
    extra_reads: list[Text] = []
    deviations: list[Text] = []

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


CONTRACTS = {c.__name__: c for c in (Policy, Initiative, EpicPlan, Task, Checkpoint, Finalization, Readiness, WorkerResult, ReviewReport)}
