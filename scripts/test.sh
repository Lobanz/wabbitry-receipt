#!/usr/bin/env bash
# Run test suite.
# Used by pre-push hook and CI; humans run this locally before push.
# Exits non-zero on any failure.
set -euo pipefail

pytest
