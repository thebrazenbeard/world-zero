from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EnergyReconciliation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gross: float
    accounted_total: float
    difference: float


class EnergyAccount(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gross: float = Field(ge=0)
    conversion_loss: float = Field(ge=0)
    sector_own_use: float = Field(ge=0)
    final_energy: float = Field(ge=0)

    def reconcile(self) -> EnergyReconciliation:
        accounted_total = self.conversion_loss + self.sector_own_use + self.final_energy
        return EnergyReconciliation(
            gross=self.gross,
            accounted_total=accounted_total,
            difference=self.gross - accounted_total,
        )


class TransitionEnergyReconciliation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sector_own_use: float = Field(ge=0)
    embodied_energy_counted_once: float = Field(ge=0)
    industrial_energy_demand_includes_embodied: float = Field(ge=0)
    additional_subtraction: float = Field(ge=0)


def reconcile_transition_energy(
    *,
    sector_own_use: float,
    embodied_energy: float,
    industrial_energy_demand_includes_embodied: float,
    subtract_embodied_again: bool,
) -> TransitionEnergyReconciliation:
    if min(sector_own_use, embodied_energy, industrial_energy_demand_includes_embodied) < 0:
        raise ValueError("energy accounting inputs must be nonnegative")
    if subtract_embodied_again and industrial_energy_demand_includes_embodied > 0 and embodied_energy > 0:
        raise ValueError("double-count: embodied transition energy is already in industrial demand")
    return TransitionEnergyReconciliation(
        sector_own_use=sector_own_use,
        embodied_energy_counted_once=embodied_energy,
        industrial_energy_demand_includes_embodied=industrial_energy_demand_includes_embodied,
        additional_subtraction=embodied_energy if subtract_embodied_again else 0.0,
    )
