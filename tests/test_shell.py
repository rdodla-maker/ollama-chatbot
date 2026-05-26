import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from tools.shell_tool import _validate_command


def test_allows_pytest():
    parts = _validate_command("pytest tests/ -q")
    assert parts[0] == "pytest"


def test_blocks_pipe():
    with pytest.raises(ValueError):
        _validate_command("echo hello | rm -rf /")


def test_blocks_rm():
    with pytest.raises(ValueError):
        _validate_command("rm -rf /")
