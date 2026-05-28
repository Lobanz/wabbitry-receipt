# Tooling

Development tools used by wabbitry-receipt and why each is here.

## Package Management

### uv

Fast Python package manager and resolver (by Astral, makers of ruff). Replaces
pip and venv. Written in Rust, 10-100x faster than pip.

**What it does for us:**

- **`uv pip install -e ".[dev]"`** — installs the project in editable mode with dev deps
- **`uv tool install -e .`** — installs as a standalone CLI tool in `~/.local/bin/`
- **`uv run wabbitry-receipt ...`** — runs commands in the project venv without activation
- Manages its own Python runtimes (independent of system Python)

**Why uv:** the current standard for Python package management. Self-contained,
fast, and handles Python version management. `uv tool install` gives us a
standalone `wabbitry-receipt` command with no venv activation needed.

### hatchling

Build backend. Tells Python how to package the project, including non-Python
files (templates, CSS, logo).

**What it does for us:**

- Automatically includes all files under `src/wabbitry_receipt/` as package data
- No manual `package-data` configuration needed
- Works with uv, pip, and all standard Python packaging tools

**Config:** `pyproject.toml [build-system]`

## Python Quality

### Ruff

All-in-one Python linter and formatter. Replaces flake8, isort, pyflakes, pycodestyle,
and black with a single fast tool.

**What it does for us:**

- **Format** (`ruff format`) — enforces consistent code style (indentation, quote
  style, trailing commas, line length). No debates about formatting in PRs.
- **Lint** (`ruff check`) — catches bugs and enforces code quality rules:
  - `E`, `F`, `W` — pyflakes/pycodestyle basics (syntax errors, unused imports)
  - `I` — import sorting
  - `N` — naming conventions (PEP 8 snake_case, CamelCase)
  - `D` — docstring enforcement (Google-style)
  - `ANN` — type annotation enforcement
  - `B` — common bugbear traps (mutable default args, `assert False` in tests)
  - `UP` — pyupgrade (modernize syntax for target Python version)
  - `S` — security checks (hardcoded passwords, suspicious imports)

**Config:** `pyproject.toml [tool.ruff]`

**Test exemptions:** tests are exempt from `D` (docstrings), `ANN` (type hints), and
`S101` (assert) — these rules are noise in test files.

**Line length:** 100 (not 88, not 120 — 100 is the sweet spot for readability on
modern monitors).

### mypy

Static type checker. Catches type errors at build time instead of runtime.

**What it does for us:**

- Enforces `--strict` mode — every function has type hints, no implicit `Any`
- Catches None-dereference bugs, wrong argument types, missing return types
- Validates pydantic model types match actual usage

**Config:** `pyproject.toml [tool.mypy]`

**Why strict:** a non-strict mypy config is almost useless — it misses too much.
Strict mode is the whole point of using a type checker.

### pytest

Test framework.

**What it does for us:**

- Runs the test suite (`tests/`)
- Fixture system for shared test data (sample rabbits, sample sales)
- `pytest-cov` plugin for coverage reporting

**Config:** `pyproject.toml [tool.pytest.ini_options]`

### djLint

HTML template linter and formatter for Jinja2, Django, Nunjucks, and other
template languages. Catches structural HTML errors, attribute quoting,
nesting issues.

**What it does for us:**

- **Lint** (`djlint --lint`) — catches HTML structure errors in `.html.j2` templates
- **Format** (`djlint --reformat`) — enforces consistent indentation and attribute style
- `--profile jinja` enables Jinja2-specific rules

**Config:** `pyproject.toml [tool.djlint]`

**Why:** ESL has no HTML/template language module. djLint fills that gap as
project-level tooling. Catches real issues (unclosed tags, missing attributes)
that ruff and mypy can't see.

## Git Hooks (pre-commit)

Pre-commit hooks run automatically before every commit. They prevent bad code from
entering the repo.

### pre-commit-hooks (general hygiene)

- `trailing-whitespace` — strips trailing spaces (prevents noisy diffs)
- `end-of-file-fixer` — ensures files end with a newline
- `check-added-large-files` — blocks accidentally committing large files (>500KB)
- `check-merge-conflict` — catches unresolved merge conflict markers
- `check-yaml` — validates YAML syntax
- `check-json` — validates JSON syntax

### gitleaks (secret scanning)

Scans every commit for leaked secrets — API keys, passwords, tokens.

**Why:** one leaked key means rotating it. gitleaks catches it before it hits the repo.
Non-negotiable for any repo that might touch customer data or API credentials.

### conventional-pre-commit (commit message format)

Enforces conventional commit format: `type(scope): subject`

**Why:** consistent commit messages enable automated changelogs, semantic versioning,
and clean `git log` output. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`,
`style`, `perf`, `ci`, `build`, `revert`.

### djLint (HTML template linting)

Lints Jinja2 HTML templates for structural errors, attribute quoting, nesting.
Runs with `--profile jinja` for Jinja2-specific rules.

**Why:** Catches HTML issues in templates that Python linters can't see — unclosed
tags, missing attributes, invalid nesting. Configured via `pyproject.toml [tool.djlint]`
with H030/H031 suppressed (meta description/keywords irrelevant for PDF templates).

## Shell Scripts

### scripts/check.sh

Runs all static checks in sequence: format check, lint, type check.

```bash
scripts/check.sh
```

**When:** before every push. Fast feedback on code quality without running tests.

### scripts/test.sh

Runs the test suite.

```bash
scripts/test.sh
```

**When:** before every push, and after any logic change.

## Runtime Dependencies

### Jinja2

Template engine. Renders sale data into HTML via templates.

### weasyprint

HTML/CSS to PDF renderer. Takes the filled HTML template and produces a styled PDF
receipt. Requires system libraries: `libpango`, `libcairo`, `libgdk-pixbuf`.

### pydantic

Data validation. Deserializes sale JSON into typed Python models with validation
at load time (ADR 0003).

## Environment

- **Package manager:** uv (manages its own Python, independent of system)
- **Build backend:** hatchling (auto-includes package data)
- **CLI entry point:** `[project.scripts]` in pyproject.toml
- **Install for development:** `uv pip install -e ".[dev]"`
- **Install as CLI tool:** `uv tool install -e .`
- **Run without activation:** `uv run wabbitry-receipt ...` or just
  `wabbitry-receipt ...` after `uv tool install`
- **Template access:** `importlib.resources.files("wabbitry_receipt") / "templates"`
