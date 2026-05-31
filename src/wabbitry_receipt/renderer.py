"""Jinja2 + weasyprint receipt renderer."""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from wabbitry_receipt.models import Sale

logger = logging.getLogger(__name__)

TEMPLATE_NAME = "receipt.html.j2"
CSS_NAME = "receipt.css"
LOGO_NAME = "logo.png"


def render_html(sale: Sale, template_dir: Path) -> str:
    """Render sale data to an HTML string using the Jinja2 template.

    Args:
        sale: Validated sale model object.
        template_dir: Directory containing receipt.html.j2 and receipt.css.

    Returns:
        Rendered HTML string.

    """
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
    )
    template = env.get_template(TEMPLATE_NAME)
    html = template.render(sale=sale)
    logger.info("rendered HTML for %s", sale.customer_name)
    return html


def render_pdf(html: str, css_path: Path, logo_path: Path) -> bytes:
    """Convert rendered HTML to PDF bytes via weasyprint.

    Args:
        html: Rendered HTML string from render_html().
        css_path: Path to the receipt CSS file.
        logo_path: Path to the logo image (used as base URL for asset resolution).

    Returns:
        PDF file content as bytes.

    """
    # Delay heavy import so CLI --help stays responsive and test collection
    # doesn't fail if system libraries are missing.
    from weasyprint import CSS, HTML  # type: ignore[import-untyped]  # noqa: PLC0415

    base_url = str(logo_path.parent)
    result = HTML(string=html, base_url=base_url).write_pdf(
        stylesheets=[CSS(filename=str(css_path))],
    )
    if result is None:
        msg = "weasyprint write_pdf returned None"
        raise RuntimeError(msg)
    pdf_bytes = result
    logger.info("rendered PDF (%d bytes)", len(pdf_bytes))
    return pdf_bytes  # type: ignore[no-any-return]
