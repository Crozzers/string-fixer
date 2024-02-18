import subprocess
import sys
import os
from pathlib import Path
import pytest

from src import main as string_fixer


CASES_DIR = Path(__file__).parent / 'cases'
SNAPSHOT_DIR = Path(__file__).parent / 'snapshots'

cases = [i for i in os.listdir(CASES_DIR) if os.path.isfile(CASES_DIR / i) and i.endswith('.py')]

@pytest.mark.parametrize('case', cases)
def test_snapshots(snapshot, case: str):
    snapshot.snapshot_dir = str(SNAPSHOT_DIR)
    input_file = str(CASES_DIR / case)
    output_file = str(SNAPSHOT_DIR / case)

    with open(input_file) as f:
        input_code = f.read()

    snapshot.assert_match(string_fixer.replace_docstring_single_with_double_quotes(input_code), output_file)
