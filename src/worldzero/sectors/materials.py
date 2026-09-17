"""Compact material circularity accounting with explicit losses and bottlenecks."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MaterialStepInput:
    beginning_in_use: float
    retirement: float
    virgin_extraction: float
    desired_new_in_use: float
    recycling_rate: float
    recycling_yield: float
    processing_loss_fraction: float

    def __post_init__(self) -> None:
        amounts = (
            self.beginning_in_use,
            self.retirement,
            self.virgin_extraction,
            self.desired_new_in_use,
        )
        if any(not math.isfinite(value) or value < 0 for value in amounts):
            raise ValueError("material amounts must be finite and nonnegative")
        if self.retirement > self.beginning_in_use:
            raise ValueError("retirement cannot exceed material in use")
        for name, value in (
            ("recycling_rate", self.recycling_rate),
            ("recycling_yield", self.recycling_yield),
            ("processing_loss_fraction", self.processing_loss_fraction),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class MaterialStepResult:
    recovered_secondary: float
    recycling_loss: float
    unrecovered_retirement_loss: float
    processing_loss: float
    actual_new_in_use: float
    unused_processed_inventory: float
    unmet_new_in_use: float
    ending_in_use: float
    input_balance_difference: float
    retirement_balance_difference: float


def reconcile_material_step(inputs: MaterialStepInput) -> MaterialStepResult:
    routed_to_recycling = inputs.retirement * inputs.recycling_rate
    recovered = routed_to_recycling * inputs.recycling_yield
    recycling_loss = routed_to_recycling - recovered
    unrecovered_loss = inputs.retirement - routed_to_recycling

    total_input = inputs.virgin_extraction + recovered
    processing_loss = total_input * inputs.processing_loss_fraction
    processed_available = total_input - processing_loss
    actual_new = min(inputs.desired_new_in_use, processed_available)
    unused_inventory = processed_available - actual_new
    unmet = inputs.desired_new_in_use - actual_new
    ending = inputs.beginning_in_use - inputs.retirement + actual_new
    input_difference = total_input - actual_new - processing_loss - unused_inventory
    retirement_difference = (
        inputs.retirement - recovered - recycling_loss - unrecovered_loss
    )
    return MaterialStepResult(
        recovered_secondary=recovered,
        recycling_loss=recycling_loss,
        unrecovered_retirement_loss=unrecovered_loss,
        processing_loss=processing_loss,
        actual_new_in_use=actual_new,
        unused_processed_inventory=unused_inventory,
        unmet_new_in_use=unmet,
        ending_in_use=ending,
        input_balance_difference=input_difference,
        retirement_balance_difference=retirement_difference,
    )
