import os
from pathlib import Path
import sys

import pytest
import string_fixer
import re

CASES_DIR = Path(__file__).parent / 'cases'
SNAPSHOT_DIR = Path(__file__).parent / 'snapshots'

cases = [
    i
    for i in os.listdir(CASES_DIR)
    if os.path.isfile(CASES_DIR / i) and i.endswith('.py')
]


@pytest.mark.parametrize('case', cases)
def test_snapshots(snapshot, case: str):
    if (match := re.match(r'.*_py3(\d+)\.py', case)):
        version = int(match.group(1))
        if sys.version_info.minor < version:
            pytest.skip(
                f'skipped {case} due to python version'
                f' (requires 3.{version}, has 3.{sys.version_info.minor})'
            )
    snapshot.snapshot_dir = str(SNAPSHOT_DIR)
    input_file = str(CASES_DIR / case)
    output_file = str(SNAPSHOT_DIR / case)

    with open(input_file) as f:
        input_code = f.read()

    snapshot.assert_match(
        string_fixer.replace_docstring_double_with_single_quotes(input_code),
        output_file,
    )
