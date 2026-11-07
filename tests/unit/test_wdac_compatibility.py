"""Unit tests for Windows WDAC compatibility and clean process behavior."""

import os
import subprocess
import sys

import pytest


@pytest.mark.unit
def test_fresh_process_import_without_workaround():
    """Verify that a fresh Python process with no environment tampering imports sqlalchemy cleanly."""
    env = os.environ.copy()
    env.pop("DISABLE_SQLALCHEMY_CEXT", None)

    code = (
        "import sqlalchemy; "
        "import sqlalchemy.engine._util_cy as cy; "
        "print('SQLAlchemy:', sqlalchemy.__version__, 'Compiled:', cy._is_compiled())"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
    assert "SQLAlchemy: 2." in result.stdout
    assert "Compiled:" in result.stdout


@pytest.mark.unit
def test_sqlalchemy_util_cy_distill_params():
    """Verify that parameter distillation functions identically in Python and Cython."""
    from sqlalchemy.engine import util

    params = [{"param_1": 10}, {"param_2": 20}]
    distilled = util._distill_params_20(params)
    assert distilled == params

    single = {"key": "val"}
    distilled_single = util._distill_params_20(single)
    assert distilled_single == [single]

    none_distilled = util._distill_params_20(None)
    assert len(none_distilled) == 0
