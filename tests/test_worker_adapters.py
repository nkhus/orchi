"""Provider adapters use real subprocesses with synthetic results, not live models."""
import json
from pathlib import Path
import sys

import pytest

from orchi_core.common import OrchiError
from orchi_core.runner import _phase, execute_ticket, run_ready, validate_adapter


def fake_adapter(world, monkeypatch, provider, failure=None):
    executable = world.root / "fake-provider"
    executable.write_text("#!" + sys.executable + "\n" + Path(__file__).with_name("fake_provider.py").read_text())
    executable.chmod(0o700)
    monkeypatch.setenv("ORCHI_TEST_PROVIDER", provider)
    if failure:
        monkeypatch.setenv("ORCHI_TEST_FAILURE", failure)
    return {"kind": provider, "executable": str(executable), "pass_env": ["ORCHI_TEST_PROVIDER", "ORCHI_TEST_FAILURE"]}


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot"])
def test_provider_executes_exact_approved_packets(world, monkeypatch, provider):
    world.begin(); world.approve(world.e.plan(world.plan1()))
    adapter = fake_adapter(world, monkeypatch, provider)
    result = run_ready(world.e, adapter)
    assert len(result["outcomes"]) == 2
    assert all(item["status"] == "integrated" for item in result["outcomes"])
    assert result["next"]["action"] == "request_epic_review"


@pytest.mark.parametrize("provider", ["claude", "copilot"])
@pytest.mark.parametrize("failure", ["process", "schema", "text", "fingerprint", "questions", "write-in-prepare"])
def test_failed_preparation_never_runs_execution(world, monkeypatch, provider, failure):
    world.begin(); world.approve(world.e.plan(world.plan1()))
    before = world.e.state()["head"]
    ticket = world.e.claim("left")
    adapter = fake_adapter(world, monkeypatch, provider, failure)
    result = execute_ticket(str(world.e.store.root), ticket, adapter)
    assert result["status"] == "blocked"
    assert world.e.state()["head"] == before
    assert not (Path(ticket["workspace"]).parent / "output/execute.argv.json").exists()


def test_claude_error_envelope_is_not_success(world, monkeypatch):
    world.begin(); world.approve(world.e.plan(world.plan1()))
    ticket = world.e.claim("left")
    adapter = fake_adapter(world, monkeypatch, "claude", "model")
    result = execute_ticket(str(world.e.store.root), ticket, adapter)
    assert result["status"] == "blocked" and result["code"] == "WORKER_MODEL_FAILED"


@pytest.mark.parametrize("provider", ["claude", "copilot"])
def test_prepare_is_read_only_even_with_broad_execution_permissions(world, monkeypatch, provider):
    world.begin(); world.approve(world.e.plan(world.plan1()))
    ticket = world.e.claim("left")
    adapter = fake_adapter(world, monkeypatch, provider)
    adapter["allowed_tools"] = ["Bash", "Write"] if provider == "claude" else ["shell", "write"]
    _phase(world.e, ticket, adapter, "prepare")
    argv = json.loads((Path(ticket["workspace"]).parent / "output/prepare.argv.json").read_text())
    if provider == "claude":
        assert argv[argv.index("--tools") + 1] == "Read,Glob,Grep"
        assert argv[argv.index("--allowedTools") + 1] == "Read,Glob,Grep"
        assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    else:
        assert argv[argv.index("--available-tools") + 1] == "view,glob,grep"
        assert argv[argv.index("--deny-tool") + 1] == "write,shell"
    assert not {"--yolo", "--allow-all", "--dangerously-skip-permissions"}.intersection(argv)
    with pytest.raises(OrchiError, match="existing phase result"):
        _phase(world.e, ticket, adapter, "prepare")


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot"])
def test_missing_executable_fails_before_claim(world, monkeypatch, provider):
    monkeypatch.setattr("orchi_core.runner.shutil.which", lambda _: None)
    with pytest.raises(OrchiError) as exc:
        run_ready(world.e, {"kind": provider})
    assert exc.value.code == provider.upper() + "_NOT_INSTALLED"


@pytest.mark.parametrize("value", [None, [], {"kind": []}, {"kind": "claude", "pass_env": "HOME"},
                                   {"kind": "copilot", "allowed_tools": "shell"},
                                   {"kind": "codex", "allowed_tools": ["*"]}])
def test_malformed_adapter_is_rejected(value):
    with pytest.raises(OrchiError) as exc:
        validate_adapter(value)
    assert exc.value.code == "INVALID_ADAPTER"
