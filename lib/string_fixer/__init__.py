import os
import re
from functools import cache
from pathlib import Path
from typing import List, Optional, TypedDict, Union

import libcst as cst
import tomli
from libcst import parse_module


class Config(TypedDict):
    target: Path
    dry_run: bool
    output: Optional[Path]
    ignore: Optional[List[Path]]
    extends: Optional[Path]


DEFAULT_CONFIG: Config = {
    'target': Path('./'),
    'dry_run': False,
    'output': None,
    'ignore': None,
    'extends': None,
}


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


def load_config_from_file(file: Path) -> Union[Config, None]:
    if not file.exists():
        return

    with open(file, 'rb') as f:
        toml = tomli.load(f)
    if 'tool' not in toml or 'string-fixer' not in toml['tool']:
        return

    config = toml['tool']['string-fixer']

    if extends := config.get('extends', None):
        extends = (file.parent / extends).resolve()
        config['extends'] = extends
        extends = extends.parent if extends.is_file() else extends

        config = {**load_config_from_dir(extends), **config}

    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)

    if target := config.get('target'):
        config['target'] = (file.parent / target).resolve()

    if output := config.get('output'):
        config['output'] = (file.parent / output).resolve()

    if config.get('ignore', []):
        ignore = []
        for pattern in config['ignore']:
            ignore.extend(file.parent.glob(pattern))
        config['ignore'] = ignore

    return config


@cache
def load_config_from_dir(path: Path, limit: Optional[Path] = None) -> Config:
    '''
    Loads closest config file to `path` in directory tree, up to `limit`.

    Args:
        path: The dir to start from when loading config files
        limit: Don't go higher than this dir

    Returns:
        Config from closest config file, or default config if N/A
    '''
    path = path.parent if path.is_file() else path
    file = path / 'pyproject.toml'
    if config := load_config_from_file(file):
        return config
    if limit and path != limit:
        return load_config_from_dir(path.parent)
    return DEFAULT_CONFIG


def process_file(file: Path, config: Config, base_dir: Optional[Path] = None):
    assert file.is_file()
    base_dir = base_dir or file.parent
    print('Processing:', file)
    print('Conf', config)
    with open(file) as f:
        code = f.read()

    modified = replace_docstring_double_with_single_quotes(code)

    if config.get('dry_run', False):
        print('---')
        print(modified)
        print('---')
    else:
        if config['output']:
            file = Path(config['output']).joinpath(*file.parts[len(base_dir.parts) :])
            print('Writing to:', file)
            os.makedirs(file.parent, exist_ok=True)
        with open(file, 'w') as f:
            f.write(modified)
