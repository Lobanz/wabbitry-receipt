"""Tests for data models."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from wabbitry_receipt.models import LineItem, LineItemType, Parent, Rabbit, Sale

FIXTURES = Path(__file__).parent / "fixtures"


def _minimal_sale_json(**overrides: Any) -> str:
    """Return a minimal valid sale JSON string, with optional field overrides."""
    data: dict[str, Any] = {
        "customer_name": "Test",
        "customer_contact": "555-0100",
        "sale_date": "2026-05-28",
        "line_items": [],
        "total": 0,
    }
    data.update(overrides)
    return json.dumps(data)


def _minimal_rabbit_json(**overrides: Any) -> str:
    """Return a minimal valid rabbit JSON string, with optional field overrides."""
    data: dict[str, Any] = {
        "gender": "M",
        "breed": "TAMUK NZW",
        "dob": "2026-03-25",
        "sire": {"name": "Xander", "breed": "TAMUK NZW"},
        "dam": {"name": "Harmony", "breed": "TAMUK NZW"},
    }
    data.update(overrides)
    return json.dumps(data)


def make_sample_rabbit() -> Rabbit:
    """Return a sample TAMUK NZW buck."""
    return Rabbit(
        gender="M",
        breed="TAMUK NZW",
        dob=date(2026, 3, 25),
        sire=Parent(name="Xander", breed="TAMUK NZW"),
        dam=Parent(name="Harmony", breed="TAMUK NZW"),
    )


def test_rabbit_creation(sample_rabbit: Rabbit) -> None:
    """Verify rabbit fields are populated correctly."""
    assert sample_rabbit.gender == "M"
    assert sample_rabbit.breed == "TAMUK NZW"
    assert sample_rabbit.sire.name == "Xander"


def test_rabbit_is_frozen() -> None:
    """Verify rabbit model is immutable (pydantic frozen config)."""
    rabbit = make_sample_rabbit()
    with pytest.raises(ValidationError, match="frozen_instance"):
        rabbit.gender = "M"  # type: ignore[misc]


def test_line_item_type_values() -> None:
    """Verify line item type enum values."""
    assert LineItemType.TRIO == LineItemType("trio")
    assert LineItemType.PAIR == LineItemType("pair")
    assert LineItemType.SINGLE == LineItemType("single")


def test_sale_from_valid_json() -> None:
    """Verify JSON round-trip: load -> model -> dump matches."""
    json_str = (FIXTURES / "sample_sale.json").read_text()
    sale = Sale.model_validate_json(json_str)
    assert sale.customer_name == "Casey Takacs"
    assert sale.sale_date == date(2026, 5, 28)
    assert len(sale.line_items) == 1
    assert sale.line_items[0].type == LineItemType.TRIO
    assert sale.total == 120.0

    # Round-trip: dump and re-parse
    dumped = sale.model_dump_json()
    sale2 = Sale.model_validate_json(dumped)
    assert sale2 == sale


def test_sale_rejects_missing_customer_name() -> None:
    """Verify ValidationError on missing required field."""
    data = json.loads(_minimal_sale_json())
    del data["customer_name"]
    with pytest.raises(ValidationError) as exc_info:
        Sale.model_validate_json(json.dumps(data))
    assert "customer_name" in str(exc_info.value)


def test_sale_rejects_wrong_type_customer_name() -> None:
    """Verify ValidationError when customer_name is not a string."""
    bad_json = _minimal_sale_json(customer_name=123)
    with pytest.raises(ValidationError) as exc_info:
        Sale.model_validate_json(bad_json)
    assert "customer_name" in str(exc_info.value)


def test_line_item_rejects_zero_price() -> None:
    """Verify Field(gt=0) catches price: 0."""
    rabbit = make_sample_rabbit()
    with pytest.raises(ValidationError, match="greater_than"):
        LineItem(type=LineItemType.TRIO, price=0, rabbits=[rabbit])


def test_line_item_rejects_negative_price() -> None:
    """Verify Field(gt=0) catches price: -5."""
    rabbit = make_sample_rabbit()
    with pytest.raises(ValidationError, match="greater_than"):
        LineItem(type=LineItemType.TRIO, price=-5, rabbits=[rabbit])


def test_sale_rejects_invalid_date_format() -> None:
    """Verify ValidationError on malformed date string."""
    bad_json = _minimal_sale_json(sale_date="not-a-date")
    with pytest.raises(ValidationError) as exc_info:
        Sale.model_validate_json(bad_json)
    assert "sale_date" in str(exc_info.value)


def test_rabbit_rejects_missing_sire() -> None:
    """Verify ValidationError on missing nested object."""
    data = json.loads(_minimal_rabbit_json())
    del data["sire"]
    with pytest.raises(ValidationError) as exc_info:
        Rabbit.model_validate_json(json.dumps(data))
    assert "sire" in str(exc_info.value)


def test_sale_from_sample_fixture(sample_sale: Sale) -> None:
    """Verify conftest fixture loads cleanly through pydantic."""
    assert sample_sale.customer_name == "Casey Takacs"
    assert sample_sale.total == 120.0
    assert len(sample_sale.line_items) == 1
    assert sample_sale.line_items[0].rabbits[0].sire.name == "Xander"


def test_sale_date_coercion() -> None:
    """Verify string dates coerce to date objects automatically."""
    json_str = _minimal_sale_json()
    sale = Sale.model_validate_json(json_str)
    assert isinstance(sale.sale_date, date)
    assert sale.sale_date == date(2026, 5, 28)


def test_sale_model_dump_roundtrip() -> None:
    """Verify model_dump produces dict that round-trips through model_validate."""
    sale = Sale(
        customer_name="Test User",
        customer_contact="555-0100",
        sale_date=date(2026, 5, 28),
        line_items=[],
        total=0,
    )
    dumped = sale.model_dump()
    restored = Sale.model_validate(dumped)
    assert restored == sale


# ---------------------------------------------------------------------------
# strain_label property
# ---------------------------------------------------------------------------


def test_strain_label_uses_desc_override() -> None:
    """If desc is set and not a sentinel, strain_label returns it."""
    rabbit = make_sample_rabbit()
    item = LineItem(type=LineItemType.TRIO, price=120.0, rabbits=[rabbit], desc="red + / black ○")
    assert item.strain_label == "red + / black ○"


def test_strain_label_ignores_mixed_sentinel() -> None:
    """MIXED sentinel triggers auto-computation."""
    rabbit = make_sample_rabbit()
    item = LineItem(type=LineItemType.TRIO, price=120.0, rabbits=[rabbit], desc="MIXED")
    assert item.strain_label == "TAMUK NZW"


def test_strain_label_ignores_pure_sentinel() -> None:
    """PURE sentinel triggers auto-computation."""
    rabbit = make_sample_rabbit()
    item = LineItem(type=LineItemType.TRIO, price=120.0, rabbits=[rabbit], desc="PURE")
    assert item.strain_label == "TAMUK NZW"


def test_strain_label_auto_computes_single_breed() -> None:
    """Auto-computation for a single breed."""
    rabbit = make_sample_rabbit()
    item = LineItem(type=LineItemType.TRIO, price=120.0, rabbits=[rabbit], desc="")
    assert item.strain_label == "TAMUK NZW"


def test_strain_label_auto_computes_mixed_breed() -> None:
    """Auto-computation for mixed breeds preserves order of first appearance."""
    buck = make_sample_rabbit()
    doe = Rabbit(
        gender="F",
        breed="M70 NZW",
        dob=date(2026, 3, 25),
        sire=Parent(name="Yaz", breed="M70 NZW"),
        dam=Parent(name="Betty", breed="M70 NZW"),
    )
    item = LineItem(type=LineItemType.PAIR, price=80.0, rabbits=[buck, doe])
    assert item.strain_label == "TAMUK NZW x M70 NZW"


def test_strain_label_auto_computes_no_rabbits() -> None:
    """Edge case: empty rabbit list returns Unknown."""
    item = LineItem(type=LineItemType.SINGLE, price=50.0, rabbits=[])
    assert item.strain_label == "Unknown"
