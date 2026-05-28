# Wabbitry Receipt — Design

## Table of Contents

- [1. Overview](#1-overview)
- [2. Use Cases](#2-use-cases)
  - [Standard sales](#standard-sales)
  - [Multi-line-item sales](#multi-line-item-sales)
  - [Mixed-strain trio](#mixed-strain-trio)
  - [Custom pricing](#custom-pricing)
  - [Spreadsheet notation](#spreadsheet-notation-primary-operator-input)
- [3. Edge Cases](#3-edge-cases)
- [4. CLI Design](#4-cli-design)
  - [Entry point](#entry-point)
  - [Arguments](#arguments)
  - [Output path resolution](#output-path-resolution)
  - [Output structure](#output-structure)
- [5. Data Model](#5-data-model)
- [6. Workflow Pipeline](#6-workflow-pipeline)
  - [6.1 Input](#61-input)
  - [6.2 Rendering](#62-rendering)
  - [6.3 PDF Generation](#63-pdf-generation)
- [7. Receipt Layout](#7-receipt-layout)
  - [Section ordering](#section-ordering-top-to-bottom)
  - [Per-rabbit layout](#per-rabbit-layout-within-line-items)
  - [CSS principles](#css-principles)
- [8. Security Considerations](#8-security-considerations)
  - [Customer PII](#customer-pii)
  - [Secret scanning](#secret-scanning)
  - [Threat model](#threat-model)
- [9. Testing Strategy](#9-testing-strategy)
  - [Unit tests](#unit-tests)
  - [Fixture data](#fixture-data)
  - [Integration testing](#integration-testing)
  - [Test naming](#test-naming)
  - [Test independence](#test-independence)
- [10. ESL Compliance](#10-esl-compliance)
- [Terms](#terms)

## 1. Overview

Wabbitry-receipt generates styled PDF sales receipts for Wascally Wabbitry
(Hazel Green, AL) from structured JSON data. It serves two interfaces:

- **Hermes path** — the operator describes a sale in natural language; Hermes
  constructs the sale JSON, calls the receipt tool, and delivers the PDF.
- **CLI path** — the operator (or a script) provides sale JSON directly;
  `python -m wabbitry_receipt generate sale.json` produces the same PDF.

Sale JSON is the contract between both paths. The renderer doesn't care how
the JSON was produced — it takes JSON in, produces HTML and PDF out.

The system is designed for edge cases that inevitably come up in a small
breeding operation: discounts for repeat customers, non-standard arrangements
(breeding-age males from prior litters), mixed-strain trios, and the frequent
case where a customer arrives before records are fully digitized.

## 2. Use Cases

### Standard sales

- **Trio** — 1 buck + 2 does ($120). The most common sale.
- **Pair** — 1 buck + 1 doe ($100).
- **Single** — 1 rabbit ($50).

### Multi-line-item sales

A customer buying two trios (6 rabbits across 2 line items on one receipt).
Each line item has its own type, price, and rabbit group.

### Mixed-strain trio

A TAMUK NZW buck with M70 NZW does (or vice versa). The breed field on each
rabbit carries its own strain — the line item type doesn't encode strain purity.

### Custom pricing

- Repeat customer discount (override price in JSON).
- Breeding-age male from a prior litter (not standard pricing).
- Mixed bulk sale where a trio plus a single should all get the bulk rate.

### Spreadsheet notation (primary operator input)

The operator's working format is tab/space-delimited paste from the trio
optimizer spreadsheet. Rows like:

```
Casey Takacs  706-669-6616  fri lunch  9.   PURE Xander-Harmony-TAM-M-1 => 2 [ Willy-Fiona-TAM-F-9, Willy-Fiona-TAM-F-10 ]
```

Hermes parses these into sale JSON. The spreadsheet notation is documented
in `references/spreadsheet-notation.md`.

## 3. Edge Cases

- **Repeat customer with discount** — operator sets a lower price in the JSON;
  the renderer uses whatever price is in the JSON.
- **Breeding-age male from prior litter** — not a standard kit; pricing may
  differ. JSON carries the authoritative price.
- **Mixed bulk sale** — trio + single where the single should also get the
  bulk rate ($40/rabbit). Pricing module computes defaults; JSON overrides.
- **Operator handwrites markings after printing** — the receipt template
  includes blank marking areas per rabbit for handwriting ear-mark codes
  (red + = buck, black ○ = doe).

## 4. CLI Design

### Entry point

```bash
python -m wabbitry_receipt generate <sale.json>
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `sale_json` | positional | yes | — | Path to the sale JSON file |
| `--output-dir` | optional | no | `output/` | Output directory for receipts |
| `--output` | optional | no | — | Full output path (dir + filename). Overrides `--output-dir`. Relative paths resolve against PWD. |

### Output path resolution

**`--output`** (highest priority) — specifies the complete output path including
filename. When set, `--output-dir` is ignored. Relative paths resolve against
the current working directory.

**`--output-dir`** — specifies the base output directory. Subfolder
(`<breeding-dob>/`) and filename (`<customer>_<sale-date>.pdf`) are still
computed from the sale JSON. Default chain:

1. `$WABBITRY_RECEIPT_OUTPUT_DIR` environment variable, if set.
2. `output/` (relative to current working directory).

### Output structure

With the default `--output-dir`:

```
output/
  <breeding-dob>/
    <customer-name>_<sale-date>.json   # source data (copy)
    <customer-name>_<sale-date>.pdf    # rendered receipt
```

Example: `output/2026-03-25/casey-takacs_2026-05-28.pdf`

The JSON is copied into the output directory alongside the PDF so the source
data is always co-located with the rendered receipt.

## 5. Data Model

The sale JSON schema, field rules, pricing rules, breeders.json role, and
output structure are all defined in ADR 0002 (`decisions/0002-data-model.md`).
That is the single source of truth. If ADR 0002 is superseded, update the
reference there — not here.

## 6. Workflow Pipeline

### 6.1 Input

The sale JSON is the single authoritative input. Two paths produce it:

**Hermes path (natural language):**
1. Operator describes the sale (or pastes spreadsheet rows).
2. Agent parses the description, looks up parent names in breeders.json,
   constructs the sale JSON. Instructions for this path are in
   `AGENT-NL.md` in the repo root.
3. Agent shows constructed JSON to operator for confirmation.
4. Agent calls `python -m wabbitry_receipt generate sale.json`.
5. PDF is delivered to the operator.

**CLI path (direct):**
1. Operator provides a sale JSON file (handwritten or from a script).
2. `python -m wabbitry_receipt generate sale.json` produces the PDF.

### 6.2 Rendering

The rendering pipeline:

```
Sale JSON → Python (load + validate) → Jinja2 (fill HTML template) → HTML
```

**Jinja2 template engine** — fills an HTML template with sale data. The
template uses semantic CSS class names; all styling lives in the CSS file,
not inline in the HTML. Template at `src/wabbitry_receipt/templates/receipt.html.j2`.

**CSS stylesheet** — plain CSS with semantic classes (~100-150 lines). No
Tailwind, no Bootstrap, no utility chains in HTML. Stylesheet at
`src/wabbitry_receipt/templates/receipt.css`.

**Logo** — Wascally Wabbitry logo image. Handled as a file path referenced
by the template; weasyprint resolves it during PDF rendering.

**desc/notes fields** — accept inline HTML. The template renders them with
Jinja2's `|safe` filter. Allowed tags: `<b>`, `<i>`, `<br>`.

### 6.3 PDF Generation

```
HTML → weasyprint → PDF
```

**weasyprint** — Python library that renders HTML/CSS to PDF using system
graphics libraries. No headless browser, no LaTeX, no external services.

**Print layout** — controlled via CSS `@page` rules (margins, page size).
The receipt is a single fixed-width page; responsive layouts are unnecessary.

**System dependencies** — weasyprint requires `libpango`, `libcairo`,
`libgdk-pixbuf`. Documented in README and `docs/tooling.md`.

## 7. Receipt Layout

### Section ordering (top to bottom)

1. **Business header** — logo, business name, contact info, address
   (Hazel Green, AL).
2. **Sale info** — customer name, contact info, sale date.
3. **Line items** — each line item (trio/pair/single) with its rabbits.
   Each rabbit shows: breed, gender, DOB, sire (name + breed), dam
   (name + breed). A small blank marking area per rabbit for handwriting
   ear-mark codes after printing.
4. **Total** — sum of line item prices.
5. **Notes** — optional sale-level comments.

### Per-rabbit layout within line items

Each rabbit in a line item gets a row or card showing its breed, gender,
DOB, and parentage (sire and dam with their breeds). A blank marking area
is included for handwriting identification marks after printing.

When all rabbits in a line item share the same DOB and/or parents, those
fields may be consolidated in a header to reduce repetition.

### CSS principles

- Plain CSS with semantic class names (e.g., `.line-item`, `.rabbit-info`,
  `.breed`), not utility chains.
- All styling in the CSS file; HTML contains only structural classes.
- ~100-150 lines of CSS handles everything.
- Single fixed-width page — no responsive layout needed.

### Implementation note

Exact aesthetics (fonts, colors, spacing, logo placement, border styles,
typography choices) will be finalized during implementation. The design
specifies structure and principles; implementation handles visual polish.

## 8. Security Considerations

### Customer PII

Sale JSON contains customer PII (name, phone number, potentially email).
This data is:

- **At rest** — JSON files in `output/` directory. These are the operator's
  records, stored locally. The `output/` directory is gitignored to prevent
  accidental commits of customer data.
- **In transit** — not applicable. This is a local CLI tool with no network
  surface. No HTTP endpoints, no API keys, no remote calls.
- **In logs** — the renderer logs operational messages (file paths, errors)
  but does not log customer PII. Per `security/foundations:never-log-credentials`
  and `observability/foundations:no-pii-in-observability-without-explicit-policy`.

### Secret scanning

gitleaks runs on every commit via pre-commit hook. The project has no API
keys or tokens, but the discipline is maintained per
`core/version-control:pre-commit-hooks-required`.

### Threat model

This is a local CLI tool run by the operator on their own machine. The threat
model is minimal:

- No network surface (no HTTP, no API).
- No authentication or authorization (single operator).
- No database (flat files).
- No user input beyond the sale JSON file path.

The primary risk is accidental commit of customer PII. Mitigation: `output/`
is gitignored, gitleaks scans for secrets.

## 9. Testing Strategy

### Unit tests

| Module | What's tested |
|--------|---------------|
| `models.py` | Pydantic model validation, JSON round-trip, immutability (frozen), field constraints, enum values |
| `pricing.py` | Unit price thresholds, line item totals, edge cases |
| `renderer.py` | HTML template rendering, PDF generation, logo resolution |
| `cli.py` | Argument parsing, missing file handling, output paths |

### Fixture data

- `tests/fixtures/sample_sale.json` — a sample trio sale for testing.
- `tests/fixtures/sample_breeders.json` — sample breeding stock.

Fixtures are self-contained; tests don't depend on operator data.

### Integration testing

The full pipeline (JSON → HTML → PDF) needs at least one integration test
that:

1. Loads sample sale JSON.
2. Renders through Jinja2 template.
3. Generates PDF via weasyprint.
4. Verifies the PDF is non-empty and contains expected content.

This catches template rendering errors, CSS loading failures, and weasyprint
configuration issues that unit tests miss.

### Test naming

Tests describe behavior, not implementation. Per
`testing/foundations:test-names-describe-behavior`:

```python
# Good
def test_unit_price_returns_bulk_rate_for_three_rabbits():
def test_rabbit_model_is_frozen():

# Bad
def test_pricing_function():
def test_rabbit_class():
```

### Test independence

Each test runs in isolation, in any order, without shared mutable state. Per
`testing/foundations:test-independence`.

## 10. ESL Compliance

See `docs/impl.md` → "ESL Compliance" for the full rule-by-rule compliance
matrix. Keeping compliance tracking with the implementation plan avoids drift —
as rules are satisfied during implementation, the matrix is updated in place.

## Terms

- **Operator** — the wabbitry owner (Lobanz) who runs the tool and manages sales.
- **ESL** — Engineering Standards Library. The rule bundle this project follows.
  Located at `/home/hermes/projects/eslbundle/standards/`.
- **ADR** — Architecture Decision Record. A document capturing a decision,
  its context, alternatives considered, and consequences.
- **Sale JSON** — the self-contained JSON file representing one sale. The
  contract between the Hermes natural-language path and the CLI path.
- **breeders.json** — the breeding stock inventory file. A lookup reference,
  not consumed by the renderer.
- **Line item** — a group of rabbits on a receipt (trio, pair, or single).
- **NZW** — New Zealand White. The breed of all rabbits. TAMUK and M70 are
  strains, not breeds.
- **Strain** — a composite line within NZW (TAMUK, M70, TAMUK Composite).
  Always output as "TAMUK NZW" or "M70 NZW", never bare strain names.
- **Trio** — 1 buck + 2 does (3 rabbits). Standard sale unit at $120.
- **Marking area** — a blank space on the printed receipt for handwriting
  ear-mark codes (red + = buck, black ○ = doe).
