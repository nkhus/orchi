import copy
import pytest
from pydantic import ValidationError
from orchi_core.common import OrchiError, path, safe_text
from orchi_core.models import Initiative, Task, EpicPlan, Source, KnowledgeEdit
from orchi_core.context import frontmatter

@pytest.mark.parametrize('value', ['/tmp/a','../a','a/../b','a//b','a\\b','./a','a/*','~/.a','a\x00b','a/','a:foo'])
def test_paths_reject_ambiguous_or_unsafe(value):
    with pytest.raises(OrchiError): path(value)

@pytest.mark.parametrize('value',['src/module.py','tests/api.test.ts','some-folder/\u0444\u0430\u0439\u043b.md'])
def test_paths_accept_exact(value):
    assert path(value) == value

@pytest.mark.parametrize('target',['docs/a.md','.codex/config.toml','.agents/skills/a/SKILL.md','AGENTS.md','src/AGENTS.md','.github/workflows/ci.yml','.env','private.pem','initiatives/active/x/a.md'])
def test_task_cannot_modify_protected_files(world,target):
    t=world.task('t','left.py','left'); t['edits'][0]['path']=target
    with pytest.raises((OrchiError,ValidationError)): Task.model_validate(t)

@pytest.mark.parametrize('field',['approach','decisions','invariants','allowed_choices','failure_modes','current_state','escalation','open_questions'])
def test_task_requires_explicit_design(world,field):
    t=world.task('t','left.py','left'); del t[field]
    with pytest.raises(ValidationError): Task.model_validate(t)

def test_future_epic_cannot_embed_tasks(world):
    spec=copy.deepcopy(world.spec); spec['epics'][1]['tasks']=[]
    with pytest.raises(ValidationError): Initiative.model_validate(spec)

def test_unresolved_design_rejected(world):
    t=world.task('t','left.py','left'); t['open_questions']=['Should we replace storage?']
    with pytest.raises(OrchiError, check=lambda e: e.code=='UNRESOLVED_DESIGN'): Task.model_validate(t)

def test_missing_acceptance_coverage(world):
    t=world.task('t','left.py','left'); t['acceptance']['other']='Other outcome'
    with pytest.raises(OrchiError, check=lambda e: e.code=='INCOMPLETE_ACCEPTANCE'): Task.model_validate(t)

def test_dependency_requires_producer_and_contract():
    with pytest.raises(OrchiError): Source.model_validate({'kind':'dependency','path':'src/x.py','reason':'Input'})

def test_knowledge_edit_action_is_unambiguous():
    with pytest.raises(OrchiError): KnowledgeEdit.model_validate({'target':'docs/x.md','action':'revalidate','content':'new text','artifacts':['src/x.py'],'checks':['test'],'reason':'why'})

def test_yaml_aliases_rejected():
    with pytest.raises(OrchiError): frontmatter('---\na: &a [1,2]\nb: *a\n---\n# X')

def test_secret_content_not_rendered():
    with pytest.raises(OrchiError): safe_text(b'-----BEGIN PRIVATE KEY-----\nredacted', 'fixture.txt')
