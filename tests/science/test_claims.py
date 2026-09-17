import importlib
import importlib.util

import pytest


def _claims():
    if importlib.util.find_spec("worldzero.science.claims") is None:
        pytest.fail("worldzero.science.claims is not implemented")
    return importlib.import_module("worldzero.science.claims")


def test_claim_revision_preserves_old_revision():
    module = _claims()
    registry = module.ClaimRegistry()
    registry.add(
        module.ClaimRecord(
            claim_id="C007",
            revision=1,
            proposition="Rebound may be material.",
            evidence_class="DISPUTED",
        )
    )
    registry.add(
        module.ClaimRecord(
            claim_id="C007",
            revision=2,
            proposition="Rebound magnitude is sector- and horizon-sensitive.",
            evidence_class="INFERRED",
            supersedes_revision=1,
        )
    )
    assert registry.get("C007", 1).proposition == "Rebound may be material."
    assert registry.current("C007").revision == 2


def test_duplicate_claim_revision_is_rejected():
    module = _claims()
    registry = module.ClaimRegistry()
    claim = module.ClaimRecord(
        claim_id="C001",
        revision=1,
        proposition="A proposition.",
        evidence_class="OBSERVED",
    )
    registry.add(claim)
    with pytest.raises(ValueError, match="duplicate"):
        registry.add(claim)


def test_supersedes_revision_must_exist():
    module = _claims()
    registry = module.ClaimRegistry()
    with pytest.raises(ValueError, match="supersedes"):
        registry.add(
            module.ClaimRecord(
                claim_id="C001",
                revision=2,
                proposition="A revision.",
                evidence_class="INFERRED",
                supersedes_revision=1,
            )
        )
