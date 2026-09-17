from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TradeFlow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    amount: float = Field(ge=0)
    loss: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_loss(self) -> TradeFlow:
        if self.loss > self.amount:
            raise ValueError("trade loss cannot exceed shipped amount")
        return self

    @property
    def delivered(self) -> float:
        return self.amount - self.loss


class TradeReconciliation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_origin_debits: float
    total_destination_credits: float
    total_losses: float
    difference: float
    origin_debits: dict[str, float]
    destination_credits: dict[str, float]


def reconcile_trade(flows: Iterable[TradeFlow]) -> TradeReconciliation:
    origin_debits: defaultdict[str, float] = defaultdict(float)
    destination_credits: defaultdict[str, float] = defaultdict(float)
    total_losses = 0.0

    for flow in flows:
        origin_debits[flow.origin] += flow.amount
        destination_credits[flow.destination] += flow.delivered
        total_losses += flow.loss

    total_origin_debits = sum(origin_debits.values())
    total_destination_credits = sum(destination_credits.values())
    return TradeReconciliation(
        total_origin_debits=total_origin_debits,
        total_destination_credits=total_destination_credits,
        total_losses=total_losses,
        difference=total_origin_debits - total_destination_credits - total_losses,
        origin_debits=dict(origin_debits),
        destination_credits=dict(destination_credits),
    )
