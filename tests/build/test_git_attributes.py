from pathlib import Path


def test_wheel_artifacts_are_never_text_normalized():
    attributes = Path(".gitattributes").read_text(encoding="utf-8")
    assert "*.whl -text" in attributes
