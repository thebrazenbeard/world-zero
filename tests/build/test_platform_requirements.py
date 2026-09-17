from pathlib import Path


def test_bootstrap_requirements_include_windows_pytest_support():
    requirements = Path("third_party/bootstrap-requirements.in").read_text(encoding="utf-8")
    assert "colorama==0.4.6" in requirements
