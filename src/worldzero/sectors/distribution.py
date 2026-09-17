"""Compact income-distribution accounting for the native backbone."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DistributionParams:
    labor_share: float

    def __post_init__(self) -> None:
        if not 0 <= self.labor_share <= 1:
            raise ValueError("labor_share must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class IncomeAllocation:
    real_output: float
    labor_income: float
    owner_income: float


def allocate_income(real_output: float, params: DistributionParams) -> IncomeAllocation:
    if real_output < 0:
        raise ValueError("real_output must be nonnegative")
    labor = real_output * params.labor_share
    owner = real_output - labor
    return IncomeAllocation(real_output=real_output, labor_income=labor, owner_income=owner)
