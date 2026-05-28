"""Tests for CLI interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wabbitry_receipt.cli import main

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_sale_dict(**overrides: object) -> dict[str, object]:
    """Return a minimal valid sale dict, with optional field overrides."""
    base: dict[str, object] = {
        "customer_name": "Test Customer",
        "customer_contact": "555-0100",
        "sale_date": "2026-05-28",
        "pickup": "2026-05-30",
        "line_items": [
            {
                "type": "trio",
                "price": 120.0,
                "rabbits": [
                    {
                        "gender": "M",
                        "breed": "TAMUK NZW",
                        "dob": "2026-03-25",
                        "sire": {"name": "Xander", "breed": "TAMUK NZW"},
                        "dam": {"name": "Harmony", "breed": "TAMUK NZW"},
                    },
                    {
                        "gender": "F",
                        "breed": "TAMUK NZW",
                        "dob": "2026-03-25",
                        "sire": {"name": "Willy", "breed": "TAMUK NZW"},
                        "dam": {"name": "Fiona", "breed": "TAMUK NZW"},
                    },
                    {
                        "gender": "F",
                        "breed": "TAMUK NZW",
                        "dob": "2026-03-25",
                        "sire": {"name": "Willy", "breed": "TAMUK NZW"},
                        "dam": {"name": "Fiona", "breed": "TAMUK NZW"},
                    },
                ],
            },
        ],
        "total": 120.0,
    }
    base.update(overrides)
    return base


def _write_sale_json(tmp_path: Path, **overrides: object) -> Path:
    """Write a minimal sale JSON file and return its path."""
    sale_path = tmp_path / "sale.json"
    sale_path.write_text(json.dumps(_minimal_sale_dict(**overrides)), encoding="utf-8")
    return sale_path


# ---------------------------------------------------------------------------
# Tests: no-args exits with code 2
# ---------------------------------------------------------------------------


def test_cli_no_args(capsys: object) -> None:
    """CLI with no args exits 2 (argparse usage error)."""
    with pytest.raises(SystemExit, match="2"):
        main([])


# ---------------------------------------------------------------------------
# Tests: end-to-end generate
# ---------------------------------------------------------------------------


def test_generate_creates_pdf(tmp_path: Path) -> None:
    """generate command produces a PDF file."""
    sale_path = _write_sale_json(tmp_path)
    out_dir = tmp_path / "out"
    main(["generate", str(sale_path), "--output-dir", str(out_dir)])

    pdfs = list(out_dir.rglob("*.pdf"))
    assert len(pdfs) == 1
    assert pdfs[0].stat().st_size > 0


def test_generate_copies_json_to_output(tmp_path: Path) -> None:
    """generate command copies the source sale JSON alongside the PDF."""
    sale_path = _write_sale_json(tmp_path)
    out_dir = tmp_path / "out"
    main(["generate", str(sale_path), "--output-dir", str(out_dir)])

    jsons = list(out_dir.rglob("*.json"))
    assert len(jsons) == 1
    # Content should match the original.
    original = json.loads(sale_path.read_text(encoding="utf-8"))
    copied = json.loads(jsons[0].read_text(encoding="utf-8"))
    assert copied == original


# ---------------------------------------------------------------------------
# Tests: --output-dir flag
# ---------------------------------------------------------------------------


def test_output_dir_flag_controls_directory(tmp_path: Path) -> None:
    """--output-dir places files under the specified directory."""
    sale_path = _write_sale_json(tmp_path)
    out_dir = tmp_path / "custom" / "dir"
    main(["generate", str(sale_path), "--output-dir", str(out_dir)])

    pdfs = list(out_dir.rglob("*.pdf"))
    assert len(pdfs) == 1


# ---------------------------------------------------------------------------
# Tests: --output flag
# ---------------------------------------------------------------------------


def test_output_flag_overrides_entire_path(tmp_path: Path) -> None:
    """--output sets the full path, ignoring --output-dir."""
    sale_path = _write_sale_json(tmp_path)
    explicit_path = tmp_path / "explicit" / "receipt.pdf"
    main(
        [
            "generate",
            str(sale_path),
            "--output-dir",
            str(tmp_path / "ignored"),
            "--output",
            str(explicit_path),
        ]
    )
    assert explicit_path.exists()
    assert explicit_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Tests: env var default for --output-dir
# ---------------------------------------------------------------------------


def test_output_dir_defaults_to_env_var(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """$WABBITRY_RECEIPT_OUTPUT_DIR is used when --output-dir is not given."""
    sale_path = _write_sale_json(tmp_path)
    env_dir = tmp_path / "from-env"
    monkeypatch.setenv("WABBITRY_RECEIPT_OUTPUT_DIR", str(env_dir))
    main(["generate", str(sale_path)])

    pdfs = list(env_dir.rglob("*.pdf"))
    assert len(pdfs) == 1


# ---------------------------------------------------------------------------
# Tests: fallback default output dir
# ---------------------------------------------------------------------------


def test_output_dir_falls_back_to_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default output dir is 'output/' when env var is unset."""
    sale_path = _write_sale_json(tmp_path)
    monkeypatch.delenv("WABBITRY_RECEIPT_OUTPUT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    main(["generate", str(sale_path)])

    pdfs = list((tmp_path / "output").rglob("*.pdf"))
    assert len(pdfs) == 1


# ---------------------------------------------------------------------------
# Tests: exit codes
# ---------------------------------------------------------------------------


def test_generate_exits_cleanly_on_valid_input(tmp_path: Path) -> None:
    """Exit code 0 on valid input."""
    sale_path = _write_sale_json(tmp_path)
    out_dir = tmp_path / "out"
    # main() should not raise; if it does, the test fails naturally.
    main(["generate", str(sale_path), "--output-dir", str(out_dir)])


def test_generate_exits_with_error_on_missing_file(tmp_path: Path) -> None:
    """Exit code 1 when the sale JSON file does not exist."""
    missing = tmp_path / "nope.json"
    with pytest.raises(SystemExit, match="1"):
        main(["generate", str(missing)])


def test_generate_exits_with_error_on_invalid_json(tmp_path: Path) -> None:
    """Exit code 1 when the JSON fails pydantic validation."""
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"customer_name": 123}', encoding="utf-8")
    with pytest.raises(SystemExit, match="1"):
        main(["generate", str(bad_path)])
