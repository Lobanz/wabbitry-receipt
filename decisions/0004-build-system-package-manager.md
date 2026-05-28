---
id: 0004
title: Build system, package manager, and CLI entry point
date: 2026-05-28
status: accepted
---

# 0004: Build System, Package Manager, and CLI Entry Point

## Context

The project needs:
1. A build backend so `pip install` (or `uv pip install`) includes non-Python
   files (templates, CSS, logo) alongside the Python code.
2. A package manager for dependency management and installation.
3. A CLI entry point so the tool runs as `wabbitry-receipt generate sale.json`
   without `python -m`, venv activation, or `uv run`.

Currently pyproject.toml has no `[build-system]` section, so `pip install .`
fails. Templates in `src/wabbitry_receipt/templates/` are not declared as
package data and would be excluded from installs.

## Decision

### Build backend: hatchling

hatchling is the build backend. It automatically includes all files under the
package directory (including non-Python files like templates, CSS, and images)
without requiring explicit `package-data` configuration.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Package manager: uv

uv (by Astral, makers of ruff) is the standard package manager. It:
- Manages its own Python runtimes (independent of system Python)
- Is 10-100x faster than pip (written in Rust)
- Uses pyproject.toml as the source of truth
- Provides `uv tool install` for standalone CLI tool installation

### CLI entry point: `[project.scripts]`

```toml
[project.scripts]
wabbitry-receipt = "wabbitry_receipt.cli:main"
```

After `uv tool install`, this creates a `wabbitry-receipt` command that works
like any regular CLI tool — no venv activation, no `python -m`, no `uv run`.

### Installation: `uv tool install`

```bash
uv tool install -e /path/to/wabbitry-receipt
```

Installs the package in an isolated environment with its own Python. The
`wabbitry-receipt` command is placed in `~/.local/bin/` (which is on PATH).
Updates via `uv tool install --force` or `uv tool upgrade`.

### Runtime template access: `importlib.resources`

```python
from importlib.resources import files

template_dir = files("wabbitry_receipt") / "templates"
```

Standard Python 3.9+ API for accessing package data at runtime. Works
regardless of install method (pip, uv, editable, zip).

## Alternatives Considered

- **setuptools (traditional)**: Rejected — requires explicit `package-data`
  configuration to include non-Python files. More verbose config.
- **flit**: Rejected — simpler than setuptools but less featureful than
  hatchling. Hatchling is the standard modern choice.
- **pip + venv + wrapper scripts**: Rejected — messy PATH management, venv
  activation, wrapper scripts. uv handles all of this cleanly.
- **pipx**: Rejected — uv tool install is its spiritual successor, faster
  and more actively developed.
- **CLI arg `--template-dir`**: Rejected — templates are package data, not
  user-configurable. `importlib.resources` finds them automatically. Override
  path can be added later if needed (non-breaking addition).
- **PyInstaller/Nuitka (binary compilation)**: Rejected — overkill for a
  local CLI tool. Adds complexity, loses Python flexibility.

## Consequences

- `uv tool install` creates a standalone `wabbitry-receipt` command in
  `~/.local/bin/`. No venv activation, no `python -m`, no system Python
  dependency.
- Templates, CSS, and logo are automatically included in the package by
  hatchling. No manual `package-data` configuration needed.
- `importlib.resources.files()` provides runtime access to templates. Works
  across all installation methods.
- `uv run wabbitry-receipt ...` is still available for development (editable
  install, instant code changes).
- The operator needs zero Python knowledge. `wabbitry-receipt generate
  sale.json` just works.
- System dependencies for weasyprint (libpango, libcairo, libgdk-pixbuf)
  still need to be installed separately.
