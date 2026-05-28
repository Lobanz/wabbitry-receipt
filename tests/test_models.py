"""Tests for data models."""

from datetime import date

from wabbitry_receipt.models import LineItemType, Parent, Rabbit


def test_rabbit_creation(sample_rabbit: Rabbit) -> None:
    """Verify rabbit dataclass fields."""
    assert sample_rabbit.gender == "M"
    assert sample_rabbit.breed == "TAMUK NZW"
    assert sample_rabbit.sire.name == "Xander"


def test_rabbit_is_frozen() -> None:
    """Verify rabbit dataclass is immutable."""
    rabbit = Rabbit(
        gender="F",
        breed="M70 NZW",
        dob=date(2026, 3, 25),
        sire=Parent(name="Yaz", breed="M70 NZW"),
        dam=Parent(name="Betty", breed="M70 NZW"),
    )
    try:
        rabbit.gender = "M"  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except AttributeError:
        pass


def test_line_item_type_values() -> None:
    """Verify line item type enum values."""
    assert LineItemType.TRIO == "trio"
    assert LineItemType.PAIR == "pair"
    assert LineItemType.SINGLE == "single"
