from decimal import Decimal

from app.services.debt_simplification import simplify_debts


def test_simplify_collapses_chain_a_owes_b_owes_c():
    # A owes B 500, B owes C 500 nets out to: A -500, B 0, C +500.
    # The simplified result should be a single A -> C transaction, never
    # touching B, even though the underlying expenses ran through B.
    net_balances = {1: Decimal("-500.00"), 2: Decimal("0.00"), 3: Decimal("500.00")}
    transactions = simplify_debts(net_balances)
    assert transactions == [(1, 3, Decimal("500.00"))]


def test_simplify_handles_multiple_creditors_and_debtors():
    net_balances = {
        1: Decimal("6000.00"),
        2: Decimal("-2000.00"),
        3: Decimal("-2000.00"),
        4: Decimal("-2000.00"),
    }
    transactions = simplify_debts(net_balances)
    assert len(transactions) == 3
    total_settled = sum(amount for _, _, amount in transactions)
    assert total_settled == Decimal("6000.00")
    for from_id, to_id, amount in transactions:
        assert to_id == 1
        assert amount == Decimal("2000.00")


def test_simplify_ignores_zero_balances():
    net_balances = {1: Decimal("0.00"), 2: Decimal("100.00"), 3: Decimal("-100.00")}
    transactions = simplify_debts(net_balances)
    assert transactions == [(3, 2, Decimal("100.00"))]


def test_simplify_empty_when_all_settled():
    net_balances = {1: Decimal("0.00"), 2: Decimal("0.00")}
    assert simplify_debts(net_balances) == []


def test_simplify_preserves_total_conservation():
    net_balances = {1: Decimal("300.00"), 2: Decimal("-100.00"), 3: Decimal("-50.00"), 4: Decimal("-150.00")}
    transactions = simplify_debts(net_balances)

    net_after = dict(net_balances)
    for from_id, to_id, amount in transactions:
        net_after[from_id] += amount
        net_after[to_id] -= amount

    assert all(v == Decimal("0.00") for v in net_after.values())
