"""Sector-level dynamics for native World Zero models."""

from .demography import AgeCohort, DemographyRates, MigrationLink
from .distribution import DistributionParams, IncomeAllocation, allocate_income
from .production import ProductionParams

__all__ = [
    "AgeCohort",
    "DemographyRates",
    "DistributionParams",
    "IncomeAllocation",
    "MigrationLink",
    "ProductionParams",
    "allocate_income",
]
