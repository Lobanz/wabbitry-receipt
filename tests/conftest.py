"""Shared fixtures for wabbitry-receipt tests."""

from datetime import date

import pytest

from wabbitry_receipt.models import (
    LineItem,
    LineItemType,
    Parent,
    Rabbit,
    Sale,
)


@pytest.fixture
def sample_rabbit() -> Rabbit:
    """Return a sample TAMUK NZW buck for testing."""
    return Rabbit(
        gender="M",
        breed="TAMUK NZW",
        dob=date(2026, 3, 25),
        sire=Parent(name="Xander", breed="TAMUK NZW"),
        dam=Parent(name="Harmony", breed="TAMUK NZW"),
    )


@pytest.fixture
def sample_sale(sample_rabbit: Rabbit) -> Sale:
    """Return a sample trio sale for testing."""
    doe1 = Rabbit(
        gender="F",
        breed="TAMUK NZW",
        dob=date(2026, 3, 25),
        sire=Parent(name="Willy", breed="TAMUK NZW"),
        dam=Parent(name="Fiona", breed="TAMUK NZW"),
    )
    doe2 = Rabbit(
        gender="F",
        breed="TAMUK NZW",
        dob=date(2026, 3, 25),
        sire=Parent(name="Willy", breed="TAMUK NZW"),
        dam=Parent(name="Fiona", breed="TAMUK NZW"),
    )
    return Sale(
        customer_name="Casey Takacs",
        customer_contact="706-669-6616",
        sale_date=date(2026, 5, 28),
        line_items=[
            LineItem(
                type=LineItemType.TRIO,
                price=120.0,
                rabbits=[sample_rabbit, doe1, doe2],
                desc="red + / black ○ / black ○",
            ),
        ],
        total=120.0,
    )
