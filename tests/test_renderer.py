"""Tests for receipt renderer."""

from __future__ import annotations

from datetime import date
from importlib import resources
from pathlib import Path

import pytest

from wabbitry_receipt.models import LineItem, LineItemType, Parent, Rabbit, Sale
from wabbitry_receipt.renderer import render_html, render_pdf


@pytest.fixture
def template_dir() -> Path:
    """Return path to the templates directory."""
    return Path(str(resources.files("wabbitry_receipt") / "templates"))


@pytest.fixture
def css_path(template_dir: Path) -> Path:
    """Return path to receipt.css."""
    return template_dir / "receipt.css"


@pytest.fixture
def logo_path(template_dir: Path) -> Path:
    """Return path to logo.png."""
    return template_dir / "logo.png"


@pytest.fixture
def sample_sale_with_notes() -> Sale:
    """Return a sample sale with notes field populated."""
    return Sale(
        customer_name="Jamie Wilson",
        customer_contact="256-555-1234",
        sale_date=date(2026, 5, 28),
        line_items=[
            LineItem(
                type=LineItemType.TRIO,
                price=120.0,
                rabbits=[
                    Rabbit(
                        gender="M",
                        breed="M70 NZW",
                        dob=date(2026, 3, 25),
                        sire=Parent(name="Yaz", breed="M70 NZW"),
                        dam=Parent(name="Betty", breed="M70 NZW"),
                    ),
                    Rabbit(
                        gender="F",
                        breed="TAMUK NZW",
                        dob=date(2026, 3, 25),
                        sire=Parent(name="Vader", breed="TAMUK NZW"),
                        dam=Parent(name="Iris", breed="TAMUK NZW"),
                    ),
                    Rabbit(
                        gender="F",
                        breed="TAMUK NZW",
                        dob=date(2026, 3, 25),
                        sire=Parent(name="Vader", breed="TAMUK NZW"),
                        dam=Parent(name="Ester", breed="TAMUK NZW"),
                    ),
                ],
            ),
        ],
        total=120.0,
        notes="Trio chosen so buck can breed both does.",
    )


def test_rendered_html_contains_business_header(sample_sale: Sale, template_dir: Path) -> None:
    """Business header with Wascally Wabbitry name is present."""
    html = render_html(sample_sale, template_dir)
    assert "Wascally Wabbitry" in html
    assert "Hazel Green, AL" in html


def test_rendered_html_contains_customer_info(sample_sale: Sale, template_dir: Path) -> None:
    """Customer name and contact are rendered."""
    html = render_html(sample_sale, template_dir)
    assert "Casey Takacs" in html
    assert "706-669-6616" in html


def test_rendered_html_contains_line_items(sample_sale: Sale, template_dir: Path) -> None:
    """Each line item's rabbits appear in the HTML."""
    html = render_html(sample_sale, template_dir)
    assert "TAMUK NZW" in html
    assert "Buck" in html
    assert "Doe" in html


def test_rendered_html_contains_total(sample_sale: Sale, template_dir: Path) -> None:
    """Dollar total is rendered."""
    html = render_html(sample_sale, template_dir)
    assert "$120.00" in html


def test_rendered_html_contains_parentage(sample_sale: Sale, template_dir: Path) -> None:
    """Sire and dam names appear in the rendered HTML."""
    html = render_html(sample_sale, template_dir)
    assert "Xander" in html  # sire
    assert "Harmony" in html  # dam
    assert "Willy" in html  # sire of does
    assert "Fiona" in html  # dam of does


def test_rendered_html_contains_notes_when_present(
    sample_sale_with_notes: Sale, template_dir: Path
) -> None:
    """Notes section renders when notes field is populated."""
    html = render_html(sample_sale_with_notes, template_dir)
    assert "Notes" in html
    assert "Trio chosen so buck can breed both does." in html


def test_rendered_html_omits_notes_when_empty(sample_sale: Sale, template_dir: Path) -> None:
    """No prepopulated notes text when notes field is empty (default)."""
    html = render_html(sample_sale, template_dir)
    assert 'class="hand-notes-pre"' not in html


def test_render_pdf_produces_nonempty_bytes(
    sample_sale: Sale,
    template_dir: Path,
    css_path: Path,
    logo_path: Path,
) -> None:
    """PDF generation produces non-empty bytes."""
    html = render_html(sample_sale, template_dir)
    pdf = render_pdf(html, css_path, logo_path)
    assert len(pdf) > 0
    assert pdf[:4] == b"%PDF"


def test_render_pdf_contains_expected_content(
    sample_sale: Sale,
    template_dir: Path,
    css_path: Path,
    logo_path: Path,
) -> None:
    """PDF has substantial content (not a stub or empty page)."""
    html = render_html(sample_sale, template_dir)
    pdf = render_pdf(html, css_path, logo_path)
    # A real receipt with logo, text, and tables should be well over 10KB.
    # A stub/empty PDF would be under 2KB.
    assert len(pdf) > 10_000, f"PDF suspiciously small ({len(pdf)} bytes)"
