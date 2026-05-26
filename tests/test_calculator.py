"""Tests for safe calculator tool."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from tools.calculator import calculator_tool, safe_calculate


def test_basic_math():
    assert safe_calculate("2 + 2") == 4.0
    assert safe_calculate("(3 + 5) * 2") == 16.0
    assert safe_calculate("-4 + 10") == 6.0


def test_calculator_tool_format():
    assert calculator_tool("What is 10 / 4") == "Result: 2.5"


def test_rejects_unsafe():
    try:
        safe_calculate("__import__('os').system('echo')")
        assert False, "Should have raised"
    except ValueError:
        pass
