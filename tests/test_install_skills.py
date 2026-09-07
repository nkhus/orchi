from pathlib import Path
import importlib.util
import json
import re
import subprocess
import sys
import yaml
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('orchi_installer',ROOT/'tools/install.py');installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)


def test_fresh_install_preserves_user_files(tmp_path):
    (tmp_path/'AGENTS.md').write_text('User rules'); (tmp_path/'.codex').mkdir(); (tmp_path/'.codex/config.toml').write_text('model="operator-model"')
    r=installer.install(tmp_path)
    assert r['status']=='installed';assert (tmp_path/'AGENTS.md').read_text()=='User rules'
    assert (tmp_path/'.codex/config.toml').read_text()=='model="operator-model"'
    assert sorted(p.name for p in (tmp_path/'.agents/skills').iterdir())==sorted(installer.NAMES)
    assert installer.install(tmp_path)['status']=='unchanged'
    p=subprocess.run([sys.executable,str(tmp_path/'.agents/skills/orchi/scripts/orchi.py'),'doctor'],capture_output=True,text=True)
    assert p.returncode==0 and json.loads(p.stdout)['result']['status']=='ready'


def test_dry_run_no_mutation(tmp_path):
    installer.install(tmp_path,dry=True);assert list(tmp_path.iterdir())==[]


def test_modified_skill_refuses_silent_overwrite(tmp_path):
    installer.install(tmp_path);f=tmp_path/'.agents/skills/orchi/SKILL.md';f.write_text('User customizations')
    with pytest.raises(ValueError): installer.install(tmp_path)
    r=installer.install(tmp_path,replace=True)
    assert (Path(r['backup'])/'orchi/SKILL.md').read_text()=='User customizations'


def test_unrelated_skills_are_preserved(tmp_path):
    other=tmp_path/'.agents/skills/custom-skill';other.mkdir(parents=True);(other/'SKILL.md').write_text('User skill')
    installer.install(tmp_path)
    assert (other/'SKILL.md').read_text()=='User skill'


def test_install_symlink_rejected(tmp_path):
    out=tmp_path/'outside';out.mkdir();project=tmp_path/'project';project.mkdir();(project/'.agents').symlink_to(out,target_is_directory=True)
    with pytest.raises(ValueError): installer.install(project)
    assert list(out.iterdir())==[]

@pytest.mark.parametrize('name',installer.NAMES)
def test_skill_contracts_and_links(name):
    folder=ROOT/'skills'/name; text=(folder/'SKILL.md').read_text()
    metadata=yaml.safe_load(text.split('---',2)[1]); assert metadata['name']==name
    assert metadata['description'] and len(text.splitlines())<60
    ui=yaml.safe_load((folder/'agents/openai.yaml').read_text())
    assert 25<=len(ui['interface']['short_description'])<=64
    assert '$'+name in ui['interface']['default_prompt']
    assert ui['policy']['allow_implicit_invocation']==(name=='orchi')
    for link in re.findall(r'\]\(([^)]+)\)',text): assert (folder/link).exists(),link


def test_generated_schemas_equal_models():
    from orchi_core.models import CONTRACTS
    for name,model in CONTRACTS.items():
        assert json.loads((ROOT/'schemas'/(name+'.schema.json')).read_text())==model.model_json_schema()
