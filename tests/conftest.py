from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from orchi_core.engine import Engine
from orchi_core.signing import keygen, sign


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return p.stdout.strip()


class World:
    def __init__(self, root):
        self.root = root
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "src").mkdir()
        (self.repo / "docs").mkdir()
        (self.repo / "src/left.py").write_text("VALUE = 0\n")
        (self.repo / "src/right.py").write_text("VALUE = 0\n")
        (self.repo / "docs/architecture.md").write_text('---\nartifacts: [src/left.py]\n---\n# Architecture\nThe left value starts at zero.\n')
        (self.repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
        git(self.repo, "add", "."); git(self.repo, "commit", "-m", "baseline")
        self.baseline = git(self.repo, "rev-parse", "HEAD")
        self.key = root / "operator.pem"
        public = keygen(self.key)
        self.policy = {
            "public_key": public,
            "checks": {
                "baseline": {"argv": [sys.executable, "-c", "import pathlib; assert pathlib.Path('src/left.py').exists()"]},
                "left": {"argv": [sys.executable, "-c", "import runpy; assert runpy.run_path('src/left.py')['VALUE']==1"]},
                "right": {"argv": [sys.executable, "-c", "import runpy; assert runpy.run_path('src/right.py')['VALUE']==2"]},
                "api": {"argv": [sys.executable, "-c", "import runpy; assert runpy.run_path('src/api.py')['ANSWER']==3"]},
                "final": {"argv": [sys.executable, "-c", "import runpy; assert runpy.run_path('src/api.py')['ANSWER']==3; assert runpy.run_path('src/left.py')['VALUE']==1"]},
            },
            "baseline_checks": ["baseline"], "final_checks": ["final"],
            "max_process_seconds": 30, "lease_seconds": 120,
        }
        self.e = Engine.setup(root / "control", self.repo, self.policy)
        self.spec = {"id": "feature", "request": "Deliver a working feature", "outcome": "Feature works with API",
                     "acceptance": {"ac-user": "API produces the intended result"}, "constraints": ["Keep public compatibility"],
                     "direction": "Separate persisted values from the API", "epics": [
                         {"id": "values", "title": "Values", "outcome": "Set internal values", "contributes_to": ["ac-user"]},
                         {"id": "api", "title": "API", "outcome": "Expose verified values", "depends_on": ["values"], "contributes_to": ["ac-user"]}]}

    def approve(self, req):
        return self.e.approve(sign(req, self.key, "approve", "test-operator"))

    def begin(self):
        self.approve(self.e.begin(self.spec))

    def task(self, tid, file, check, action="modify", with_doc=False):
        sources = [{"kind": "code", "path": "src/" + ("left.py" if action == "create" else file), "reason": "Actual implementation to change"}]
        if with_doc:
            sources.append({"kind": "knowledge", "path": "docs/architecture.md", "reason": "Relevant architecture constraint"})
        return {"id": tid, "goal": "Implement " + tid, "acceptance": {"ac-" + tid: "Required value is present"},
                "current_state": "Inspect existing values", "approach": "Use the existing plain Python module",
                "decisions": ["Preserve the module interface"], "invariants": ["No side effects on import"],
                "allowed_choices": ["Local variable spelling"], "failure_modes": ["Missing dependency must fail explicitly"],
                "edits": [{"path": "src/" + file, "action": action, "how": "Apply the declared value/behavior change"}],
                "context": sources,
                "verification": [{"criterion": "ac-" + tid, "scenario": "Read module", "expected": "The specified result", "checks": [check]}],
                "escalation": ["Stop if public compatibility must change"], "open_questions": []}

    def plan1(self):
        return {"initiative_id": "feature", "epic_id": "values", "based_on": self.e.state()["head"],
                "goal": "Set internal values", "shared_design": "Independent value modules; no shared mutable state",
                "acceptance": {"ac-values": "Both values available"}, "acceptance_checks": {"ac-values": ["left", "right"]},
                "tasks": [self.task("left", "left.py", "left", with_doc=True), self.task("right", "right.py", "right")]}

    def activate(self, ticket):
        p = self.e.store.get_artifact(ticket["packet_id"])
        self.e.activate(ticket["id"], {"packet_fingerprint": p["fingerprint"], "understood_goal": p["task"]["goal"],
                                       "fixed_decisions": p["task"]["decisions"], "acceptance_ids": list(p["task"]["acceptance"]), "questions": []})
        return p

    def perform(self, tid, contents):
        t = self.e.claim(tid); self.activate(t)
        for p, value in contents.items():
            f = Path(t["workspace"]) / p
            f.parent.mkdir(parents=True, exist_ok=True)
            if value is None:
                f.unlink()
            else:
                f.write_text(value)
        return self.e.submit(t["id"], {"status": "completed", "summary": "Implemented assigned design"})

    def pass_review(self, scope="epic"):
        req = self.e.review_request(scope)
        return self.e.record_review({"request_id": req["id"], "reviewer": "independent-test-reviewer", "complete": True,
                                     "covered_paths": req["required_paths"], "findings": [], "summary": "No significant findings in exact target"})

    def checkpoint1(self):
        return {"epic_id": "values", "based_on": self.e.state()["head"], "report": "Reconciled actual value behavior",
                "entries": [{"target": "docs/architecture.md", "action": "replace", "content": "# Architecture\nThe left value is one.\n",
                             "artifacts": ["src/left.py"], "checks": ["left"], "reason": "Verified change to the value"}],
                "dispositions": [{"path": "src/left.py", "targets": ["docs/architecture.md"], "reason": "Changes documented behavior"},
                                 {"path": "src/right.py", "targets": [], "reason": "Internal numeric fixture; no canonical claim affected"}]}

    def finish_first(self):
        self.begin(); self.approve(self.e.plan(self.plan1()))
        assert self.perform("left", {"src/left.py": "VALUE = 1\n"})["status"] == "integrated"
        assert self.perform("right", {"src/right.py": "VALUE = 2\n"})["status"] == "integrated"
        self.pass_review()
        self.e.checkpoint(self.checkpoint1())

    def finish_second(self):
        task = self.task("api", "api.py", "api", action="create", with_doc=True)
        p = {"initiative_id": "feature", "epic_id": "api", "based_on": self.e.state()["head"],
             "goal": "Expose values", "shared_design": "Use the actual verified first-epic result",
             "acceptance": {"ac-api": "API available"}, "acceptance_checks": {"ac-api": ["api"]}, "tasks": [task]}
        self.approve(self.e.plan(p))
        assert self.perform("api", {"src/api.py": "ANSWER = 3\n"})["status"] == "integrated"
        self.pass_review()
        self.e.checkpoint({"epic_id": "api", "based_on": self.e.state()["head"], "report": "Document verified API",
                           "entries": [{"target": "docs/api.md", "action": "replace", "content": "# API\nThe answer is three.\n",
                                        "artifacts": ["src/api.py"], "checks": ["api"], "reason": "New verified interface"}],
                           "dispositions": [{"path": "src/api.py", "targets": ["docs/api.md"], "reason": "Adds an interface"}]})


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)
