"""Data models for wabbitry-receipt."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class LineItemType(StrEnum):
    """Type of line item on a sale."""

    TRIO = "trio"
    PAIR = "pair"
    SINGLE = "single"


@dataclass(frozen=True)
class Parent:
    """A rabbit's parent (sire or dam)."""

    name: str
    breed: str


@dataclass(frozen=True)
class Rabbit:
    """A rabbit for sale, with lineage info."""

    gender: str
    breed: str
    dob: date
    sire: Parent
    dam: Parent


@dataclass(frozen=True)
class LineItem:
    """A line item on a sale (trio, pair, or single)."""

    type: LineItemType
    price: float
    rabbits: list[Rabbit]
    desc: str | None = None


@dataclass(frozen=True)
class Sale:
    """A complete sale transaction."""

    customer_name: str
    customer_contact: str
    sale_date: date
    pickup: date
    line_items: list[LineItem]
    total: float
    notes: str = ""
