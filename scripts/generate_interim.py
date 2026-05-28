#!/usr/bin/env python3
"""Generate an interim markdown receipt from a sale JSON file."""

import json
import sys
from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "interim_receipt.md"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def load_sale(path: Path) -> dict:
    """Load and return sale JSON."""
    with open(path) as f:
        return json.load(f)


def format_rabbit(rabbit: dict) -> str:
    """Format a single rabbit as a markdown line."""
    gender = "Buck" if rabbit["gender"] == "M" else "Doe"
    sire = rabbit["sire"]
    dam = rabbit["dam"]
    return (
        f"  - {gender} — {rabbit['breed']}  \n"
        f"    DOB: {rabbit['dob']}  \n"
        f"    Sire: {sire['name']} ({sire['breed']})  \n"
        f"    Dam: {dam['name']} ({dam['breed']})"
    )


def format_line_item(item: dict) -> str:
    """Format a line item as markdown."""
    type_label = item["type"].capitalize()
    price = item["price"]
    desc = item.get("desc", "")

    lines = [f"### {type_label} — ${price:.2f}"]
    if desc:
        lines.append(f"*{desc}*")
    lines.append("")
    for rabbit in item["rabbits"]:
        lines.append(format_rabbit(rabbit))
    lines.append("")
    return "\n".join(lines)


def render_receipt(sale: dict) -> str:
    """Render sale data into the markdown template."""
    template = TEMPLATE_PATH.read_text()

    line_items = "\n".join(
        format_line_item(item) for item in sale["line_items"]
    )

    notes = sale.get("notes", "")
    if notes:
        notes = f"*{notes}*"

    result = template.replace("{{customer_name}}", sale["customer_name"])
    result = result.replace("{{customer_contact}}", sale["customer_contact"])
    result = result.replace("{{sale_date}}", sale["sale_date"])
    result = result.replace("{{pickup}}", sale["pickup"])
    result = result.replace("{{line_items}}", line_items)
    result = result.replace("{{total}}", f"${sale['total']:.2f}")
    result = result.replace("{{notes}}", notes)

    return result


def main() -> None:
    """Generate receipt from sale JSON."""
    if len(sys.argv) < 2:
        print("Usage: generate_interim.py <sale.json>")
        sys.exit(1)

    sale_path = Path(sys.argv[1])
    if not sale_path.exists():
        print(f"Error: {sale_path} not found")
        sys.exit(1)

    sale = load_sale(sale_path)
    receipt = render_receipt(sale)

    # Build output path: output/<dob>/<customer>_<sale_date>.md
    # Use first rabbit's DOB as breeding date
    first_dob = sale["line_items"][0]["rabbits"][0]["dob"]
    customer_slug = sale["customer_name"].lower().replace(" ", "-")
    sale_date = sale["sale_date"]

    out_dir = OUTPUT_DIR / first_dob
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{customer_slug}_{sale_date}.md"
    out_path.write_text(receipt)

    print(f"Receipt written to {out_path}")
    print()
    print(receipt)


if __name__ == "__main__":
    main()
