from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_digest_bound_manifests_are_forced_to_lf_checkout() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "data/manifests/**/*.yaml text eol=lf" in attributes


def test_offline_qualification_commands_are_independent_steps() -> None:
    workflow = (ROOT / ".github/workflows/build-offline-bundles.yml").read_text(
        encoding="utf-8"
    )

    assert "- name: Test Windows reconstruction" in workflow
    assert "- name: Lint Windows reconstruction" in workflow
    assert "- name: Type-check Windows reconstruction" in workflow
    assert "- name: Test Linux reconstruction" in workflow
    assert "- name: Lint Linux reconstruction" in workflow
    assert "- name: Type-check Linux reconstruction" in workflow

    assert "name: Qualify Windows reconstruction" not in workflow
    assert "name: Qualify Linux reconstruction" not in workflow
