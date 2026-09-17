import pytest

from worldzero.science.claims import ClaimRecord, ClaimRegistry, SourceRef
from worldzero.science.types import EvidenceClass


def test_claim_revision_preserves_old_revision():
    registry = ClaimRegistry()
    registry.add(
        ClaimRecord(
            claim_id="C007",
            revision=1,
            proposition="Rebound may be material.",
            evidence_class=EvidenceClass.DISPUTED,
        )
    )
    registry.add(
        ClaimRecord(
            claim_id="C007",
            revision=2,
            proposition="Rebound magnitude is sector- and horizon-sensitive.",
            evidence_class=EvidenceClass.INFERRED,
            supersedes_revision=1,
        )
    )
    assert registry.get("C007", 1).proposition == "Rebound may be material."
    assert registry.current("C007").revision == 2


def test_duplicate_revision_is_rejected():
    registry = ClaimRegistry()
    claim = ClaimRecord(
        claim_id="C001",
        revision=1,
        proposition="A proposition.",
        evidence_class=EvidenceClass.HYPOTHESIS,
    )
    registry.add(claim)
    with pytest.raises(ValueError, match="duplicate"):
        registry.add(claim)


def test_missing_superseded_revision_is_rejected():
    registry = ClaimRegistry()
    with pytest.raises(ValueError, match="superseded revision"):
        registry.add(
            ClaimRecord(
                claim_id="C001",
                revision=2,
                proposition="A revised proposition.",
                evidence_class=EvidenceClass.INFERRED,
                supersedes_revision=1,
            )
        )


def test_source_ref_is_content_bearing_not_just_free_text():
    source = SourceRef(source_id="DOI:10.1111/jiec.13084", locator="abstract")
    claim = ClaimRecord(
        claim_id="C002",
        revision=1,
        proposition="Empirical series can be compared with scenario trajectories.",
        evidence_class=EvidenceClass.OBSERVED,
        sources=(source,),
    )
    assert claim.sources[0].source_id == "DOI:10.1111/jiec.13084"
