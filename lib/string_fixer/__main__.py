import argparse
import os
import sys
from pathlib import Path

from . import file_is_ignored, process_file
from ._version import __version__
from .config import load_config_from_dir, merge_with_cli_args

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
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        action=argparse.BooleanOptionalAction,
        help="Show planned changes but don't modify any files",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Instead of modifying files in-place, write a copy to this directory',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '-c',
        '--config-root',
        type=str,
        help='Override base directory to load configs from',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--target-version',
        type=str,
        help='Python version to target for compatibility',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--prefer-least-escapes',
        action=argparse.BooleanOptionalAction,
        help='Try to produce strings with the least number of escapes, even if that means deviating from the quote style',
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--quote-style',
        help='Change the preferred quote style between single (default) and double quotes',
        choices=['single', 'double'],
        default=argparse.SUPPRESS
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Print version info',
        default=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if 'version' in args and args.version:
        print(__version__)
        sys.exit(0)

    config = merge_with_cli_args(load_config_from_dir(Path('./')), args)

    target = Path(config['target'])
    if 'config_root' in args and args.config_root:
        config_root = Path(args.config_root)
        assert config_root.exists(), 'config root must exist'
        assert (
            config_root in target.parents
        ), 'config root must be a parent of the target'
    else:
        config_root = target

    assert target.exists(), 'target must exist'

    if target.is_file():
        process_file(
            target,
            (
                config
                if 'config_root' not in args
                else merge_with_cli_args(
                    load_config_from_dir(target, limit=config_root), args
                )
            ),
        )
    else:
        for root, _, files in os.walk(target):
            root = Path(root)
            config = merge_with_cli_args(
                load_config_from_dir(root, limit=config_root), args
            )
            if file_is_ignored(root, config['ignore'], config['include']):
                continue
            for file in files:
                file = root / file
                if not file.suffix == '.py':
                    continue
                if file_is_ignored(file, config['ignore'], config['include']):
                    continue
                process_file(file, config, base_dir=target)
