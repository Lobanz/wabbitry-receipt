"""CLI interface for wabbitry-receipt."""

import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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
        "--breeders",
        type=Path,
        default=Path("data/breeders.json"),
        help="Path to breeders.json (default: data/breeders.json).",
    )
    generate_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory for generated receipts (default: output).",
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        # REASON: placeholder — renderer not yet implemented.
        logger.info("generate command invoked", extra={"sale_json": str(args.sale_json)})
        print("Not yet implemented.")
