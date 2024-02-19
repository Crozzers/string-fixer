import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, TypedDict

import libcst as cst
import tomli
from libcst import parse_module


class Config(TypedDict):
    target: Path
    dry_run: bool
    output: Optional[str]


class DocstringDoubleToSingle(cst.CSTTransformer):
    def _escape_quote(self, match: re.Match) -> str:
        '''
        Handle quotes, check if they're escaped, escape them if not
        '''
        escapes, quote = match.groups()
        if len(escapes) % 2 == 1:
            # quote is escaped. Do nothing
            return escapes + quote
        # quote is not escaped. Escape it
        return escapes + (('\\' + quote[0]) * len(quote))

    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> cst.SimpleString:
        if '"' not in original_node.quote:
            return original_node

        # remove start and end quotes
        text = updated_node.value[len(updated_node.quote) : -len(updated_node.quote)]
        quote_len = len(updated_node.quote)

        text = re.sub(
            r'(\\*)(["\']{%d,})' % quote_len,
            self._escape_quote,
            text,
            flags=re.MULTILINE,
        )

        new_quote = '\'' * len(updated_node.quote)
        return updated_node.with_changes(value=f'{new_quote}{text}{new_quote}')


def replace_docstring_double_with_single_quotes(code: str) -> str:
    module = parse_module(code)
    transformer = DocstringDoubleToSingle()
    modified_module = module.visit(transformer)
    return modified_module.code


def load_config(cli_overrides: argparse.Namespace) -> Config:
    '''
    Loads the program config from the following places (low -> high priority):
    1. pyproject.toml in current working directory
    2. pyproject.toml in target directory
    3. CLI args
    '''
    base_config: Config = {
        'target': Path('./'),
        'dry_run': False,
        'output': None
    }
    # check for config options in cwd
    if os.path.isfile('./pyproject.toml'):
        with open('./pyproject.toml', 'rb') as f:
            toml = tomli.load(f)
            if 'tool' in toml and 'string-fixer' in toml['tool']:
                base_config.update(toml['tool']['string-fixer'])
    # check for config options in target dir
    target_dir = Path(base_config['target'])
    if not target_dir.is_dir():
        target_dir = Path(base_config['target']).parent

    if os.path.isfile(target_dir / 'pyproject.toml'):
        with open(target_dir / 'pyproject.toml', 'rb') as f:
            toml = tomli.load(f)
            if 'tool' in toml and 'string-fixer' in toml['tool']:
                base_config.update(toml['tool']['string-fixer'])

    for key, value in base_config.items():
        if getattr(cli_overrides, key, None) is None:
            continue
        base_config[key] = Path(value) if key == 'target' else value
    return base_config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'string-fixer',
        description='Simple tool to replace "double quotes" with \'single quotes\' in Python files',
    )
    parser.add_argument(
        '-t',
        '--target',
        type=str,
        help='File or directory of Python files to format. Only .py files will be included. (default: ./)',
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help='Show planned changes but don\'t modify any files',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Instead of modifying files in-place, write a copy to this directory',
    )
    args = parser.parse_args()

    config = load_config(args)

    collected_targets: List[Path] = []
    parent: Path

    if os.path.isdir(config['target']):
        parent = Path(config['target'])
        for path, _, files in os.walk(config['target']):
            path = Path(path)
            for file in files:
                if not file.endswith('.py'):
                    continue
                collected_targets.append(path / file)
    else:
        parent = Path(config['target']).parent
        if config['target'].suffix == '.py':
            collected_targets.append(Path(config['target']))

    collected_targets = [i for i in collected_targets if i.exists()]

    if not collected_targets:
        print('No valid .py files found')
        sys.exit(1)

    for file in collected_targets:
        print('Processing:', file)
        with open(file) as f:
            code = f.read()

        modified = replace_docstring_double_with_single_quotes(code)

        if config['dry_run']:
            print('---')
            print(modified)
            print('---')
        else:
            if config['output']:
                file = Path(config['output']).joinpath(*file.parts[len(parent.parts) :])
                print('Writing to:', file)
                os.makedirs(file.parent, exist_ok=True)
            with open(file, 'w') as f:
                f.write(modified)
