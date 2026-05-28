"""Tests for pricing logic."""

from wabbitry_receipt.pricing import (
    BULK_RABBIT_PRICE,
    SINGLE_RABBIT_PRICE,
    line_item_total,
    unit_price,
)


def test_unit_price_single_rabbit() -> None:
    """Verify $50/rabbit when total is 1."""
    assert unit_price(1) == SINGLE_RABBIT_PRICE


def test_unit_price_two_rabbits() -> None:
    """Verify $50/rabbit when total is 2."""
    assert unit_price(2) == SINGLE_RABBIT_PRICE


def test_unit_price_bulk() -> None:
    """Verify $40/rabbit when total is 3."""
    assert unit_price(3) == BULK_RABBIT_PRICE


def test_unit_price_large_bulk() -> None:
    """Verify $40/rabbit when total is 10."""
    assert unit_price(10) == BULK_RABBIT_PRICE


def test_line_item_total_single() -> None:
    """Verify single rabbit total is $50."""
    assert line_item_total(1) == 50.0


def test_line_item_total_trio() -> None:
    """Verify trio total is $120."""
    assert line_item_total(3) == 120.0
