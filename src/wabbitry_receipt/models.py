"""Data models for wabbitry-receipt."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LineItemType(StrEnum):
    """Type of line item on a sale."""

    TRIO = "trio"
    PAIR = "pair"
    SINGLE = "single"


class Parent(BaseModel):
    """A rabbit's parent (sire or dam)."""

    model_config = ConfigDict(frozen=True)

    name: str
    breed: str


class Rabbit(BaseModel):
    """A rabbit for sale, with lineage info."""

    model_config = ConfigDict(frozen=True)

    gender: str
    breed: str
    dob: date
    sire: Parent
    dam: Parent


class LineItem(BaseModel):
    """A line item on a sale (trio, pair, or single)."""

    model_config = ConfigDict(frozen=True)

    type: LineItemType
    price: float = Field(gt=0)
    rabbits: list[Rabbit]
    desc: str | None = None


class Sale(BaseModel):
    """A complete sale transaction."""

    model_config = ConfigDict(frozen=True)

    customer_name: str
    customer_contact: str
    sale_date: date
    line_items: list[LineItem]
    total: float = Field(ge=0)
    notes: str = ""
