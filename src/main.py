from typing import List
import libcst as cst
from libcst import parse_module
import sys
import os
from pathlib import Path
import argparse
import re


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

        new_quote = "'" * len(updated_node.quote)
        return updated_node.with_changes(value=f'{new_quote}{text}{new_quote}')


def replace_docstring_double_with_single_quotes(code: str) -> str:
    module = parse_module(code)
    transformer = DocstringDoubleToSingle()
    modified_module = module.visit(transformer)
    return modified_module.code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'string-fixer',
        description='Simple tool to replace "double quotes" with \'single quotes\' in Python files',
    )
    parser.add_argument(
        'target',
        type=str,
        help='File or directory of Python files to format. Only .py files will be included',
    )
    parser.add_argument(
        '-d',
        '--dry-run',
        action='store_true',
        help="Show planned changes but don't modify any files",
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Instead of modifying files in-place, write a copy to this directory',
    )
    args = parser.parse_args()

    collected_targets: List[Path] = []
    parent: Path

    if os.path.isdir(args.target):
        parent = Path(args.target)
        for path, _, files in os.walk(args.target):
            path = Path(path)
            for file in files:
                if not file.endswith('.py'):
                    continue
                collected_targets.append(path / file)
    else:
        parent = Path(args.target).parent
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

        modified = replace_docstring_double_with_single_quotes(code)

        if args.dry_run:
            print('---')
            print(modified)
            print('---')
        else:
            if args.output:
                file = Path(args.output).joinpath(*file.parts[len(parent.parts) :])
                print('Writing to:', file)
                os.makedirs(file.parent, exist_ok=True)
            with open(file, 'w') as f:
                f.write(modified)
