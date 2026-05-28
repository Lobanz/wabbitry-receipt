#!/usr/bin/env bash
# Run all static checks: format, lint, type-check.
# Used by pre-commit hook and CI; humans run this locally before push.
# Exits non-zero on any failure.
set -euo pipefail

ruff format --check .
ruff check .
mypy .
