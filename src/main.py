from typing import List
import libcst as cst
from libcst import parse_module
import sys
import os
from pathlib import Path
import argparse


class DocstringSingleToDouble(cst.CSTTransformer):
    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString) -> cst.SimpleString:
        return original_node.with_changes(value=original_node.value.replace('"', "'"))


def replace_docstring_single_with_double_quotes(code: str) -> str:
    module = parse_module(code)
    transformer = DocstringSingleToDouble()
    modified_module = module.visit(transformer)
    return modified_module.code


if __name__ == '__main__':
    parser = argparse.ArgumentParser('string-fixer', description='Simple tool to replace "double quotes" with \'single quotes\' in Python files.')
    parser.add_argument('target', type=str, help='File or directory of Python files to format. Only .py files will be included')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Show planned changes but don\'t modify any files.')
    args = parser.parse_args()

    collected_targets: List[Path] = []

    if os.path.isdir(args.target):
        for path, _, files in os.walk(args.target):
            path = Path(path)
            for file in files:
                if not file.endswith('.py'):
                    continue
                collected_targets.append(path / file)
    else:
        if args.target.endswith('.py'):
            collected_targets.append(Path(args.target))

    collected_targets = [i for i in collected_targets if i.exists()]

    if not collected_targets:
        print('No valid .py files found')
        sys.exit(1)

    for file in collected_targets:
        print('Processing:', file)
        with open(file) as f:
            code = f.read()

        modified = replace_docstring_single_with_double_quotes(code)

        if args.dry_run:
            print('---')
            print(modified)
            print('---')
        else:
            with open(file, 'w') as f:
                f.write(modified)
