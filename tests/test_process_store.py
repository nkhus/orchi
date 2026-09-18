import sys
import pytest
from orchi_core.process import run
from orchi_core.store import Store
from orchi_core.common import OrchiError


def test_process_returns_real_failure(tmp_path):
    r=run([sys.executable,'-c','raise SystemExit(7)'],tmp_path,5,1024)
    assert r['returncode']==7 and not r['passed']


def test_process_timeout(tmp_path):
    r=run([sys.executable,'-c','import time; time.sleep(8)'],tmp_path,1,1024)
    assert r['stopped']=='timeout' and not r['passed']


def test_process_output_limit(tmp_path):
    r=run([sys.executable,'-c','print("X"*20000)'],tmp_path,5,1024)
    assert r['stopped']=='output_limit' and not r['passed']


def test_environment_not_inherited(tmp_path,monkeypatch):
    monkeypatch.setenv('PRIVATE_TEST_SECRET','do-not-propagate')
    r=run([sys.executable,'-c','import os; assert "PRIVATE_TEST_SECRET" not in os.environ'],tmp_path,5,1024)
    assert r['passed']


def test_transaction_rolls_back(tmp_path):
    s=Store(tmp_path/'control'); s.initialize({'x':1})
    with pytest.raises(RuntimeError):
        with s.transaction('test') as state:
            state['x']=2; raise RuntimeError('interrupted')
    assert s.read()['x']==1


def test_artifact_tampering_detected(tmp_path):
    s=Store(tmp_path/'control'); oid=s.artifact({'a':1}); (s.root/'artifacts'/f'{oid}.json').write_text('{"a":2}')
    with pytest.raises(OrchiError, check=lambda e: e.code=='ARTIFACT_CORRUPT'): s.get_artifact(oid)


def test_concurrent_identical_artifacts_are_atomically_visible(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    s=Store(tmp_path/'control'); value={'body':'x'*200_000}
    def write_and_read(_):
        oid=s.artifact(value)
        assert s.get_artifact(oid)==value
        return oid
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(write_and_read,range(32)))
    assert len(set(results))==1
    assert not list((s.root/'artifacts').glob('.pending-*'))
