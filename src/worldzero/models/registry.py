"""Ordered module composition for the integrated World Zero solver."""

from __future__ import annotations

from dataclasses import dataclass

from worldzero.core import FlowSpec, StockSpec


@dataclass(frozen=True, slots=True)
class ModelContribution:
    module_id: str
    stocks: tuple[StockSpec, ...]
    flows: tuple[FlowSpec, ...]

    def __post_init__(self) -> None:
        if not self.module_id.strip():
            raise ValueError("module_id must be non-empty")


class ModuleRegistry:
    def __init__(self) -> None:
        self._contributions: list[ModelContribution] = []
        self._ids: set[str] = set()

    @property
    def module_ids(self) -> tuple[str, ...]:
        return tuple(contribution.module_id for contribution in self._contributions)

    def add(self, contribution: ModelContribution) -> None:
        if contribution.module_id in self._ids:
            raise ValueError(f"duplicate module ownership: {contribution.module_id}")
        self._ids.add(contribution.module_id)
        self._contributions.append(contribution)

    def compose(self) -> tuple[tuple[StockSpec, ...], tuple[FlowSpec, ...]]:
        stocks = tuple(stock for item in self._contributions for stock in item.stocks)
        flows = tuple(flow for item in self._contributions for flow in item.flows)
        stock_ids = tuple(str(stock.stock_id) for stock in stocks)
        flow_ids = tuple(str(flow.flow_id) for flow in flows)
        if len(stock_ids) != len(set(stock_ids)):
            raise ValueError("duplicate stock ownership across registered modules")
        if len(flow_ids) != len(set(flow_ids)):
            raise ValueError("duplicate flow ownership across registered modules")
        return stocks, flows
