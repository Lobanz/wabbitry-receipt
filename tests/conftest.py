"""Shared fixtures for wabbitry-receipt tests."""

from datetime import date

import pytest

from wabbitry_receipt.models import Rabbit, Sale, SaleLineItem


@pytest.fixture
def sample_rabbit() -> Rabbit:
    """Return a sample TAMUK NZW buck for testing."""
    return Rabbit(
        name="Kit 1",
        strain="TAMUK",
        breed="NZW",
        gender="M",
        dob=date(2026, 3, 25),
        sire_name="Xander",
        sire_strain="TAMUK",
        sire_breed="NZW",
        dam_name="Harmony",
        dam_strain="TAMUK",
        dam_breed="NZW",
    )


@pytest.fixture
def sample_sale(sample_rabbit: Rabbit) -> Sale:
    """Return a sample trio sale for testing."""
    doe1 = Rabbit(
        name="Kit 9",
        strain="TAMUK",
        breed="NZW",
        gender="F",
        dob=date(2026, 3, 25),
        sire_name="Willy",
        sire_strain="TAMUK",
        sire_breed="NZW",
        dam_name="Fiona",
        dam_strain="TAMUK",
        dam_breed="NZW",
    )
    doe2 = Rabbit(
        name="Kit 10",
        strain="TAMUK",
        breed="NZW",
        gender="F",
        dob=date(2026, 3, 25),
        sire_name="Willy",
        sire_strain="TAMUK",
        sire_breed="NZW",
        dam_name="Fiona",
        dam_strain="TAMUK",
        dam_breed="NZW",
    )
    return Sale(
        customer_name="Casey Takacs",
        customer_contact="706-669-6616",
        sale_date=date(2026, 5, 28),
        pickup="fri lunch",
        line_items=[
            SaleLineItem(rabbit=sample_rabbit, unit_price=40.0),
            SaleLineItem(rabbit=doe1, unit_price=40.0),
            SaleLineItem(rabbit=doe2, unit_price=40.0),
        ],
    )
