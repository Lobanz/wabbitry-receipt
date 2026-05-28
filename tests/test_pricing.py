"""Tests for pricing logic."""

from wabbitry_receipt.pricing import (
    BULK_RABBIT_PRICE,
    SINGLE_RABBIT_PRICE,
    line_item_total,
    unit_price,
)


def test_unit_price_single_rabbit() -> None:
    assert unit_price(1) == SINGLE_RABBIT_PRICE


def test_unit_price_two_rabbits() -> None:
    assert unit_price(2) == SINGLE_RABBIT_PRICE


def test_unit_price_bulk() -> None:
    assert unit_price(3) == BULK_RABBIT_PRICE


def test_unit_price_large_bulk() -> None:
    assert unit_price(10) == BULK_RABBIT_PRICE


def test_line_item_total_single() -> None:
    assert line_item_total(1) == 50.0


def test_line_item_total_trio() -> None:
    assert line_item_total(3) == 120.0
