"""Sector-level dynamics for native World Zero models."""

from .demography import AgeCohort, DemographyRates, MigrationLink
from .distribution import DistributionParams, IncomeAllocation, allocate_income
from .energy import EnergyCapacity, EnergyDispatch, dispatch_useful_energy
from .materials import MaterialStepInput, MaterialStepResult, reconcile_material_step
from .production import ProductionParams
from .technology import LearningCurve

__all__ = [
    "AgeCohort",
    "DemographyRates",
    "DistributionParams",
    "EnergyCapacity",
    "EnergyDispatch",
    "IncomeAllocation",
    "LearningCurve",
    "MaterialStepInput",
    "MaterialStepResult",
    "MigrationLink",
    "ProductionParams",
    "allocate_income",
    "dispatch_useful_energy",
    "reconcile_material_step",
]
