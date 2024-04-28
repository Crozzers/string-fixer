import os
import platform
import sys
from pathlib import Path

import pytest
from packaging import specifiers, version

sys.path.insert(0, str(Path(__file__).parent / '..'))

import string_fixer

CASES_DIR = Path(__file__).parent / 'cases'
SNAPSHOT_DIR = Path(__file__).parent / 'snapshots'

cases = [
    i
    for i in os.listdir(CASES_DIR)
    if os.path.isfile(CASES_DIR / i) and i.endswith('.py')
]

special_cases = {
    'f_strings_py312': {'python': '>=3.12'},
    'f_strings_py311': {'python': '<=3.11'}
}

@pytest.mark.parametrize('case', cases)
def test_snapshots(snapshot, case: str):
    if case[:-3] in special_cases:
        special = special_cases[case[:-3]]
        if special['python']:
            specifier = specifiers.Specifier(special['python'])
            current = version.Version(platform.python_version())
            if not specifier.contains(current):
                pytest.skip(
                    f'skipped {case} due to python version'
                    f' (requires {specifier}, has {current})'
                )

    snapshot.snapshot_dir = str(SNAPSHOT_DIR)
    input_file = str(CASES_DIR / case)
    output_file = str(SNAPSHOT_DIR / case)

    with open(input_file) as f:
        input_code = f.read()

    snapshot.assert_match(
        string_fixer.replace_quotes(input_code),
        output_file,
    )
