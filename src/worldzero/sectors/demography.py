"""Regional cohort demography with explicit births, deaths, ageing, and migration."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import pairwise
from types import MappingProxyType

from worldzero.core import FlowSpec, ModelState, StockId, StockSpec
from worldzero.regions.definitions import RegionSet


class AgeCohort(StrEnum):
    CHILD = "child"
    YOUNG_ADULT = "young_adult"
    MATURE_ADULT = "mature_adult"
    OLDER_ADULT = "older_adult"


_COHORT_ORDER = (
    AgeCohort.CHILD,
    AgeCohort.YOUNG_ADULT,
    AgeCohort.MATURE_ADULT,
    AgeCohort.OLDER_ADULT,
)
_NEXT_COHORT = dict(pairwise(_COHORT_ORDER))


@dataclass(frozen=True, slots=True)
class DemographyRates:
    birth_rate_per_young_adult: float = 0.0
    mortality: Mapping[AgeCohort, float] = field(default_factory=dict)
    ageing: Mapping[AgeCohort, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.birth_rate_per_young_adult < 0:
            raise ValueError("birth rate must be nonnegative")
        mortality = {cohort: float(self.mortality.get(cohort, 0.0)) for cohort in _COHORT_ORDER}
        ageing = {cohort: float(self.ageing.get(cohort, 0.0)) for cohort in _COHORT_ORDER}
        if any(value < 0 for value in mortality.values()):
            raise ValueError("mortality rates must be nonnegative")
        if any(value < 0 for value in ageing.values()):
            raise ValueError("ageing rates must be nonnegative")
        if ageing[AgeCohort.OLDER_ADULT] != 0.0:
            raise ValueError("older-adult cohort cannot age into another cohort")
        object.__setattr__(self, "mortality", MappingProxyType(mortality))
        object.__setattr__(self, "ageing", MappingProxyType(ageing))

    @classmethod
    def zero(
        cls,
        *,
        birth_rate_per_young_adult: float = 0.0,
        mortality: Mapping[AgeCohort, float] | None = None,
        ageing: Mapping[AgeCohort, float] | None = None,
    ) -> DemographyRates:
        return cls(
            birth_rate_per_young_adult=birth_rate_per_young_adult,
            mortality={} if mortality is None else mortality,
            ageing={} if ageing is None else ageing,
        )


@dataclass(frozen=True, slots=True)
class MigrationLink:
    source_region: str
    target_region: str
    annual_fraction: float

    def __post_init__(self) -> None:
        if self.source_region == self.target_region:
            raise ValueError("migration source and target must differ")
        if not 0 <= self.annual_fraction <= 1:
            raise ValueError("migration fraction must be within [0, 1]")


def population_stock_id(region_id: str, cohort: AgeCohort) -> StockId:
    return StockId(f"population:{region_id}:{cohort.value}")


def _cohort_initial(
    initial_population: Mapping[str, Mapping[AgeCohort, float]],
    region_id: str,
    cohort: AgeCohort,
) -> float:
    value = float(initial_population.get(region_id, {}).get(cohort, 0.0))
    if value < 0:
        raise ValueError("initial population must be nonnegative")
    return value


def _proportional_rate(stock_id: StockId, fraction: float) -> Callable[[ModelState, float], float]:
    def rate(state: ModelState, _t: float) -> float:
        return fraction * state.value(stock_id)

    return rate


def build_demography_sector(
    regions: RegionSet,
    *,
    initial_population: Mapping[str, Mapping[AgeCohort, float]],
    rates_by_region: Mapping[str, DemographyRates],
    migration_links: Sequence[MigrationLink] = (),
) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
    stocks: list[StockSpec] = []
    flows: list[FlowSpec] = []
    for region_id in regions.ids:
        rates = rates_by_region.get(region_id)
        if rates is None:
            raise ValueError(f"missing demography rates for {region_id}")
        for cohort in _COHORT_ORDER:
            stock_id = population_stock_id(region_id, cohort)
            stocks.append(
                StockSpec(
                    stock_id,
                    owner="demography",
                    unit="people",
                    initial=_cohort_initial(initial_population, region_id, cohort),
                    region=region_id,
                )
            )
        young_id = population_stock_id(region_id, AgeCohort.YOUNG_ADULT)
        if rates.birth_rate_per_young_adult > 0:
            flows.append(
                FlowSpec(
                    f"births:{region_id}",
                    source=None,
                    target=population_stock_id(region_id, AgeCohort.CHILD),
                    unit_per_time="people/year",
                    rate=_proportional_rate(young_id, rates.birth_rate_per_young_adult),
                )
            )
        for cohort in _COHORT_ORDER:
            stock_id = population_stock_id(region_id, cohort)
            mortality_rate = rates.mortality[cohort]
            if mortality_rate > 0:
                flows.append(
                    FlowSpec(
                        f"deaths:{region_id}:{cohort.value}",
                        source=stock_id,
                        target=None,
                        unit_per_time="people/year",
                        rate=_proportional_rate(stock_id, mortality_rate),
                    )
                )
            ageing_rate = rates.ageing[cohort]
            if ageing_rate > 0:
                flows.append(
                    FlowSpec(
                        f"ageing:{region_id}:{cohort.value}",
                        source=stock_id,
                        target=population_stock_id(region_id, _NEXT_COHORT[cohort]),
                        unit_per_time="people/year",
                        rate=_proportional_rate(stock_id, ageing_rate),
                    )
                )
    region_ids = set(regions.ids)
    for link in migration_links:
        if link.source_region not in region_ids or link.target_region not in region_ids:
            raise ValueError("migration link references undeclared region")
        for cohort in _COHORT_ORDER:
            source_id = population_stock_id(link.source_region, cohort)
            target_id = population_stock_id(link.target_region, cohort)
            flows.append(
                FlowSpec(
                    f"migration:{link.source_region}:{link.target_region}:{cohort.value}",
                    source=source_id,
                    target=target_id,
                    unit_per_time="people/year",
                    rate=_proportional_rate(source_id, link.annual_fraction),
                )
            )
    return tuple(stocks), tuple(flows)


def region_population(state: ModelState, region_id: str) -> float:
    return sum(state.value(population_stock_id(region_id, cohort)) for cohort in _COHORT_ORDER)


def working_age_population(state: ModelState, region_id: str) -> float:
    return state.value(population_stock_id(region_id, AgeCohort.YOUNG_ADULT)) + state.value(
        population_stock_id(region_id, AgeCohort.MATURE_ADULT)
    )


def global_population(state: ModelState, regions: RegionSet) -> float:
    return sum(region_population(state, region_id) for region_id in regions.ids)
