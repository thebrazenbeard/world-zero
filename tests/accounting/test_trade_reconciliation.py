import pytest


def test_trade_routing_conserves_global_physical_stock():
    from worldzero.accounting.trade import TradeFlow, reconcile_trade

    flows = [
        TradeFlow(origin="A", destination="B", amount=10.0, loss=1.0),
        TradeFlow(origin="B", destination="C", amount=4.0, loss=0.5),
    ]
    result = reconcile_trade(flows)
    assert result.total_origin_debits == pytest.approx(
        result.total_destination_credits + result.total_losses
    )
    assert result.difference == pytest.approx(0.0)


def test_trade_flow_rejects_loss_larger_than_shipped_amount():
    from pydantic import ValidationError

    from worldzero.accounting.trade import TradeFlow

    with pytest.raises(ValidationError):
        TradeFlow(origin="A", destination="B", amount=2.0, loss=3.0)


def test_trade_reconciliation_preserves_regional_net_balances():
    from worldzero.accounting.trade import TradeFlow, reconcile_trade

    result = reconcile_trade(
        [
            TradeFlow(origin="A", destination="B", amount=10.0, loss=1.0),
            TradeFlow(origin="B", destination="A", amount=4.0, loss=0.0),
        ]
    )
    assert result.origin_debits["A"] == pytest.approx(10.0)
    assert result.destination_credits["A"] == pytest.approx(4.0)
    assert result.destination_credits["B"] == pytest.approx(9.0)
