"""Wabbitry Receipt — sales receipt generator for Wascally Wabbitry."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("wabbitry-receipt")
except PackageNotFoundError:
    __version__ = "0.0.0"
