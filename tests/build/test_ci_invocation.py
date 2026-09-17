from pathlib import Path


def test_offline_workflow_invokes_verifier_and_bootstrap_as_modules():
    workflow = Path(".github/workflows/build-offline-bundles.yml").read_text(encoding="utf-8")
    assert "python -m tools.verify_wheelhouse" in workflow
    assert "python -m tools.bootstrap_offline" in workflow
    assert "python -m tools.build_wheelhouse" not in workflow
    assert "python tools/bootstrap_offline.py" not in workflow


def test_offline_workflow_binds_verification_to_trigger_sha_and_cancels_stale_runs():
    workflow = Path(".github/workflows/build-offline-bundles.yml").read_text(encoding="utf-8")
    assert "ref: ${{ github.sha }}" in workflow
    assert "cancel-in-progress: true" in workflow


def test_offline_workflow_is_read_only_and_not_bound_to_retired_pr2_branch():
    workflow = Path(".github/workflows/build-offline-bundles.yml").read_text(encoding="utf-8")
    assert "impl/scientific-spine-v2" not in workflow
    assert "git push" not in workflow
    assert "contents: read" in workflow


def test_offline_workflow_qualifies_both_committed_platform_bundles():
    workflow = Path(".github/workflows/build-offline-bundles.yml").read_text(encoding="utf-8")
    assert "third_party/wheels/cp312-manylinux_x86_64" in workflow
    assert "third_party/wheels/cp312-win_amd64" in workflow
    assert "qualify-linux:" in workflow
    assert "qualify-windows:" in workflow
