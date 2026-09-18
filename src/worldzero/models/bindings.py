"""Governed data and provisional-parameter bindings for the native V0 baseline."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from worldzero.data.cohorts import load_age_cohort_manifest
from worldzero.data.derived import DerivedDatasetManifest, load_derived_dataset_manifest
from worldzero.data.manifests import DatasetAdmissionStatus
from worldzero.data.wpp_age5 import COHORT_POPULATION_CSV_FIELDS
from worldzero.models.environment import RegionalEnvironmentParams
from worldzero.models.native_backbone import NativeBackboneConfig
from worldzero.models.scenarios import load_scenario_manifest
from worldzero.models.world_zero_v0 import WorldZeroV0Config
from worldzero.regions.definitions import load_region_set_manifest
from worldzero.sectors.demography import AgeCohort, DemographyRates, MigrationLink
from worldzero.sectors.distribution import DistributionParams
from worldzero.sectors.food_land import FoodProductionParams, SoilDynamicsParams
from worldzero.sectors.institutions import InstitutionParams
from worldzero.sectors.production import ProductionParams
from worldzero.sectors.trade import TradeLink

TOTAL_POPULATION_CSV_FIELDS = (
    "region_id",
    "year",
    "population_persons",
    "source_observation_class",
    "observation_class",
    "validation_eligible",
)
_REQUIRED_POPULATION_ROLES = {"POPULATION_TOTAL", "POPULATION_COHORT"}


class DatasetBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["POPULATION_TOTAL", "POPULATION_COHORT"]
    dataset_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)


class BaselineDataBundleManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_DATA_BUNDLE_V1"]
    data_manifest_id: str = Field(min_length=1)
    status: Literal["BINDING_REQUIRED", "READY"]
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str = Field(min_length=1)
    year: int
    population_reconciliation_tolerance_persons: float = Field(ge=0)
    bindings: tuple[DatasetBinding, ...]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_bindings(self) -> BaselineDataBundleManifest:
        roles = [binding.role for binding in self.bindings]
        if len(roles) != len(set(roles)):
            raise ValueError("data bundle roles must be unique")
        if self.status == "READY" and set(roles) != _REQUIRED_POPULATION_ROLES:
            raise ValueError("READY baseline bundle requires total and cohort population bindings")
        return self

    @property
    def binding_by_role(self) -> dict[str, DatasetBinding]:
        return {binding.role: binding for binding in self.bindings}


class CohortRates(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    child: float = Field(ge=0)
    young_adult: float = Field(ge=0)
    mature_adult: float = Field(ge=0)
    older_adult: float = Field(ge=0)

    def as_mapping(self) -> dict[AgeCohort, float]:
        return {
            AgeCohort.CHILD: self.child,
            AgeCohort.YOUNG_ADULT: self.young_adult,
            AgeCohort.MATURE_ADULT: self.mature_adult,
            AgeCohort.OLDER_ADULT: self.older_adult,
        }


class DemographyExecutionParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    birth_rate_per_young_adult: float = Field(ge=0)
    mortality: CohortRates
    ageing: CohortRates

    @model_validator(mode="after")
    def validate_ageing(self) -> DemographyExecutionParameters:
        if self.ageing.older_adult != 0:
            raise ValueError("older_adult ageing must be zero")
        return self


class ProductionExecutionParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    productive_capital_per_person: float = Field(ge=0)
    service_capital_per_person: float = Field(ge=0)
    capital_output_ratio: float = Field(gt=0)
    labor_productivity: float = Field(ge=0)
    investment_share: float = Field(ge=0, le=1)
    service_investment_fraction: float = Field(ge=0, le=1)
    productive_depreciation_rate: float = Field(ge=0)
    service_depreciation_rate: float = Field(ge=0)


class EnvironmentExecutionParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    productive_land_per_person: float = Field(ge=0)
    bioenergy_land_per_person: float = Field(ge=0)
    initial_soil_condition: float = Field(ge=0, le=1)
    soil_degradation_rate: float = Field(ge=0)
    soil_recovery_rate: float = Field(ge=0)
    soil_degradation_pressure: float = Field(ge=0)
    soil_restoration_effort: float = Field(ge=0)
    renewable_water_per_person: float = Field(ge=0)
    irrigation_demand_per_person: float = Field(ge=0)
    other_water_demand_per_person: float = Field(ge=0)
    nutrient_input_per_person: float = Field(ge=0)
    food_energy_input_per_person: float = Field(ge=0)
    base_yield_per_land: float = Field(ge=0)
    managed_input_gain: float = Field(ge=0)
    water_half_saturation_per_person: float = Field(gt=0)
    nutrient_half_saturation_per_person: float = Field(gt=0)
    energy_half_saturation_per_person: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_land(self) -> EnvironmentExecutionParameters:
        if self.bioenergy_land_per_person > self.productive_land_per_person:
            raise ValueError("bioenergy land cannot exceed productive land")
        return self


class RegionExecutionParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    demography: DemographyExecutionParameters
    production: ProductionExecutionParameters
    labor_share: float = Field(ge=0, le=1)
    environment: EnvironmentExecutionParameters
    food_requirement_per_person: float = Field(ge=0)


class MigrationLinkSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_region: str = Field(min_length=1)
    target_region: str = Field(min_length=1)
    annual_fraction: float = Field(ge=0, le=1)


class FoodTradeLinkSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    capacity: float = Field(ge=0)
    loss_fraction: float = Field(ge=0, le=1)
    enabled: bool = True


class InstitutionExecutionParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    response_capacity: float = Field(ge=0, le=1)
    implementation_delay: float = Field(ge=0)


class BaselineParameterSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["WORLD_ZERO_V0_EXECUTION_PARAMETER_SET_V1"]
    parameter_set_id: str = Field(min_length=1)
    status: Literal["PROVISIONAL_EXECUTION"]
    evidence_class: Literal["MODELING_ASSUMPTION"]
    region_set_version: str = Field(min_length=1)
    cohort_set_version: str = Field(min_length=1)
    default_region: RegionExecutionParameters
    region_overrides: dict[str, RegionExecutionParameters] = Field(default_factory=dict)
    migration_links: tuple[MigrationLinkSpec, ...]
    food_trade_links: tuple[FoodTradeLinkSpec, ...]
    institutions: InstitutionExecutionParameters
    notes: str | None = None


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load_baseline_data_bundle_manifest(path: Path) -> BaselineDataBundleManifest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("baseline data bundle must be a mapping")
    return BaselineDataBundleManifest.model_validate(payload)


def load_baseline_parameter_set(path: Path) -> BaselineParameterSet:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("baseline parameter set must be a mapping")
    return BaselineParameterSet.model_validate(payload)


def _verified_output_path(root: Path, manifest: DerivedDatasetManifest) -> Path:
    path = _resolve(root, Path(manifest.output_path))
    payload = path.read_bytes()
    if len(payload) != manifest.output_length_bytes:
        raise ValueError(f"derived artifact length mismatch: {manifest.dataset_id}")
    if hashlib.sha256(payload).hexdigest() != manifest.output_sha256:
        raise ValueError(f"derived artifact digest mismatch: {manifest.dataset_id}")
    return path


def _load_bound_manifest(
    root: Path,
    binding: DatasetBinding,
) -> DerivedDatasetManifest:
    manifest = load_derived_dataset_manifest(_resolve(root, Path(binding.manifest_path)))
    if manifest.dataset_id != binding.dataset_id:
        raise ValueError(f"dataset binding identity mismatch: {binding.role}")
    if manifest.admission_status is not DatasetAdmissionStatus.ADMITTED:
        raise ValueError(f"bound derived dataset must be ADMITTED: {binding.role}")
    if manifest.unit != "persons":
        raise ValueError(f"bound population dataset unit must be persons: {binding.role}")
    return manifest


def _parse_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("CSV boolean must be lowercase true or false")


def _load_total_population(
    path: Path,
    *,
    manifest: DerivedDatasetManifest,
    year: int,
    region_ids: tuple[str, ...],
) -> dict[str, float]:
    values: dict[str, float] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != TOTAL_POPULATION_CSV_FIELDS:
            raise ValueError("total-population CSV schema does not match frozen contract")
        for row in reader:
            if int(row["year"]) != year:
                raise ValueError("total-population CSV year does not match data bundle")
            if row["source_observation_class"] != manifest.source_observation_class.value:
                raise ValueError("total-population source observation class mismatch")
            if row["observation_class"] != "DERIVED":
                raise ValueError("total-population artifact must be DERIVED")
            if _parse_bool(row["validation_eligible"]) != manifest.validation_eligible:
                raise ValueError("total-population validation flag mismatch")
            region_id = row["region_id"]
            if region_id in values:
                raise ValueError(f"duplicate total-population region: {region_id}")
            value = float(row["population_persons"])
            if value < 0:
                raise ValueError("total population must be nonnegative")
            values[region_id] = value
    if set(values) != set(region_ids):
        raise ValueError("total-population regions must exactly match frozen region set")
    return values


def _load_cohort_population(
    path: Path,
    *,
    manifest: DerivedDatasetManifest,
    year: int,
    region_ids: tuple[str, ...],
) -> dict[str, dict[AgeCohort, float]]:
    values: dict[str, dict[AgeCohort, float]] = {region_id: {} for region_id in region_ids}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COHORT_POPULATION_CSV_FIELDS:
            raise ValueError("cohort-population CSV schema does not match frozen contract")
        for row in reader:
            if int(row["year"]) != year:
                raise ValueError("cohort-population CSV year does not match data bundle")
            if row["source_observation_class"] != manifest.source_observation_class.value:
                raise ValueError("cohort-population source observation class mismatch")
            if row["observation_class"] != "DERIVED":
                raise ValueError("cohort-population artifact must be DERIVED")
            if _parse_bool(row["validation_eligible"]) != manifest.validation_eligible:
                raise ValueError("cohort-population validation flag mismatch")
            region_id = row["region_id"]
            if region_id not in values:
                raise ValueError(f"cohort-population artifact contains unknown region: {region_id}")
            cohort = AgeCohort(row["cohort_id"])
            if cohort in values[region_id]:
                raise ValueError(f"duplicate cohort population row: {region_id}/{cohort.value}")
            value = float(row["population_persons"])
            if value < 0:
                raise ValueError("cohort population must be nonnegative")
            values[region_id][cohort] = value
    expected_cohorts = set(AgeCohort)
    if any(set(region_values) != expected_cohorts for region_values in values.values()):
        raise ValueError("every region must contain every frozen age cohort")
    return values


def resolve_baseline_population(
    *,
    root: Path,
    bundle: BaselineDataBundleManifest,
    region_ids: tuple[str, ...],
) -> dict[str, dict[AgeCohort, float]]:
    if bundle.status != "READY":
        raise ValueError("baseline data bundle is not READY")
    bindings = bundle.binding_by_role
    total_manifest = _load_bound_manifest(root, bindings["POPULATION_TOTAL"])
    cohort_manifest = _load_bound_manifest(root, bindings["POPULATION_COHORT"])

    for manifest in (total_manifest, cohort_manifest):
        if manifest.region_set_version != bundle.region_set_version:
            raise ValueError("derived population region-set version mismatch")
        if manifest.years != (bundle.year,):
            raise ValueError("derived population year does not match data bundle")
    if cohort_manifest.cohort_set_version != bundle.cohort_set_version:
        raise ValueError("cohort artifact does not bind the required cohort-set version")
    if total_manifest.source_observation_class != cohort_manifest.source_observation_class:
        raise ValueError("total and cohort population source classes must match")
    if total_manifest.validation_eligible != cohort_manifest.validation_eligible:
        raise ValueError("total and cohort population validation flags must match")

    total_values = _load_total_population(
        _verified_output_path(root, total_manifest),
        manifest=total_manifest,
        year=bundle.year,
        region_ids=region_ids,
    )
    cohort_values = _load_cohort_population(
        _verified_output_path(root, cohort_manifest),
        manifest=cohort_manifest,
        year=bundle.year,
        region_ids=region_ids,
    )

    tolerance = bundle.population_reconciliation_tolerance_persons
    for region_id in region_ids:
        cohort_total = sum(cohort_values[region_id].values())
        if abs(cohort_total - total_values[region_id]) > tolerance:
            raise ValueError(f"cohort population does not reconcile for {region_id}")
    return cohort_values


def build_world_zero_v0_config(
    *,
    root: Path,
    scenario_path: Path,
    data_bundle_path: Path,
    parameter_set_path: Path,
    region_set_path: Path = Path("regions/WZ_MACROREGION_V0.yaml"),
    cohort_set_path: Path = Path("data/cohorts/WZ_AGE_COHORT_V0.yaml"),
) -> WorldZeroV0Config:
    scenario = load_scenario_manifest(_resolve(root, scenario_path))
    if not scenario.executable or scenario.scenario_class != "NATIVE_BASELINE":
        raise ValueError("runtime loader requires an EXECUTABLE native baseline scenario")

    bundle = load_baseline_data_bundle_manifest(_resolve(root, data_bundle_path))
    parameters = load_baseline_parameter_set(_resolve(root, parameter_set_path))
    if scenario.data_manifest_id != bundle.data_manifest_id:
        raise ValueError("scenario data_manifest_id does not match data bundle")
    if scenario.parameter_set_id != parameters.parameter_set_id:
        raise ValueError("scenario parameter_set_id does not match parameter set")
    if scenario.start != float(bundle.year):
        raise ValueError("scenario start must equal the data-bundle baseline year")

    region_manifest = load_region_set_manifest(_resolve(root, region_set_path))
    cohort_manifest = load_age_cohort_manifest(_resolve(root, cohort_set_path))
    if region_manifest.status.value != "FROZEN":
        raise ValueError("runtime loader requires a FROZEN region set")
    regions = region_manifest.region_set
    expected_region_version = regions.version
    expected_cohort_version = cohort_manifest.version
    if (
        scenario.region_set_version != expected_region_version
        or bundle.region_set_version != expected_region_version
        or parameters.region_set_version != expected_region_version
    ):
        raise ValueError("region-set versions do not resolve to the frozen runtime subject")
    if (
        bundle.cohort_set_version != expected_cohort_version
        or parameters.cohort_set_version != expected_cohort_version
    ):
        raise ValueError("cohort-set versions do not resolve to the frozen runtime subject")
    unknown_overrides = set(parameters.region_overrides) - set(regions.ids)
    if unknown_overrides:
        raise ValueError("parameter-set overrides reference unknown regions")

    initial_population = resolve_baseline_population(
        root=root,
        bundle=bundle,
        region_ids=regions.ids,
    )
    demography: dict[str, DemographyRates] = {}
    production: dict[str, ProductionParams] = {}
    distribution: dict[str, DistributionParams] = {}
    environment: dict[str, RegionalEnvironmentParams] = {}
    food_requirement: dict[str, float] = {}

    for region_id in regions.ids:
        region_parameters = parameters.region_overrides.get(
            region_id,
            parameters.default_region,
        )
        population = sum(initial_population[region_id].values())
        if population <= 0:
            raise ValueError(f"baseline population must be positive for {region_id}")

        demographic = region_parameters.demography
        demography[region_id] = DemographyRates(
            birth_rate_per_young_adult=demographic.birth_rate_per_young_adult,
            mortality=demographic.mortality.as_mapping(),
            ageing=demographic.ageing.as_mapping(),
        )

        productive = region_parameters.production
        production[region_id] = ProductionParams(
            initial_productive_capital=population * productive.productive_capital_per_person,
            initial_service_capital=population * productive.service_capital_per_person,
            capital_output_ratio=productive.capital_output_ratio,
            labor_productivity=productive.labor_productivity,
            investment_share=productive.investment_share,
            service_investment_fraction=productive.service_investment_fraction,
            productive_depreciation_rate=productive.productive_depreciation_rate,
            service_depreciation_rate=productive.service_depreciation_rate,
        )
        distribution[region_id] = DistributionParams(labor_share=region_parameters.labor_share)

        regional_environment = region_parameters.environment
        environment[region_id] = RegionalEnvironmentParams(
            total_productive_land=population
            * regional_environment.productive_land_per_person,
            bioenergy_land=population * regional_environment.bioenergy_land_per_person,
            initial_soil_condition=regional_environment.initial_soil_condition,
            soil=SoilDynamicsParams(
                degradation_rate=regional_environment.soil_degradation_rate,
                recovery_rate=regional_environment.soil_recovery_rate,
            ),
            soil_degradation_pressure=regional_environment.soil_degradation_pressure,
            soil_restoration_effort=regional_environment.soil_restoration_effort,
            renewable_water_supply=population
            * regional_environment.renewable_water_per_person,
            irrigation_demand=population
            * regional_environment.irrigation_demand_per_person,
            other_water_demand=population
            * regional_environment.other_water_demand_per_person,
            nutrient_input=population * regional_environment.nutrient_input_per_person,
            food_energy_input=population
            * regional_environment.food_energy_input_per_person,
            food=FoodProductionParams(
                base_yield_per_land=regional_environment.base_yield_per_land,
                managed_input_gain=regional_environment.managed_input_gain,
                water_half_saturation=population
                * regional_environment.water_half_saturation_per_person,
                nutrient_half_saturation=population
                * regional_environment.nutrient_half_saturation_per_person,
                energy_half_saturation=population
                * regional_environment.energy_half_saturation_per_person,
            ),
        )
        food_requirement[region_id] = region_parameters.food_requirement_per_person

    migration_links = tuple(
        MigrationLink(
            source_region=link.source_region,
            target_region=link.target_region,
            annual_fraction=link.annual_fraction,
        )
        for link in parameters.migration_links
    )
    native = NativeBackboneConfig(
        regions=regions,
        initial_population=initial_population,
        demography_rates=demography,
        migration_links=migration_links,
        production=production,
        distribution=distribution,
        start=scenario.start,
        stop=scenario.stop,
        dt=scenario.dt,
        energy=None,
        materials=None,
        climate=None,
        environment=environment,
    )
    food_trade_links = tuple(
        TradeLink(
            origin=link.origin,
            destination=link.destination,
            capacity=link.capacity,
            loss_fraction=link.loss_fraction,
            enabled=link.enabled,
        )
        for link in parameters.food_trade_links
    )
    institutions = InstitutionParams(
        response_capacity=parameters.institutions.response_capacity,
        implementation_delay=parameters.institutions.implementation_delay,
    )
    return WorldZeroV0Config(
        native=native,
        food_requirement_per_person=food_requirement,
        food_trade_links=food_trade_links,
        institutions=institutions,
        intervention=None,
    )
