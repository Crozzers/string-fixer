import os
import sys
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, TypedDict, Union, cast

import tomli


class Config(TypedDict):
    target: Path
    dry_run: bool
    output: Optional[Path]
    ignore: Optional[List[Path]]
    include: Optional[List[Path]]
    extends: Optional[Path]
    target_version: Optional[str]


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
        './**/venv'
    ],
    'include': None,
    'extends': None,
    'target_version': f'{sys.version_info.major}.{sys.version_info.minor}'
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
                ignore.update(file.parent.glob(pattern))

        # populate from local .gitignore
        if (git_ignore := (file.parent / '.gitignore')).exists():
            with open(git_ignore) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    try:
                        ignore.update(file.parent.glob(line))
                    except ValueError as e:
                        raise ValueError(
                            f'error when parsing glob from gitignore: {line!r}'
                            f', file: {git_ignore.absolute().relative_to(os.getcwd())}'
                        ) from e

        config['ignore'] = list({i for i in ignore if all(p not in ignore for p in i.parents)})

    if 'include' in config and config['include']:
        include = []
        for pattern in config['include']:
            if isinstance(pattern, Path):
                include.append(pattern)
            else:
                include.extend(file.parent.glob(pattern))
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
