"""Stock, flow and model-state primitives."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .interfaces import FlowId, RegionId, SectorId, StockId
from .invariants import InvariantResult


class ModelState:
    def __init__(self, values: Mapping[str, float]) -> None:
        normalized: dict[StockId, float] = {}
        for raw_id, raw_value in values.items():
            stock_id = StockId(str(raw_id))
            value = float(raw_value)
            if not math.isfinite(value):
                raise ValueError(f"state value for {stock_id} must be finite")
            normalized[stock_id] = value
        self._values = normalized

    @property
    def values(self) -> Mapping[StockId, float]:
        return MappingProxyType(self._values)

    def value(self, stock_id: StockId | str) -> float:
        return self._values[StockId(str(stock_id))]


RateFunction = Callable[[ModelState, float], float]
InvariantFunction = Callable[[ModelState, float], InvariantResult]


@dataclass(frozen=True, slots=True)
class StockSpec:
    stock_id: StockId | str
    owner: SectorId | str
    unit: str
    initial: float
    nonnegative: bool = True
    region: RegionId | str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "stock_id", StockId(str(self.stock_id)))
        object.__setattr__(self, "owner", SectorId(str(self.owner)))
        if self.region is not None:
            object.__setattr__(self, "region", RegionId(str(self.region)))
        if not self.unit.strip():
            raise ValueError("stock unit must be non-empty")
        if not math.isfinite(self.initial):
            raise ValueError("stock initial value must be finite")
        if self.nonnegative and self.initial < 0:
            raise ValueError("nonnegative stock cannot start below zero")


@dataclass(frozen=True, slots=True)
class FlowSpec:
    flow_id: FlowId | str
    source: StockId | str | None
    target: StockId | str | None
    unit_per_time: str
    rate: RateFunction

    def __post_init__(self) -> None:
        object.__setattr__(self, "flow_id", FlowId(str(self.flow_id)))
        if self.source is not None:
            object.__setattr__(self, "source", StockId(str(self.source)))
        if self.target is not None:
            object.__setattr__(self, "target", StockId(str(self.target)))
        if self.source is None and self.target is None:
            raise ValueError("flow must have a source or target")
        if self.source == self.target:
            raise ValueError("flow source and target must differ")
        if not self.unit_per_time.strip():
            raise ValueError("flow unit_per_time must be non-empty")


class StockFlowModel:
    def __init__(
        self,
        stocks: Iterable[StockSpec],
        flows: Iterable[FlowSpec],
        invariants: Iterable[InvariantFunction] = (),
    ) -> None:
        self.stocks = tuple(stocks)
        self.flows = tuple(flows)
        self.invariants = tuple(invariants)
        self._stock_by_id = {StockId(str(spec.stock_id)): spec for spec in self.stocks}
        if len(self._stock_by_id) != len(self.stocks):
            raise ValueError("duplicate stock_id")
        flow_ids = {FlowId(str(flow.flow_id)) for flow in self.flows}
        if len(flow_ids) != len(self.flows):
            raise ValueError("duplicate flow_id")
        for flow in self.flows:
            self._validate_flow(flow)

    @property
    def stock_by_id(self) -> Mapping[StockId, StockSpec]:
        return MappingProxyType(self._stock_by_id)

    def _validate_flow(self, flow: FlowSpec) -> None:
        for endpoint in (flow.source, flow.target):
            if endpoint is not None and StockId(str(endpoint)) not in self._stock_by_id:
                raise ValueError(f"flow {flow.flow_id} references unknown stock {endpoint}")
        if flow.source is not None and flow.target is not None:
            source_unit = self._stock_by_id[StockId(str(flow.source))].unit
            target_unit = self._stock_by_id[StockId(str(flow.target))].unit
            if source_unit != target_unit:
                raise ValueError(f"flow {flow.flow_id} connects incompatible stock units")

    def initial_state(self) -> ModelState:
        return ModelState({str(spec.stock_id): spec.initial for spec in self.stocks})

    def derivatives(self, state: ModelState, t: float) -> dict[StockId, float]:
        if set(state.values) != set(self._stock_by_id):
            raise ValueError("model state stock set does not match model definition")
        derivatives = {stock_id: 0.0 for stock_id in self._stock_by_id}
        for flow in self.flows:
            rate = float(flow.rate(state, t))
            if rate < 0:
                raise ValueError(f"flow {flow.flow_id} produced a negative rate")
            if flow.source is not None:
                derivatives[StockId(str(flow.source))] -= rate
            if flow.target is not None:
                derivatives[StockId(str(flow.target))] += rate
        return derivatives
