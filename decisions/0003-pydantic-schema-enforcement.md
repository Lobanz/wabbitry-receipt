---
id: 0003
title: Pydantic for schema enforcement
date: 2026-05-28
status: accepted
---

# 0003: Pydantic for Schema Enforcement

## Context

models.py uses `@dataclass(frozen=True)` for `Rabbit`, `Parent`, `LineItem`,
and `Sale`. These models are loaded from sale JSON files — either constructed
by the Hermes NL agent path or provided directly by the operator via CLI.

Dataclasses provide immutability but zero validation. A field typed `str`
happily accepts `None`, `42`, or `""`. A `float` field accepts `-5`. Invalid
data surfaces only at render time (broken PDFs) or worse — silently produces
incorrect receipts.

The project already declares pydantic as a dependency in pyproject.toml.

## Decision

Use pydantic `BaseModel` with `ConfigDict(frozen=True)` instead of
`@dataclass(frozen=True)` for all domain models. Validate JSON at load time
via `Sale.model_validate_json()`.

Pydantic provides:

- **Schema enforcement at the trust boundary** — invalid JSON fails
  immediately with a human-readable `ValidationError`, not silently at
  render time.
- **Type coercion** — `"2026-05-28"` in JSON becomes `date(2026, 5, 28)`
  automatically.
- **Field constraints** — `Field(gt=0)` on price rejects zero and negatives
  at construction time.
- **JSON round-trip** — `model_validate_json()` for loading,
  `model_dump_json()` for serialization, both schema-aware.
- **Immutability preserved** — `ConfigDict(frozen=True)` prevents field
  assignment, same as `@dataclass(frozen=True)`.

This decision reflects a broader engineering principle: input validation is
security hygiene. Even for a local CLI tool with no network surface,
validating data at the boundary is a habit worth building into every project.

## Alternatives Considered

- **Keep dataclasses, add manual validation.** Rejected — requires
  hand-written checks for every field, every constraint. Error-prone,
  verbose, easy to forget a field. No standard error format.
- **attrs + cattrs.** Rejected — pydantic is already in deps, attrs would
  add a second dependency for the same purpose.
- **JSON Schema validation only (no model change).** Rejected — validates
  structure but doesn't produce typed Python objects. Still need manual
  construction after validation.

## Consequences

- `Sale.model_validate_json(data)` replaces manual JSON loading and object
  construction — one call handles both.
- Invalid sale JSON raises `ValidationError` at the CLI entry point, before
  the renderer runs. Error messages include field names and constraint
  violations.
- Existing `tests/fixtures/sample_sale.json` loads cleanly through pydantic
  (dates coerce from strings, types match).
- The `frozen-dataclass-for-compound-constants` ESL rule is satisfied via
  pydantic's `ConfigDict(frozen=True)` rather than `@dataclass(frozen=True)`.
  The intent (immutability) is preserved; the mechanism differs.
- mypy --strict works with pydantic via the built-in plugin (configured in
  pyproject.toml).
