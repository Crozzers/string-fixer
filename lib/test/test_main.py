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
    'f_strings_py311': {'python': '<=3.11'},
    'double_quote_style': {'quote_style': 'double'},
    'least_escapes_false': {'prefer_least_escapes': False}
}

@pytest.mark.parametrize('case', cases)
def test_snapshots(snapshot, case: str):
    target = '3.8'
    options = {}
    if case[:-3] in special_cases:
        special = special_cases[case[:-3]]
        if 'python' in special:
            specifier = specifiers.Specifier(special['python'])
            target = special['python'].strip('<=>!')
            current = version.Version(platform.python_version())
            if not specifier.contains(current):
                pytest.skip(
                    f'skipped {case} due to python version'
                    f' (requires {specifier}, has {current})'
                )
        if 'prefer_least_escapes' in special:
            options['prefer_least_escapes'] = special['prefer_least_escapes']
        if 'quote_style' in special:
            options['quote_style'] = special['quote_style']

    snapshot.snapshot_dir = str(SNAPSHOT_DIR)
    input_file = str(CASES_DIR / case)
    output_file = str(SNAPSHOT_DIR / case)

    with open(input_file) as f:
        input_code = f.read()

    snapshot.assert_match(
        string_fixer.replace_quotes(input_code, target_python=target, **options),
        output_file,
    )


@pytest.mark.parametrize('file,ignore,include,result', [
    ('./test.py', [], [], False),
    ('./test.py', ['./test.py'], [], True),
    ('./test.py', ['./test.py'], ['./test.py'], False),
    ('./test.py', [], ['./test.py'], False),
    ('./folder/test2.py', ['./folder'], ['./folder/test.py'], True),
    ('./folder/test.py', ['./folder'], ['./folder/test.py'], False),
])
def test_file_is_ignored(file, ignore, include, result):
    assert string_fixer.file_is_ignored(
        Path(file),
        [Path(i) for i in ignore],
        [Path(i) for i in include]
    ) is result
