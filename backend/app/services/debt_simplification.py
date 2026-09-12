import heapq
from decimal import Decimal

from app.utils.money import quantize


def simplify_debts(net_balances: dict[int, Decimal]) -> list[tuple[int, int, Decimal]]:
    """Given each user's net balance (positive = owed money, negative = owes
    money), returns a minimal-ish list of (from_user_id, to_user_id, amount)
    transactions that settle everyone using a greedy largest-debtor /
    largest-creditor match. Because this operates on *net* balances (not
    pairwise IOUs), A-owes-B-owes-C chains collapse automatically -- e.g. if
    A nets -500 and C nets +500 with B at 0, the output is a single A->C
    transaction even though the underlying expenses never involved A and C
    directly.
    """
    creditors: list[tuple[Decimal, int]] = []
    debtors: list[tuple[Decimal, int]] = []

    for user_id, net in net_balances.items():
        net = quantize(net)
        if net > 0:
            heapq.heappush(creditors, (-net, user_id))
        elif net < 0:
            heapq.heappush(debtors, (net, user_id))

    transactions: list[tuple[int, int, Decimal]] = []

    while creditors and debtors:
        neg_credit, creditor_id = heapq.heappop(creditors)
        credit = -neg_credit
        debit_net, debtor_id = heapq.heappop(debtors)
        debt = -debit_net

        settle_amount = quantize(min(credit, debt))
        if settle_amount > 0:
            transactions.append((debtor_id, creditor_id, settle_amount))

        remaining_credit = quantize(credit - settle_amount)
        remaining_debt = quantize(debt - settle_amount)

        if remaining_credit > 0:
            heapq.heappush(creditors, (-remaining_credit, creditor_id))
        if remaining_debt > 0:
            heapq.heappush(debtors, (-remaining_debt, debtor_id))

    return transactions
