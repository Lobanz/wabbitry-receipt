# Wabbitry Receipt — Implementation Plan

This document breaks the design (`docs/design.md`) into staged execution
phases. Each phase produces testable deliverables and commits independently.

**Decisions made during design review (2026-05-28):**

- **Pydantic for schema enforcement.** Models.py converts from dataclasses to
  pydantic. Rationale: input validation is security hygiene — even for a local
  CLI tool, validating JSON at load time catches malformed data before it
  reaches the renderer. Pydantic is already declared as a dependency.
  See ADR 0003 (`decisions/0003-pydantic-schema-enforcement.md`).
- **Build system, package manager, CLI entry point.** hatchling as build
  backend, uv as package manager, `[project.scripts]` for CLI entry point.
  `uv tool install` creates a standalone `wabbitry-receipt` command.
  See ADR 0004 (`decisions/0004-build-system-package-manager.md`).
- **Logo file** confirmed at `src/wabbitry_receipt/templates/logo.png`.

## Table of Contents

- [Dependencies Between Phases](#dependencies-between-phases)
- [Phase 0: Build System Setup](#phase-0-build-system-setup)
- [Phase 1: Schema Validation + Pydantic Models](#phase-1-schema-validation--pydantic-models)
- [Phase 2: Renderer Foundation](#phase-2-renderer-foundation)
- [Phase 3: CLI Completion](#phase-3-cli-completion)
- [Phase 4: Integration + Polish](#phase-4-integration--polish)
- [Phase 5: Commit + Push](#phase-5-commit--push)
- [ESL Compliance](#esl-compliance)

## Dependencies Between Phases

```
Phase 0 (build system) ──→ Phase 1 (pydantic models) ──→ Phase 2 (renderer)
                                                              │
                                                              ▼
                                                    Phase 3 (CLI)
                                                              │
                                                              ▼
                                                    Phase 4 (integration)
                                                              │
                                                              ▼
                                                    Phase 5 (commit + push)
```

Phase 0 sets up the build system, package manager, and CLI entry point.
Phase 1 establishes the data contract (pydantic models with schema
enforcement). Phase 2 builds the renderer against those models. Phase 3
wires them together in the CLI. Phases 1 and 2 are independent, but
pydantic-first means the renderer is built against the real model API
from day one — no dataclass-to-pydantic swap later.

---

## Phase 0: Build System Setup

**Goal:** Configure build backend, package manager, and CLI entry point so
the project is installable and runnable as a regular command.

### Tasks

| Task | File/Action |
|------|-------------|
| Add build system | `pyproject.toml` — `[build-system]` with hatchling |
| Add CLI entry point | `pyproject.toml` — `[project.scripts]` |
| Verify install | `uv pip install -e ".[dev]"` succeeds |
| Verify CLI | `uv run wabbitry-receipt --help` works |
| Verify tool install | `uv tool install -e .` creates standalone command |
| Verify template access | `importlib.resources.files()` finds templates |

### Deliverable

Project installs via uv. CLI entry point works. Templates accessible via
`importlib.resources`. No venv activation needed to run the tool.

### ESL rules active in this phase

- `concrete-decisions-recorded` — ADR 0004 records the build system decision
- `explicit-dependencies` — build backend and package manager are explicit in pyproject.toml

---

## Phase 1: Schema Validation + Pydantic Models

**Goal:** Convert models.py from dataclasses to pydantic. JSON loads validate
against the schema at construction time.

### Files to modify

| File | Change |
|------|--------|
| `src/wabbitry_receipt/models.py` | dataclasses → pydantic BaseModel with frozen config |
| `tests/test_models.py` | Add pydantic validation tests, JSON round-trip tests |
| `tests/conftest.py` | Update fixtures if model construction changes |

### Pydantic model design

```python
from pydantic import BaseModel, ConfigDict, Field

class Parent(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    breed: str

class Rabbit(BaseModel):
    model_config = ConfigDict(frozen=True)
    gender: str
    breed: str
    dob: date
    sire: Parent
    dam: Parent

class LineItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: LineItemType
    price: float = Field(gt=0)
    rabbits: list[Rabbit]
    desc: str | None = None

class Sale(BaseModel):
    model_config = ConfigDict(frozen=True)
    customer_name: str
    customer_contact: str
    sale_date: date
    pickup: date
    line_items: list[LineItem]
    total: float = Field(ge=0)
    notes: str = ""
```

Key changes from dataclasses:
- `ConfigDict(frozen=True)` replaces `@dataclass(frozen=True)`
- `Field(gt=0)` on price rejects zero and negative values
- `Field(ge=0)` on total allows zero (edge case: free sample)
- `model_validate_json()` loads + validates in one call
- `model_dump()` / `model_dump_json()` for serialization

### Validation behavior

- Type coercion: `"2026-05-28"` string → `date(2026, 5, 28)` automatically
- Missing required fields: `ValidationError` with field name and message
- Wrong types: `ValidationError` with expected vs actual
- Constraint violations: `Field(gt=0)` rejects `price: 0` or `price: -5`

### Test plan — expanded `test_models.py`

| Test | What it verifies |
|------|-----------------|
| `test_sale_from_valid_json` | JSON round-trip: load → model → dump matches |
| `test_sale_rejects_missing_customer_name` | ValidationError on missing required field |
| `test_sale_rejects_wrong_type_customer_name` | ValidationError on `customer_name: 123` |
| `test_line_item_rejects_zero_price` | `Field(gt=0)` catches `price: 0` |
| `test_line_item_rejects_negative_price` | `Field(gt=0)` catches `price: -5` |
| `test_sale_rejects_invalid_date_format` | ValidationError on `sale_date: "not-a-date"` |
| `test_rabbit_rejects_missing_sire` | ValidationError on missing nested object |
| `test_sale_from_sample_fixture` | `tests/fixtures/sample_sale.json` loads cleanly |
| `test_model_immutability` | Cannot assign to frozen model fields |
| Existing tests | Immutability, enum values — still pass with pydantic |

### Deliverable

Models validate JSON at load time. Invalid data raises `ValidationError` with
clear messages. Existing fixtures load cleanly. All model tests pass.

### ESL rules active in this phase

- `validate-at-trust-boundaries` — pydantic validates at JSON load boundary
- `no-magic-literals` — Field constraints use named parameters, not inline checks
- `tests-have-meaningful-assertions` — each test asserts specific validation behavior
- `test-names-describe-behavior` — test names describe what's validated

---

## Phase 2: Renderer Foundation

**Goal:** HTML template + CSS + renderer module that produces a styled receipt
from pydantic model objects.

### Files to create

| File | Purpose |
|------|---------|
| `src/wabbitry_receipt/templates/receipt.html.j2` | Jinja2 template — business header, sale info, line items with parentage, total, notes, marking areas |
| `src/wabbitry_receipt/templates/receipt.css` | Plain CSS, semantic classes (~100-150 lines). `@page` rules for print layout. |
| `src/wabbitry_receipt/renderer.py` | `render_html(sale, template_dir) -> str` and `render_pdf(html, css_path, logo_path) -> bytes` |
| `tests/test_renderer.py` | HTML output assertions (sections present, data populated), PDF generation smoke test |

### Template structure (per design.md section 7)

1. Business header — logo, "Wascally Wabbitry", contact, Hazel Green AL
2. Sale info — customer name, contact, sale date, pickup date
3. Line items — each with type, price, rabbits (breed, gender, DOB, sire, dam, marking area)
4. Total
5. Notes (optional)

### CSS principles

- Semantic classes: `.line-item`, `.rabbit-info`, `.breed`, `.marking-area`
- All styling in CSS file; HTML has only structural classes
- `@page` for print margins and page size
- Single fixed-width page — no responsive layout

### Renderer API

```python
def render_html(sale: Sale, template_dir: Path) -> str:
    """Render sale data to HTML string using Jinja2 template."""

def render_pdf(html: str, css_path: Path, logo_path: Path) -> bytes:
    """Convert HTML to PDF via weasyprint with embedded CSS."""
```

`render_html` and `render_pdf` are separate functions. This lets tests verify
HTML content without depending on weasyprint's system libraries.

### Logo resolution

Logo lives at `src/wabbitry_receipt/templates/logo.png`. The template
references it by relative path; weasyprint resolves it during PDF rendering.
The renderer passes the template directory to weasyprint as the base URL.

### Test plan — `test_renderer.py`

| Test | What it verifies |
|------|-----------------|
| `test_rendered_html_contains_business_header` | "Wascally Wabbitry" present |
| `test_rendered_html_contains_customer_info` | Customer name and contact rendered |
| `test_rendered_html_contains_line_items` | Each line item's rabbits appear |
| `test_rendered_html_contains_total` | Dollar total rendered |
| `test_rendered_html_contains_parentage` | Sire and dam names appear |
| `test_rendered_html_contains_notes_when_present` | Notes section renders |
| `test_rendered_html_omits_notes_when_empty` | No empty notes section |
| `test_render_pdf_produces_nonempty_bytes` | PDF generation smoke test |
| `test_render_pdf_contains_expected_content` | PDF bytes contain customer name (pyPdf or bytestring search) |

### Deliverable

A renderer that takes pydantic Sale model objects and produces a styled HTML
string and PDF bytes. Tests pass. Template handles all layout sections from
the design.

### ESL rules active in this phase

- `no-magic-literals` — template paths, CSS path, logo path as named constants
- `explicit-dependencies` — renderer takes template_dir as argument, no globals
- `module-headers-required` — renderer.py gets a module docstring
- `doc-comments-on-public-interfaces` — render_html and render_pdf get docstrings

---

## Phase 3: CLI Completion

**Goal:** Full CLI with output path resolution, JSON copy, and end-to-end
file generation.

### Files to modify

| File | Change |
|------|--------|
| `src/wabbitry_receipt/cli.py` | Complete arg parsing, output resolution, JSON copy, call renderer |
| `src/wabbitry_receipt/__main__.py` | Entry point (may already exist) |
| `tests/test_cli.py` | Full CLI tests |

### Output path resolution (per design.md section 4)

Priority order:
1. `--output` — full path, overrides everything, relative to PWD
2. `--output-dir` — base directory, subfolder + filename computed from JSON
3. `$WABBITRY_RECEIPT_OUTPUT_DIR` env var — if set, used as default for `--output-dir`
4. `output/` — hardcoded fallback

When `--output` is set, `--output-dir` is ignored.

### JSON copy

After rendering, copy the source sale JSON into the output directory alongside
the PDF. This keeps source data co-located with the rendered receipt.

### CLI flow

```
1. Parse args (sale_json, --output-dir, --output)
2. Load sale JSON → Sale.model_validate_json()
3. Resolve output path
4. render_html(sale, template_dir)
5. render_pdf(html, css_path, logo_path)
6. Write PDF to output path
7. Copy sale JSON to output directory
```

### Test plan — `test_cli.py`

| Test | What it verifies |
|------|-----------------|
| `test_generate_creates_pdf` | End-to-end: JSON in → PDF file out |
| `test_generate_copies_json_to_output` | JSON file appears alongside PDF |
| `test_output_dir_flag_controls_directory` | `--output-dir /tmp/test` works |
| `test_output_flag_overrides_entire_path` | `--output /tmp/out.pdf` ignores `--output-dir` |
| `test_output_dir_defaults_to_env_var` | `$WABBITRY_RECEIPT_OUTPUT_DIR` respected |
| `test_output_dir_falls_back_to_output` | Default is `output/` when env var unset |
| `test_generate_exits_cleanly_on_valid_input` | Exit code 0 |
| `test_generate_exits_with_error_on_missing_file` | Exit code 1, error message |
| `test_generate_exits_with_error_on_invalid_json` | Exit code 1, ValidationError message |

### Deliverable

Full CLI works: `python -m wabbitry_receipt generate sale.json` produces PDF
and JSON copy in the output directory. All output path modes work. Tests pass.

### ESL rules active in this phase

- `explicit-dependencies` — CLI parses args at entry, passes through to renderer
- `exceptions-not-error-codes` — invalid input raises, doesn't return error codes
- `never-log-credentials` — CLI logs operational messages, not customer PII
- `emit-at-decision-points` — logs at file loaded, rendered, written

---

## Phase 4: Integration + Polish

**Goal:** Full pipeline verified end-to-end. Repo hygiene. Documentation
updated.

### Tasks

| Task | File/Action |
|------|-------------|
| Integration test | Full pipeline: sample JSON → PDF → verify content |
| Manual PDF verification | Open generated PDF, check layout, fonts, page breaks |
| Template aesthetics iteration | Visually inspect generated PDF and iterate on CSS/template until it looks right (fonts, spacing, logo placement, header/footer balance) |
| `.gitignore` update | Add `output/`, `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.ruff_cache/` |
| README update | Usage examples, CLI args, env var, system deps (libpango, libcairo) |
| Remove interim receipt | Delete `scripts/generate_interim.py` and `templates/interim_receipt.md` if superseded |

### Integration test

One test that:
1. Loads `tests/fixtures/sample_sale.json`
2. Calls `Sale.model_validate_json()`
3. Calls `render_html()` and `render_pdf()`
4. Verifies PDF is non-empty
5. Verifies PDF contains expected content (customer name in bytes)

This catches template rendering errors, CSS loading failures, and weasyprint
configuration issues that unit tests miss.

### Template aesthetics

Generate a PDF from the sample sale JSON. Visually inspect it — fonts, spacing,
logo placement, header/footer balance, table alignment. Iterate on
`receipt.css` and `receipt.html.j2` until it looks right. This is inherently
manual and subjective; expect multiple CSS→PDF→inspect cycles. The goal is a
receipt that looks professional enough to hand to a customer.

### Deliverable

Repo is clean. README documents usage. Integration test covers the full
pipeline. `.gitignore` protects against accidental PII commits.

---

## Phase 5: Commit + Push

**Goal:** All checks pass. Clean commit history. Push to main.

### Pre-commit verification

```bash
# Quality checks
bash scripts/check.sh    # ruff format --check, ruff check, mypy --strict

# Tests
bash scripts/test.sh     # pytest with coverage
```

### Commit strategy

Two commits, conventional format:

1. `feat: convert models to pydantic with schema validation`
   - models.py, test_models.py, conftest.py changes

2. `feat: add HTML/PDF receipt renderer and CLI`
   - Template, CSS, logo, renderer.py, cli.py, all tests
   - .gitignore, README updates

Or a single commit if the changes are tightly coupled:

```
feat: implement receipt renderer with pydantic validation and CLI

- Jinja2 HTML template with semantic CSS
- Pydantic models with schema enforcement at JSON load
- CLI with --output-dir and --output path resolution
- Full test coverage for models, renderer, and CLI
```

### Deliverable

All tests pass. All checks pass. Clean commit on main.

---

## ESL Compliance

This implementation satisfies the Engineering Standards Library rules. Below is
the mapping from each applicable rule to how this project complies.

### Design principles (core/engineering-principles.design)

| Principle | How this design complies |
|-----------|------------------------|
| `concrete-over-abstract` | Pricing constants are named `Final` vars (`SINGLE_RABBIT_PRICE`, `BULK_RABBIT_PRICE`). Breed codes are `StrEnum` values. Line item types are `LineItemType` enum. No magic numbers or string literals. |
| `open-source-by-default` | All dependencies are open source: Jinja2, weasyprint, pydantic, ruff, mypy, pytest. No closed-source or vendor-locked tooling. |
| `documentation-is-part-of-the-system` | Design doc (`docs/design.md`), tooling doc (`docs/tooling.md`), ADRs (`decisions/`), and README all ship with the code. Changes to the system update documentation in the same change. |
| `code-lives-in-the-future` | Module headers explain purpose. Docstrings describe contracts. ADRs preserve decision context. Named constants convey intent. Tests demonstrate behavior. The codebase is self-teaching to a future-AI reader. |
| `ask-before-assuming` | Ambiguous requirements produced decision stubs (ADR 0001, 0002). No silent gap-filling from training priors. |
| `designed-in-qualities` | Testing, observability (structured logging), and security (PII handling, gitleaks) are designed in from the start, not bolted on. |
| `failure-should-be-loud` | Errors are logged at error level. No silent exception suppression. REASON comments required for any intentional suppression. |
| `explicit-over-implicit` | Renderer takes template path and CSS path as arguments. No module-level globals for configuration. Dependencies injected, not imported as singletons. |

### Design principles (core/version-control.design)

| Principle | How this design complies |
|-----------|------------------------|
| `commit-history-as-documentation` | Conventional Commits format enforced. Squash-merge keeps main linear and informative. |
| `issue-linkage-is-institutional-memory` | Non-trivial commits reference issues. ADRs capture decision context. |
| `cheapest-gate-first` | Pre-commit hooks run fast checks (gitleaks, trailing whitespace, conventional commits). CI runs the full suite. |
| `main-is-always-deployable` | Feature branches, squash-merge to main. Every commit on main builds and passes tests. |

### Implementation rules (core/engineering-principles.impl)

| Rule | How this project complies |
|------|--------------------------|
| `ask-before-assume` | Decision stubs written for template engine (0001) and data model (0002). No silent assumptions about format, pricing, or schema. |
| `no-magic-literals` | `SINGLE_RABBIT_PRICE = 50.0`, `BULK_RABBIT_PRICE = 40.0`, `BULK_THRESHOLD = 3` — all named `Final` constants. `LineItemType` and breed codes as enums. |
| `no-silent-suppression` | Error handling logs at error level. Any suppression uses `# REASON:` comments explaining why. |
| `explicit-dependencies` | Renderer receives template path and CSS path as function arguments. No module-level globals for configuration. CLI args parsed at entry point, passed through. |
| `docs-with-the-system` | Design doc (`docs/design.md`), tooling doc (`docs/tooling.md`), ADRs, and README all in repo. ADR 0001 (template engine) and 0002 (data model) record decisions alongside code. |
| `concrete-decisions-recorded` | Four ADRs accepted: 0001 (Jinja2 + weasyprint), 0002 (sale JSON schema), 0003 (pydantic for schema enforcement), 0004 (build system, package manager, CLI entry point). Alternatives considered and rejected with reasons. |
| `oss-by-default` | All deps are OSS. No closed-source justification needed. |

### Implementation rules (core/version-control.impl)

| Rule | How this project complies |
|------|--------------------------|
| `conventional-commit-format` | Enforced by `conventional-pre-commit` hook at commit-msg stage. |
| `commits-reference-issues` | Non-trivial commits reference GitHub issues. |
| `branch-name-format` | `<type>/<kebab-description>` format. |
| `every-commit-buildable-with-passing-tests` | Squash-merge to main; CI verifies build + tests. |
| `no-checkpoint-commits-on-main` | Squash-merge collapses WIP commits into clean main commits. |
| `pre-commit-hooks-required` | `.pre-commit-config.yaml` with gitleaks, trailing whitespace, end-of-file fixer, large file check, merge conflict detection, YAML/JSON validation, conventional commits. |
| `no-bypass-without-justification` | `--no-verify` reserved for emergencies only. |
| `tags-follow-semver` | Semver tags on releases when applicable. |

### Security foundations (security/foundations.impl)

| Rule | Applicability | How this project complies |
|------|--------------|--------------------------|
| `validate-at-trust-boundaries` | Sale JSON input | Pydantic validates JSON at load time. Schema rejects malformed input. |
| `parameterize-all-queries` | N/A | No database. |
| `sanitize-at-point-of-use` | desc/notes HTML | Template renders with `|safe` filter. Allowed tags limited to `<b>`, `<i>`, `<br>`. |
| `never-log-credentials` | Customer PII | Renderer logs operational messages (file paths, errors), not customer data. |
| `no-hardcoded-secrets` | N/A | No API keys, tokens, or passwords in the project. |
| `no-system-internals-in-external-responses` | N/A | No external responses — local CLI tool. |
| `dual-channel-error-handling` | N/A | No external consumers. |
| `static-analysis-required` | ruff + mypy | Pre-commit hooks run ruff check, ruff format, mypy. CI re-runs. |
| `tls-required-in-production` | N/A | No network surface. |
| `defense-in-depth-required` | N/A | No authentication or authorization surface. |

### Documentation foundations (documentation/foundations.impl)

| Rule | How this project complies |
|------|--------------------------|
| `doc-comments-on-public-interfaces` | All public functions, classes, and modules have Google-format docstrings. |
| `comment-internals-when-not-obvious` | Comments explain non-obvious choices (pricing logic, breed validation). Trivial code is not commented. |
| `no-tautological-comments` | Comments add context, not restatements of code. |
| `update-comments-when-changing-code` | Docstrings updated when behavior changes. |
| `reason-comments-for-suppressions` | All lint/type suppressions use `# REASON:` comments. |
| `todos-reference-issues` | TODO comments include issue references. |
| `module-headers-required` | Every Python file starts with a module docstring. |
| `no-commented-out-code-in-commits` | No commented-out code in committed source. |
| `define-terms-before-first-use` | Domain terms defined in the design doc's Terms section. |

### Testing foundations (testing/foundations.impl)

| Rule | How this project complies |
|------|--------------------------|
| `tests-have-meaningful-assertions` | Every test asserts specific behavior (field values, immutability, pricing math). |
| `tests-verify-designed-in-obligations` | Renderer tests verify PII does NOT appear in log emissions (inverse assertion). |
| `no-tautological-tests` | Tests verify real behavior, not mock return values. |
| `test-independence` | Each test uses its own fixtures. No shared mutable state. |
| `no-flaky-tests` | No sleep-based synchronization. Deterministic test data. |
| `no-sleep-for-synchronization` | N/A — no async operations in the receipt pipeline. |
| `honest-mocks` | Mocks only at architectural boundaries (filesystem for output tests). |
| `test-names-describe-behavior` | Test names describe what the system does, not how the test works. |
| `coverage-floor-for-critical-code` | Pricing logic (financial calculations) has full coverage. |

### Observability foundations (observability/foundations.impl)

| Rule | Applicability | How this project complies |
|------|--------------|--------------------------|
| `structured-emissions-only` | Logging | Uses Python `logging` module with structured format. No `print()` in production code. |
| `logger-is-injected-dependency` | Logging | `logging.getLogger(__name__)` at module level. Python idiom; configuration explicit at startup. |
| `request-id-on-every-record` | N/A | No request processing — local CLI tool. |
| `propagate-correlation-context` | N/A | No outbound calls. |
| `emit-at-decision-points` | Renderer | Logs at key points: file loaded, template rendered, PDF written, errors. |
| `no-secrets-in-observability` | N/A | No secrets in the project. |
| `no-pii-in-observability-without-explicit-policy` | Renderer | Customer PII (name, phone) is NOT logged. Only operational messages. |
| `errors-emit-at-error-level` | Error handling | All exceptions logged at error level before propagation. |

### Python rules (languages/python.impl)

| Rule | How this project complies |
|------|--------------------------|
| `type-hints-on-public-signatures` | All public functions have type hints. mypy --strict enforces. |
| `mypy-strict-mode` | `strict = true` in pyproject.toml. |
| `any-requires-reason-comment` | No `Any` usage in current codebase. |
| `prefer-protocol-types-in-parameters` | `list[Rabbit]` used where list semantics are needed. |
| `google-docstring-format` | All docstrings use Google format. |
| `docstring-required-on-public` | Every public function, class, and module has a docstring. |
| `module-docstring-required` | Every .py file starts with a module docstring. |
| `ruff-for-format-and-lint` | ruff is the sole linter and formatter. |
| `mypy-for-type-checking` | mypy is the sole type checker. |
| `pytest-for-tests` | pytest is the test runner. |
| `commands-wrapped-in-project-script` | `scripts/check.sh` and `scripts/test.sh` wrap common operations. |
| `imports-grouped` | stdlib, then third-party, then local. ruff `I` enforces. |
| `no-star-imports` | No star imports in production code. |
| `snake-case-filenames` | All Python files use snake_case. |
| `tests-mirror-source-structure` | `tests/test_models.py` mirrors `src/wabbitry_receipt/models.py`. |
| `one-concern-per-file` | Each module has one concern: models, pricing, renderer, cli. |
| `module-level-constants-screaming-snake-case` | `SINGLE_RABBIT_PRICE`, `BULK_RABBIT_PRICE`, `BULK_THRESHOLD` — all `Final` typed. |
| `enum-for-related-constant-sets` | `LineItemType(StrEnum)` for trio/pair/single. |
| `frozen-dataclass-for-compound-constants` | `Rabbit`, `Parent`, `LineItem`, `Sale` — pydantic `BaseModel` with `ConfigDict(frozen=True)`. Migrated from dataclasses per ADR 0003 to gain schema enforcement at the JSON load boundary. |
| `exceptions-not-error-codes` | Exceptions for error handling (file not found, validation errors). |
| `custom-exception-class-per-error-category` | Will define `WabbitryReceiptError` base with domain-specific subclasses. |
| `project-base-exception-class` | `WabbitryReceiptError(Exception)` as project base. |
