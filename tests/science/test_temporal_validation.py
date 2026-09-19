from pathlib import Path

import pytest

from worldzero.models.scenarios import load_scenario_manifest
from worldzero.science.population_evidence import (
    PopulationEvidenceCatalog,
    PopulationEvidenceObservation,
)
from worldzero.science.temporal_validation import (
    TemporalPopulationValidationSubject,
    verify_temporal_population_validation_subject,
)


def _observation(
    observation_id: str,
    *,
    year: int,
    region_id: str,
    cohort_id: str,
) -> PopulationEvidenceObservation:
    return PopulationEvidenceObservation(
        observation_id=observation_id,
        role="POPULATION_COHORT",
        dataset_id=f"cohort-{year}",
        manifest_path=f"data/manifests/cohort-{year}.yaml",
        manifest_sha256="a" * 64,
        output_sha256="b" * 64,
        year=year,
        region_id=region_id,
        cohort_id=cohort_id,
        source_observation_class="OFFICIAL_ESTIMATE",
        validation_eligible=True,
        evidence_covariance_group_id="UN_WPP_2024_POPULATION_FAMILY",
    )


def _catalog(catalog_id: str, year: int) -> PopulationEvidenceCatalog:
    return PopulationEvidenceCatalog(
        schema_version="WZ_POPULATION_EVIDENCE_CATALOG_V1",
        catalog_id=catalog_id,
        frozen_before_execution=True,
        region_set_version="WZ_MACROREGION_V0",
        cohort_set_version="WZ_AGE_COHORT_V0",
        observations=(
            _observation(
                f"cohort-{year}-north-child",
                year=year,
                region_id="north",
                cohort_id="child",
            ),
            _observation(
                f"cohort-{year}-south-child",
                year=year,
                region_id="south",
                cohort_id="child",
            ),
        ),
    )


def _subject() -> TemporalPopulationValidationSubject:
    return TemporalPopulationValidationSubject(
        schema_version="WZ_TEMPORAL_POPULATION_VALIDATION_SUBJECT_V1",
        subject_id="WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_VALIDATION_V1",
        frozen_before_execution=True,
        initialization_catalog_id="INIT-2022",
        holdout_catalog_id="HOLD-2023",
        initialization_year=2022,
        holdout_year=2023,
        region_set_version="WZ_MACROREGION_V0",
        cohort_set_version="WZ_AGE_COHORT_V0",
        initialization_observation_ids=(
            "cohort-2022-north-child",
            "cohort-2022-south-child",
        ),
        holdout_observation_ids=(
            "cohort-2023-north-child",
            "cohort-2023-south-child",
        ),
    )


def test_temporal_subject_accepts_complete_disjoint_2022_to_2023_cohort_cuts():
    subject = _subject()
    assert (
        verify_temporal_population_validation_subject(
            subject=subject,
            initialization_catalog=_catalog("INIT-2022", 2022),
            holdout_catalog=_catalog("HOLD-2023", 2023),
        )
        is subject
    )


def test_temporal_subject_requires_holdout_after_initialization():
    payload = _subject().model_dump()
    payload["initialization_year"] = 2023
    payload["holdout_year"] = 2022
    with pytest.raises(ValueError, match="strictly after"):
        TemporalPopulationValidationSubject.model_validate(payload)


def test_temporal_subject_rejects_incomplete_initialization_cut():
    subject = _subject().model_copy(
        update={"initialization_observation_ids": ("cohort-2022-north-child",)}
    )
    with pytest.raises(ValueError, match="complete governed cohort cut"):
        verify_temporal_population_validation_subject(
            subject=subject,
            initialization_catalog=_catalog("INIT-2022", 2022),
            holdout_catalog=_catalog("HOLD-2023", 2023),
        )


def test_temporal_subject_rejects_incomplete_holdout_cut():
    subject = _subject().model_copy(
        update={"holdout_observation_ids": ("cohort-2023-north-child",)}
    )
    with pytest.raises(ValueError, match="complete governed cohort cut"):
        verify_temporal_population_validation_subject(
            subject=subject,
            initialization_catalog=_catalog("INIT-2022", 2022),
            holdout_catalog=_catalog("HOLD-2023", 2023),
        )


def test_temporal_subject_rejects_catalog_identity_substitution():
    with pytest.raises(ValueError, match="initialization catalog identity mismatch"):
        verify_temporal_population_validation_subject(
            subject=_subject(),
            initialization_catalog=_catalog("OTHER-2022", 2022),
            holdout_catalog=_catalog("HOLD-2023", 2023),
        )


def test_temporal_subject_rejects_wrong_year_catalog():
    with pytest.raises(ValueError, match="no governed cohort observations"):
        verify_temporal_population_validation_subject(
            subject=_subject(),
            initialization_catalog=_catalog("INIT-2022", 2021),
            holdout_catalog=_catalog("HOLD-2023", 2023),
        )


def test_temporal_subject_rejects_direct_observation_id_overlap():
    payload = _subject().model_dump()
    payload["holdout_observation_ids"] = ("cohort-2022-north-child",)
    with pytest.raises(ValueError, match="initialization/temporal-holdout overlap"):
        TemporalPopulationValidationSubject.model_validate(payload)


def test_2022_to_2023_candidate_scenario_stays_non_executable_until_binding_exists():
    scenario = load_scenario_manifest(
        Path("scenarios/validation/2022_to_2023_demography_temporal_holdout.yaml")
    )
    assert scenario.scenario_class == "NATIVE_BASELINE"
    assert scenario.status == "DATA_BINDING_REQUIRED"
    assert not scenario.executable
    assert scenario.start == 2022.0
    assert scenario.stop == 2023.0
    assert scenario.data_manifest_id is None
    assert scenario.parameter_set_id is None
