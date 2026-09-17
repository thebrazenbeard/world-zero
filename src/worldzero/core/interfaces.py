"""Typed identifiers and scalar quantities for the simulation core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Self


class _NonEmptyId(str):
    def __new__(cls, value: str) -> Self:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{cls.__name__} must be a non-empty string")
        return str.__new__(cls, value.strip())


class StockId(_NonEmptyId):
    pass


class FlowId(_NonEmptyId):
    pass


class SectorId(_NonEmptyId):
    pass


class RegionId(_NonEmptyId):
    pass


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.value):
            raise ValueError("quantity value must be finite")
        if not self.unit.strip():
            raise ValueError("quantity unit must be non-empty")
