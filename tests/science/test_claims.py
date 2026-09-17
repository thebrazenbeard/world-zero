import pytest

from worldzero.science.claims import ClaimRecord, ClaimRegistry, SourceRef


def test_claim_revision_preserves_old_revision():
    registry = ClaimRegistry()
    registry.add(ClaimRecord(
        claim_id="C007", revision=1,
        proposition="Rebound may be material.",
        evidence_class="DISPUTED",
    ))
    registry.add(ClaimRecord(
        claim_id="C007", revision=2,
        proposition="Rebound magnitude is sector- and horizon-sensitive.",
        evidence_class="INFERRED",
        supersedes_revision=1,
    ))
    assert registry.get("C007", 1).proposition == "Rebound may be material."
    assert registry.current("C007").revision == 2


def test_duplicate_claim_revision_is_rejected():
    registry = ClaimRegistry()
    claim = ClaimRecord(
        claim_id="C001", revision=1, proposition="A", evidence_class="OBSERVED"
    )
    registry.add(claim)
    with pytest.raises(ValueError, match="duplicate"):
        registry.add(claim)


def test_missing_superseded_revision_is_rejected():
    registry = ClaimRegistry()
    with pytest.raises(ValueError, match="supersedes"):
        registry.add(ClaimRecord(
            claim_id="C002", revision=2,
            proposition="B", evidence_class="INFERRED",
            supersedes_revision=1,
        ))


def test_source_refs_round_trip_through_claim():
    claim = ClaimRecord(
        claim_id="C003", revision=1,
        proposition="Observed series exists.", evidence_class="OBSERVED",
        sources=(SourceRef(source_id="SERIES_A", locator="doi:example"),),
    )
    assert claim.sources[0].source_id == "SERIES_A"
