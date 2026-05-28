---
id: 0002
title: Sale JSON schema and data model
date: 2026-05-28
status: accepted
---

# 0002: Sale JSON Schema and Data Model

## Context

Wabbitry-receipt generates PDF sales receipts from structured JSON. Two data
sources exist:

1. **breeders.json** — breeding stock inventory (adult sires and dams). Used as
   a lookup reference when constructing sale JSON from natural language prompts.
   Not consumed by the renderer.
2. **sale.json** — one per sale. Self-contained input to the renderer.

## Decision

### sale.json Schema

```json
{
  "customer_name": "Casey Takacs",
  "customer_contact": "706-669-6616",
  "sale_date": "2026-05-28",
  "line_items": [
    {
      "type": "trio",
      "price": 120.00,
      "desc": "red + / black ○ / black ○",
      "rabbits": [
        {
          "gender": "M",
          "breed": "TAMUK NZW",
          "dob": "2026-03-25",
          "sire": {"name": "Xander", "breed": "TAMUK NZW"},
          "dam": {"name": "Harmony", "breed": "TAMUK NZW"}
        },
        {
          "gender": "F",
          "breed": "TAMUK NZW",
          "dob": "2026-03-25",
          "sire": {"name": "Willy", "breed": "TAMUK NZW"},
          "dam": {"name": "Fiona", "breed": "TAMUK NZW"}
        },
        {
          "gender": "F",
          "breed": "TAMUK NZW",
          "dob": "2026-03-25",
          "sire": {"name": "Willy", "breed": "TAMUK NZW"},
          "dam": {"name": "Fiona", "breed": "TAMUK NZW"}
        }
      ]
    }
  ],
  "total": 120.00,
  "notes": ""
}
```

### breeders.json Schema (existing, unchanged)

```json
{
  "name": "Xander",
  "breed": "TAMUK NZW",
  "gender": "M",
  "siblings": []
}
```

breeders.json is a lookup reference. It tracks adult breeding stock (names,
breeds, gender, sibling relationships). The renderer does not consume it —
sale.json is self-contained.

### Field Rules

- **`breed`** is one combined field: "M70 NZW", "TAMUK NZW", "TAMUK Composite".
  Never split into separate strain/breed fields.
- **`gender`** is "M" or "F".
- **`dob`** is an ISO 8601 date (YYYY-MM-DD).
- **`sire`/`dam`** each have `name` and `breed`. These are the rabbit's parents.
- **`type`** is a LineItemType enum: "trio", "pair", "single".
  - trio = 1 buck + 2 does (3 rabbits)
  - pair = 1 buck + 1 doe (2 rabbits)
  - single = 1 rabbit
- **`price`** is the line item total. Default pricing logic computes it, but the
  JSON value is authoritative (allows discount overrides).
- **`total`** is the sale-level total (sum of line item prices).
- **`desc`** is an optional small text field on line items. Defaults to empty.
  Used for notes the operator wants on the receipt (e.g., rabbit identification
  markings like "red + / black ○"). The template also includes a small blank
  area per rabbit for handwriting marks after printing.
  Accepts inline HTML for formatting (`<b>`, `<i>`, `<br>`).
- **`notes`** is an optional sale-level comment field. Defaults to empty.
  Displayed at the bottom of the receipt under the total. Used for general
  sale context (e.g., "trios chosen so each buck can breed any of the does").
  Accepts inline HTML for formatting (`<b>`, `<i>`, `<br>`).

### Pricing Rules

Default pricing is per-rabbit based on total rabbits across the entire sale:
- Total < 3 rabbits: $50/rabbit
- Total >= 3 rabbits: $40/rabbit

Default line item prices:
- Trio (3 rabbits): $120
- Pair (2 rabbits): $100
- Single (1 rabbit): $50

### Why Prices Are in JSON

Prices are included in the sale JSON rather than computed at render time for
flexibility. The default pricing logic handles the happy path, but the operator
may need to handle edge cases:

- **Discounts** — a repeat customer or partial refund
- **Non-standard arrangements** — breeding-age males from prior breedings,
  rescue rabbits, special deals
- **Mixed sales** — a trio plus a single where the single should also get the
  bulk rate

The renderer uses whatever price is in the JSON. The pricing module provides
defaults; the JSON carries the authoritative value.

### Output Structure

```
output/
  <breeding-dob>/
    <customer-name>_<sale-date>.json
    <customer-name>_<sale-date>.pdf
```

Example: `output/2026-03-25/casey-takacs_2026-05-28.pdf`

## Alternatives Considered

- **Normalized schema**: sale.json references rabbit IDs from breeders.json.
  Rejected — requires both files at render time, adds complexity.
- **Per-rabbit pricing**: price on each rabbit instead of line item. Rejected —
  pricing is per sale total, not per rabbit.
- **Split strain/breed fields**: separate `strain` and `breed` fields. Rejected
  by operator — breed is one combined field.

## Consequences

- Sale.json is self-contained — renderer needs no external data.
- The operator uses breeders.json to look up parent names when constructing sale
  JSON from natural language.
- Pricing logic provides defaults; JSON carries the authoritative price.
- The `type` field is informational (for receipt display), not prescriptive.
- The `desc` field and template blank area handle rabbit identification markings.
- The `notes` field provides sale-level commentary at the bottom of the receipt.
