# Wabbitry Receipt

Sales receipt generator for Wascally Wabbitry (Hazel Green, AL).

Generates styled PDF receipts from structured JSON data. Dual interface:
CLI for direct use, Hermes for natural language.

## Quick Start

```bash
pip install -e .
python -m wabbitry_receipt generate data/sale.json
```

## Data Model

- `data/breeders.json` — breeding stock inventory (maintained by operator)
- `data/logo.png` — Wascally Wabbitry logo

Sale JSON schema: see `decisions/0002-data-model.md`

## Output

Generated receipts accumulate in `output/<breeding-dob>/`:
- `<customer-name>_<sale-date>.json` — sale data
- `<customer-name>_<sale-date>.pdf` — rendered receipt

## Common Commands

```bash
scripts/check.sh   # ruff format + ruff check + mypy
scripts/test.sh    # pytest
```

## ESL Compliance

This project follows [eng-std-lib](/home/hermes/projects/eslbundle/standards/AGENT-STANDARDS.md) standards.
