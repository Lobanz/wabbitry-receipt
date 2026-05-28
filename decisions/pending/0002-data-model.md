---
id: pending-20260528-data-model
title: Sale JSON schema and data model
date: 2026-05-28
status: pending
trigger: ask-before-assume
context_modules: [core/engineering-principles, languages/python]
---

# Data Model for Sale and Breeder JSON

## Context

The receipt generator needs two JSON data sources: breeders.json (breeding stock
inventory, maintained by operator) and sale.json (one per sale). The schema must
support both CLI and Hermes natural-language paths.

## Question

What fields belong in sale.json, and how should it reference breeders.json?

## Options

### Option A: Flat sale JSON (self-contained)
Each sale.json includes all rabbit details inline (sire/dam names, strains, DOB).
No reference to breeders.json at render time. Simple, auditable, no dependency.

### Option B: Referenced sale JSON
sale.json references rabbit IDs from breeders.json. Renderer looks up parentage.
Normalized but requires both files at render time.

### Option C: Hybrid
sale.json includes rabbit details but renderer can cross-validate against
breeders.json for consistency. Best of both but more complex.

## Recommendation

Option A (flat). The sale is a point-in-time record. Parentage info is duplicated
from breeders.json at sale creation time but the receipt is self-contained.
Normalization deferred to when the reservation system takes shape.

## Affected work

models.py dataclass design, sale.json schema, renderer template variables.
