"""Data models for wabbitry-receipt."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Rabbit:
    """A rabbit for sale, with lineage and breed info."""

    name: str
    strain: str
    breed: str
    gender: str
    dob: date
    sire_name: str
    sire_strain: str
    sire_breed: str
    dam_name: str
    dam_strain: str
    dam_breed: str


@dataclass(frozen=True)
class SaleLineItem:
    """A single rabbit line item on a sale."""

    rabbit: Rabbit
    unit_price: float


@dataclass(frozen=True)
class Sale:
    """A complete sale transaction."""

    customer_name: str
    customer_contact: str
    sale_date: date
    pickup: str
    line_items: list[SaleLineItem]
