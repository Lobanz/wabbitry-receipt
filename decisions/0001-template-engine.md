---
id: 0001
title: Template engine selection — Jinja2 + weasyprint
date: 2026-05-28
status: accepted
---

# 0001: Template Engine Selection

## Context

Wabbitry-receipt generates PDF sales receipts from structured data. The pipeline
needs a templating engine and a PDF renderer. Candidates evaluated:

- **Jinja2 + weasyprint** — Python-native, full CSS control, HTML is human-editable.
- **pandoc + LaTeX** — gold standard for typesetting, but 1GB LaTeX install.
- **odfpy** — ODT-native, low-level, poor templating support.
- **docxtpl** — Jinja2 in DOCX, mature but requires ODT→DOCX conversion.

## Decision

Jinja2 for HTML templating, weasyprint for HTML→PDF rendering.

## Alternatives Considered

- **pandoc + LaTeX**: rejected — heavy install, overkill for a one-page receipt.
- **odfpy**: rejected — low-level, no templating support.
- **docxtpl**: rejected — DOCX format adds conversion step from existing ODT.

## Consequences

- HTML template is human-editable for edge case tweaks.
- weasyprint requires system dependencies (libcairo, libpango) — documented in README.
- CSS controls visual layout — logo placement, table styling, fonts.
- Pretty-printed HTML serves as intermediate tweaking format.
