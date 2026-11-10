"""Runs the JavaScript unit tests with Node when it is installed. Browser behaviour itself is not automated here."""
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed, so JavaScript tests cannot run")
def test_javascript_unit_tests_pass():
    tests = [str(p) for p in sorted(HERE.glob("*.test.mjs"))]
    assert tests, "no JavaScript tests found"
    result = subprocess.run(["node", "--test", *tests], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
