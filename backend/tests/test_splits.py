from decimal import Decimal

import pytest

from app.utils.money import quantize, split_equal, split_exact, split_percentage, split_shares


def test_split_equal_evenly_divisible():
    result = split_equal(Decimal("1000"), [1, 2, 3, 4])
    assert result == {1: Decimal("250.00"), 2: Decimal("250.00"), 3: Decimal("250.00"), 4: Decimal("250.00")}
    assert sum(result.values()) == Decimal("1000.00")


def test_split_equal_distributes_remainder_deterministically():
    # 100 / 3 = 33.33 repeating -- the extra cent must go somewhere, and the
    # total must still sum exactly to 100.00.
    result = split_equal(Decimal("100"), [1, 2, 3])
    assert sum(result.values()) == Decimal("100.00")
    assert result[1] == Decimal("33.34")
    assert result[2] == Decimal("33.33")
    assert result[3] == Decimal("33.33")


def test_split_exact_matching_total():
    result = split_exact(Decimal("1000"), {1: Decimal("400"), 2: Decimal("300"), 3: Decimal("200"), 4: Decimal("100")})
    assert result == {1: Decimal("400.00"), 2: Decimal("300.00"), 3: Decimal("200.00"), 4: Decimal("100.00")}


def test_split_exact_rejects_mismatched_total():
    with pytest.raises(ValueError):
        split_exact(Decimal("1000"), {1: Decimal("400"), 2: Decimal("300")})


def test_split_exact_rejects_negative_amount():
    with pytest.raises(ValueError):
        split_exact(Decimal("100"), {1: Decimal("150"), 2: Decimal("-50")})


def test_split_percentage_matching_100():
    result = split_percentage(
        Decimal("1000"),
        {1: Decimal("40"), 2: Decimal("30"), 3: Decimal("20"), 4: Decimal("10")},
    )
    assert result == {1: Decimal("400.00"), 2: Decimal("300.00"), 3: Decimal("200.00"), 4: Decimal("100.00")}
    assert sum(result.values()) == Decimal("1000.00")


def test_split_percentage_rejects_non_100_total():
    with pytest.raises(ValueError):
        split_percentage(Decimal("1000"), {1: Decimal("50"), 2: Decimal("40")})


def test_split_percentage_handles_thirds_without_drift():
    result = split_percentage(Decimal("100"), {1: Decimal("33.34"), 2: Decimal("33.33"), 3: Decimal("33.33")})
    assert sum(result.values()) == Decimal("100.00")


def test_split_shares_proportional():
    result = split_shares(Decimal("900"), {1: 1, 2: 2, 3: 3})
    assert sum(result.values()) == Decimal("900.00")
    assert result[3] > result[2] > result[1]


def test_split_shares_rejects_zero_total_shares():
    with pytest.raises(ValueError):
        split_shares(Decimal("100"), {1: 0, 2: 0})


def test_quantize_rounds_half_up():
    assert quantize(Decimal("10.005")) == Decimal("10.01")
    assert quantize(Decimal("10.004")) == Decimal("10.00")
