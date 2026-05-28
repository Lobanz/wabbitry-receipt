"""Tests for CLI interface."""

from wabbitry_receipt.cli import main


def test_cli_no_args(capsys) -> None:
    try:
        main([])
    except SystemExit as e:
        assert e.code == 2
