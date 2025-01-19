import argparse
import glob as _glob
import os
import sys
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional, TypedDict, Union, cast

import tomli


def glob(pattern: str, root_dir: Path):
    return (
        root_dir / Path(i)
        for i in _glob.glob(pattern, root_dir=root_dir, recursive=True)
    )


class Config(TypedDict):
    target: Path
    dry_run: bool
    output: Optional[Path]
    ignore: Optional[List[Path]]
    include: Optional[List[Path]]
    extends: Optional[Path]
    target_version: Optional[str]
    prefer_least_escapes: bool
    quote_style: Optional[Literal['single', 'double']]


class UnparsedConfig(Config, TypedDict):
    ignore: Optional[Union[List[Path], List[str]]]
    include: Optional[Union[List[Path], List[str]]]


DEFAULT_CONFIG: UnparsedConfig = {
    'target': Path('./'),
    'dry_run': False,
    'output': None,
    'ignore': [
        './**/.*',
        './**/site-packages',
        './**/node_modules',
        './**/build',
        './**/dist',
        './**/__pycache__',
        './**/venv',
    ],
    'include': None,
    'extends': None,
    'target_version': f'{sys.version_info.major}.{sys.version_info.minor}',
    'prefer_least_escapes': True,
    'quote_style': 'single'
}


def parse_config(config: UnparsedConfig, file: Path) -> Config:
    config = deepcopy(config)

    if extends := config.get('extends', None):
        extends = (file.parent / extends).resolve()
        config['extends'] = extends
        extends = extends.parent if extends.is_file() else extends

        config = {**load_config_from_dir(extends), **config}

    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)  # type: ignore

    if target := config.get('target'):
        config['target'] = (file.parent / target).resolve()

    if output := config.get('output'):
        config['output'] = (file.parent / output).resolve()

    if 'ignore' in config and config['ignore']:
        ignore = set()

        # populate using config
        for pattern in config['ignore'] + (DEFAULT_CONFIG['ignore'] or []):
            if isinstance(pattern, Path):
                ignore.add(pattern)
            else:
                # use glob module rather than pathlib glob because syntax is much more lenient
                ignore.update(glob(pattern, file.parent))

        # populate from local .gitignore
        if (git_ignore := (file.parent / '.gitignore')).exists():
            with open(git_ignore) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    try:
                        ignore.update(glob(line, file.parent))
                    except ValueError as e:
                        raise ValueError(
                            f'error when parsing glob from gitignore: {line!r}'
                            f', file: {git_ignore.absolute().relative_to(os.getcwd())}'
                        ) from e

        config['ignore'] = list(
            {i for i in ignore if all(p not in ignore for p in i.parents)}
        )

    if 'include' in config and config['include']:
        include = []
        for pattern in config['include']:
            if isinstance(pattern, Path):
                include.append(pattern)
            else:
                include.extend(glob(pattern, file.parent))
        config['include'] = include

    if target_version := config.get('target_version', None):
        if not isinstance(target_version, str):
            raise TypeError('target_version must be string')

    return cast(Config, config)


def load_config_from_file(file: Path) -> Union[Config, None]:
    if not file.exists():
        return

    with open(file, 'rb') as f:
        toml = tomli.load(f)
    if 'tool' not in toml or 'string-fixer' not in toml['tool']:
        return

    config = toml['tool']['string-fixer']

    return parse_config(config, file)


@lru_cache
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
        return load_config_from_dir(path.parent, limit)
    return parse_config(DEFAULT_CONFIG, file)


def merge_with_cli_args(config: Config, args: argparse.Namespace) -> Config:
    # parse args relative to cwd so that any paths get fully expanded
    cli_config = parse_config(
        cast(UnparsedConfig, vars(args)), Path.cwd() / 'pyproject.toml'
    )
    for key, value in cli_config.items():
        if key not in DEFAULT_CONFIG:
            continue

        if key == 'include' or key == 'ignore':
            if not value:
                continue
            if not config[key]:
                config[key] = []
            config[key].extend(value)  # type: ignore
        elif value:
            config[key] = value

    return config
