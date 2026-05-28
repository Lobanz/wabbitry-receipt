"""Pricing logic for Wascally Wabbitry sales."""

from typing import Final

SINGLE_RABBIT_PRICE: Final = 50.0
BULK_RABBIT_PRICE: Final = 40.0
BULK_THRESHOLD: Final = 3


def unit_price(quantity: int) -> float:
    """Return per-rabbit price based on total quantity in the sale.

    Args:
        quantity: Total number of rabbits in the sale.

    Returns:
        Price per rabbit: $50 for 1-2, $40 for 3+.

    """
    if quantity >= BULK_THRESHOLD:
        return BULK_RABBIT_PRICE
    return SINGLE_RABBIT_PRICE


def line_item_total(quantity: int) -> float:
    """Return total price for the given quantity of rabbits.

    Args:
        quantity: Number of rabbits.

    Returns:
        Total price (quantity * unit_price).

    """
    return quantity * unit_price(quantity)
