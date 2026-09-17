import tomllib
from pathlib import Path


def _declared_requirements() -> set[str]:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    runtime = set(project.get("dependencies", ()))
    dev = set(project.get("optional-dependencies", {}).get("dev", ()))
    return runtime | dev


def _bootstrap_requirements() -> set[str]:
    lines = Path("third_party/bootstrap-requirements.in").read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}


def test_project_dependency_contract_is_available_in_offline_bootstrap_set():
    declared = _declared_requirements()
    bootstrap = _bootstrap_requirements()
    missing = sorted(declared - bootstrap)
    assert not missing, f"project dependencies absent from exact offline bootstrap set: {missing}"
