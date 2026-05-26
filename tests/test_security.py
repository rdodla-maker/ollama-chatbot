"""Tests for filesystem security helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest

from core.security import resolve_safe_path


def test_blocks_traversal():
    with pytest.raises(ValueError):
        resolve_safe_path("../../../Windows/System32/drivers/etc/hosts")
