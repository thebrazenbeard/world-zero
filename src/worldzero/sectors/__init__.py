"""Sector-level dynamics for native World Zero models."""

from .climate import ClimateParams, ClimateState, LinearDamage, QuadraticDamage, step_climate
from .demography import AgeCohort, DemographyRates, MigrationLink
from .distribution import DistributionParams, IncomeAllocation, allocate_income
from .energy import (
    EnergyBuildParams,
    EnergyCapacity,
    EnergyDispatch,
    build_energy_sector,
    dispatch_useful_energy,
)
from .food_land import (
    FoodProductionParams,
    FoodProductionResult,
    LandAllocation,
    SoilDynamicsParams,
    allocate_land,
    produce_food,
    update_soil_condition,
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
from .water import WaterAllocation, allocate_water

__all__ = [
    "AgeCohort",
    "ClimateParams",
    "ClimateState",
    "DemographyRates",
    "DistributionParams",
    "EnergyBuildParams",
    "EnergyCapacity",
    "EnergyDispatch",
    "FoodProductionParams",
    "FoodProductionResult",
    "IncomeAllocation",
    "LandAllocation",
    "LearningCurve",
    "LinearDamage",
    "MaterialStepInput",
    "MaterialStepResult",
    "MaterialStockParams",
    "MigrationLink",
    "ProductionParams",
    "QuadraticDamage",
    "SoilDynamicsParams",
    "WaterAllocation",
    "allocate_income",
    "allocate_land",
    "allocate_water",
    "build_energy_sector",
    "build_material_sector",
    "dispatch_useful_energy",
    "produce_food",
    "reconcile_material_step",
    "step_climate",
    "update_soil_condition",
]
