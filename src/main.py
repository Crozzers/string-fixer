from typing import List
import libcst as cst
from libcst import parse_module
import sys
import os
from pathlib import Path


class DocstringSingleToDouble(cst.CSTTransformer):
    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString) -> cst.SimpleString:
        return original_node.with_changes(value=original_node.value.replace('"', "'"))


def replace_docstring_single_with_double_quotes(code: str) -> str:
    module = parse_module(code)
    transformer = DocstringSingleToDouble()
    modified_module = module.visit(transformer)
    return modified_module.code


if __name__ == '__main__':
    target = sys.argv[1]

    collected_targets: List[Path] = []

    if os.path.isdir(target):
        for path, _, files in os.walk(target):
            path = Path(path)
            for file in files:
                if not file.endswith('.py'):
                    continue
                collected_targets.append(path / file)
    else:
        if target.endswith('.py'):
            collected_targets.append(Path(target))

    collected_targets = [i for i in collected_targets if i.exists()]

    if not collected_targets:
        print('No valid .py files found')
        sys.exit(1)

    for file in collected_targets:
        print('Processing:', file)
        with open(file) as f:
            code = f.read()

        modified = replace_docstring_single_with_double_quotes(code)

        with open(file, 'w') as f:
            f.write(modified)
