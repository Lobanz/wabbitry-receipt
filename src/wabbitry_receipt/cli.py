"""CLI interface for wabbitry-receipt.

Provides the ``generate`` subcommand for rendering sale JSON files into
styled PDF receipts with a co-located JSON copy.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from wabbitry_receipt.models import Sale
from wabbitry_receipt.renderer import (
    CSS_NAME,
    LOGO_NAME,
    render_html,
    render_pdf,
)

logger = logging.getLogger(__name__)

# Default output directory when neither --output-dir nor the env var is set.
DEFAULT_OUTPUT_DIR = Path("output")


def _resolve_output_dir(explicit: Path | None) -> Path:
    """Return the base output directory.

    Priority:
    1. Explicit --output-dir value
    2. $WABBITRY_RECEIPT_OUTPUT_DIR env var
    3. DEFAULT_OUTPUT_DIR (``output/``)
    """
    if explicit is not None:
        return explicit
    env_val = os.environ.get("WABBITRY_RECEIPT_OUTPUT_DIR")
    if env_val:
        return Path(env_val)
    return DEFAULT_OUTPUT_DIR


def _output_path_for_sale(sale: Sale, output_dir: Path) -> Path:
    """Compute the PDF output path from sale data.

    Structure: ``<output_dir>/<sale_date>/<customer-name>.pdf``
    """
    date_folder = sale.sale_date.isoformat()
    customer_slug = sale.customer_name.lower().replace(" ", "-")
    return output_dir / date_folder / f"{customer_slug}.pdf"


def _get_template_dir() -> Path:
    """Return the template directory via importlib.resources."""
    import importlib.resources  # noqa: PLC0415

    ref = importlib.resources.files("wabbitry_receipt") / "templates"
    return Path(str(ref))


def main(argv: list[str] | None = None) -> None:
    """Run the receipt generator CLI."""
    parser = argparse.ArgumentParser(
        prog="wabbitry-receipt",
        description="Generate sales receipts for Wascally Wabbitry.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a receipt from a sale JSON file.",
    )
    generate_parser.add_argument(
        "sale_json",
        type=Path,
        help="Path to the sale JSON file.",
    )
    generate_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory for generated receipts. "
            "Default: $WABBITRY_RECEIPT_OUTPUT_DIR env var, or output/"
        ),
    )
    generate_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Full output path (dir + filename). Overrides --output-dir.",
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        _cmd_generate(args.sale_json, args.output, args.output_dir)


def _cmd_generate(
    sale_json: Path,
    output_override: Path | None,
    output_dir_arg: Path | None,
) -> None:
    """Execute the generate subcommand.

    Args:
        sale_json: Path to the sale JSON input file.
        output_override: --output value (full path), or None.
        output_dir_arg: --output-dir value, or None.

    Raises:
        SystemExit: With code 1 on any operational error.

    """
    # 1. Load and validate sale JSON.
    try:
        raw = sale_json.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError, PermissionError) as exc:
        logger.error("cannot read sale JSON: %s — %s", sale_json, exc.__class__.__name__)
        print(f"Error: cannot read file: {sale_json}", file=sys.stderr)
        sys.exit(1)

    try:
        sale = Sale.model_validate_json(raw)
    except Exception:
        logger.error("invalid sale JSON: %s", sale_json, exc_info=True)
        print(f"Error: invalid sale JSON: {sale_json}", file=sys.stderr)
        sys.exit(1)

    # 2. Resolve output path.
    template_dir = _get_template_dir()
    css_path = template_dir / CSS_NAME
    logo_path = template_dir / LOGO_NAME

    if output_override is not None:
        pdf_path = (
            output_override if output_override.is_absolute() else Path.cwd() / output_override
        )
    else:
        output_dir = _resolve_output_dir(output_dir_arg)
        pdf_path = _output_path_for_sale(sale, output_dir)

    # 3. Render.
    try:
        html = render_html(sale, template_dir)
        pdf_bytes = render_pdf(html, css_path, logo_path)
    except Exception:
        logger.error("rendering failed", exc_info=True)
        print("Error: rendering failed — see log for details.", file=sys.stderr)
        sys.exit(1)

    # 4. Write PDF.
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(pdf_bytes)
    logger.info("wrote PDF: %s (%d bytes)", pdf_path, len(pdf_bytes))

    # 5. Copy sale JSON alongside the PDF (skip if already there).
    json_copy = pdf_path.with_suffix(".json")
    if json_copy.resolve() != sale_json.resolve():
        shutil.copy2(sale_json, json_copy)
        logger.info("copied sale JSON: %s", json_copy)
    else:
        logger.info("sale JSON already at destination: %s", json_copy)

    print(f"Receipt written: {pdf_path}")
