from pathlib import Path


def test_offline_workflow_invokes_repo_tools_as_modules():
    workflow = Path('.github/workflows/build-offline-bundles.yml').read_text(encoding='utf-8')
    assert 'python -m tools.build_wheelhouse' in workflow
    assert 'python -m tools.verify_wheelhouse' in workflow
    assert 'python -m tools.bootstrap_offline' in workflow
    assert 'python tools/build_wheelhouse.py' not in workflow
    assert 'python tools/bootstrap_offline.py' not in workflow
