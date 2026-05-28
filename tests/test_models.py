"""Tests for data models."""

from datetime import date

from wabbitry_receipt.models import Rabbit


def test_rabbit_creation(sample_rabbit: Rabbit) -> None:
    assert sample_rabbit.name == "Kit 1"
    assert sample_rabbit.strain == "TAMUK"
    assert sample_rabbit.breed == "NZW"
    assert sample_rabbit.gender == "M"


def test_rabbit_is_frozen() -> None:
    rabbit = Rabbit(
        name="Test",
        strain="M70",
        breed="NZW",
        gender="F",
        dob=date(2026, 3, 25),
        sire_name="Yaz",
        sire_strain="M70",
        sire_breed="NZW",
        dam_name="Betty",
        dam_strain="M70",
        dam_breed="NZW",
    )
    try:
        rabbit.name = "Changed"  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except AttributeError:
        pass
