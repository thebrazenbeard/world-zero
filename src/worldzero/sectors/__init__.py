"""Sector-level dynamics for native World Zero models."""

from .demography import AgeCohort, DemographyRates, MigrationLink
from .distribution import DistributionParams, IncomeAllocation, allocate_income
from .energy import (
    EnergyBuildParams,
    EnergyCapacity,
    EnergyDispatch,
    build_energy_sector,
    dispatch_useful_energy,
)
from .materials import (
    MaterialStepInput,
    MaterialStepResult,
    MaterialStockParams,
    build_material_sector,
    reconcile_material_step,
)
from .production import ProductionParams
from .technology import LearningCurve

__all__ = [
    "AgeCohort",
    "DemographyRates",
    "DistributionParams",
    "EnergyBuildParams",
    "EnergyCapacity",
    "EnergyDispatch",
    "IncomeAllocation",
    "LearningCurve",
    "MaterialStepInput",
    "MaterialStepResult",
    "MaterialStockParams",
    "MigrationLink",
    "ProductionParams",
    "allocate_income",
    "build_energy_sector",
    "build_material_sector",
    "dispatch_useful_energy",
    "reconcile_material_step",
]
