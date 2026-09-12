from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")
PERCENTAGE_TOLERANCE = Decimal("0.01")


def quantize(amount: Decimal) -> Decimal:
    return Decimal(amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _distribute_remainder(amounts: dict[int, Decimal], target_total: Decimal) -> dict[int, Decimal]:
    """Nudge quantized shares by +/-0.01 (round-robin over sorted user ids)
    until they sum exactly to target_total. Needed because dividing a
    quantized total by N or applying percentages independently can leave a
    few cents of rounding drift -- financial splits must sum exactly.
    """
    result = {k: quantize(v) for k, v in amounts.items()}
    current_total = quantize(sum(result.values(), Decimal("0")))
    diff = quantize(target_total - current_total)
    if diff == 0:
        return result

    cents = int((diff * 100).to_integral_value(rounding=ROUND_HALF_UP))
    step = Decimal("0.01") if cents > 0 else Decimal("-0.01")
    ordered_keys = sorted(result.keys())
    for i in range(abs(cents)):
        key = ordered_keys[i % len(ordered_keys)]
        result[key] = quantize(result[key] + step)
    return result


def split_equal(total: Decimal, user_ids: list[int]) -> dict[int, Decimal]:
    if not user_ids:
        raise ValueError("At least one participant is required")
    n = len(user_ids)
    base_share = quantize(Decimal(total) / n)
    amounts = {uid: base_share for uid in user_ids}
    return _distribute_remainder(amounts, quantize(total))


def split_exact(total: Decimal, exact_amounts: dict[int, Decimal]) -> dict[int, Decimal]:
    quantized = {uid: quantize(amount) for uid, amount in exact_amounts.items()}
    for uid, amount in quantized.items():
        if amount < 0:
            raise ValueError(f"Split amount for user {uid} cannot be negative")
    computed_total = quantize(sum(quantized.values(), Decimal("0")))
    if computed_total != quantize(total):
        raise ValueError(
            f"Exact split amounts ({computed_total}) do not sum to the expense total ({quantize(total)})"
        )
    return quantized


def split_percentage(total: Decimal, percentages: dict[int, Decimal]) -> dict[int, Decimal]:
    for uid, pct in percentages.items():
        if pct < 0:
            raise ValueError(f"Percentage for user {uid} cannot be negative")
    pct_total = sum(percentages.values(), Decimal("0"))
    if abs(pct_total - Decimal("100")) > PERCENTAGE_TOLERANCE:
        raise ValueError(f"Percentages must sum to 100 (got {pct_total})")

    raw_amounts = {uid: quantize(Decimal(total) * pct / Decimal("100")) for uid, pct in percentages.items()}
    return _distribute_remainder(raw_amounts, quantize(total))


def split_shares(total: Decimal, shares: dict[int, int]) -> dict[int, Decimal]:
    for uid, share in shares.items():
        if share < 0:
            raise ValueError(f"Shares for user {uid} cannot be negative")
    total_shares = sum(shares.values())
    if total_shares <= 0:
        raise ValueError("Total shares must be greater than zero")

    raw_amounts = {
        uid: quantize(Decimal(total) * Decimal(share) / Decimal(total_shares)) for uid, share in shares.items()
    }
    return _distribute_remainder(raw_amounts, quantize(total))
