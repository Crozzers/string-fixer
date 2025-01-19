import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Literal, Optional

import libcst as cst
from libcst import FormattedString, parse_module

from .config import Config


def version_lt(a: str, b: str):
    '''
    Minimal version check for python versions

    Returns:
        a < b
    '''
    return int(a.replace('.', '')) < int(b.replace('.', ''))


class QuoteTransformer(cst.CSTTransformer):
    def __init__(self, target_python: Optional[str] = None, prefer_least_escapes = True, quote_style: Literal['single', 'double'] = 'single'):
        '''
        Args:
            target_python: which version of python to target. Defaults to current version
        '''
        self._target_python = target_python or f'{sys.version_info.major}.{sys.version_info.minor}'
        self.prefer_least_escapes = prefer_least_escapes
        self.quote_style = quote_style

    def _escape_quote_sub(self, match: re.Match) -> str:
        '''
        Handle quotes, check if they're escaped, escape them if not
        '''
        escapes, quote = match.groups()
        if len(escapes) % 2 == 1:
            # quote is escaped. Do nothing
            return escapes + quote
        # quote is not escaped. Escape it
        return escapes + (('\\' + quote[0]) * len(quote))

    def _escape_quotes(self, text: str, quote_re: str, quote_len: int):
        return re.sub(
            r'(\\*)([%s]{%d,})' % (quote_re, quote_len),
            self._escape_quote_sub,
            text,
            flags=re.MULTILINE,
        )

    def _unescape_quote_sub(self, match: re.Match) -> str:
        escapes, quote = match.groups()
        if not quote:
            return escapes + quote
        if len(escapes) % 2 == 0:
            # quote is unescaped. Do nothing
            return escapes + quote
        # quote is escaped. Unescape it
        return escapes[:-1] + quote

    def _unescape_quotes(self, text: str, quote_re: str, quote_len: int):
        return re.sub(
            r'(\\*)([%s]{1,%d})' % (quote_re, quote_len),
            self._unescape_quote_sub,
            text,
            flags=re.MULTILINE,
        )

    def _count_escapes(self, text: str):
        return len([i for i in re.findall(r'(\\*)["\']', text) if len(i) % 2 != 0])

    def _get_quote(self):
        return ("'", '"') if self.quote_style == 'single' else ('"', "'")

    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString,
        quote_override: Optional[str] = None
    ) -> cst.SimpleString:
        '''
        Args:
            original_node: the node being visited
            updated_node: a deep clone of `original_node` where transformations can be applied
            quote_override: override what kind of quote we are assigning to the string. Useful for
                nested f-strings where quote re-use is not allowed
        '''
        quote = quote_override or self._get_quote()[0]
        anti = '\'' if quote[0] == '"' else '"'
        prefix = original_node.prefix
        quote_len = max(len(quote), len(updated_node.quote))

        if anti not in original_node.quote:
            return updated_node

        # remove start and end quotes
        text = updated_node.value[len(updated_node.quote) + len(prefix) : -len(updated_node.quote)]
        new_quote = quote[0] * quote_len

        if 'r' in prefix :
            if quote in text:
                # we can't add/remove escapes from rstrings
                return original_node
            # if the target quote isn't in the rstring then we can do a simple quote swap
        else:
            # unescape as many internal quotes as possible
            text = orig_text = self._unescape_quotes(text, quote + anti, quote_len)
            # escape the quotes we want to wrap the string with
            text = self._escape_quotes(text, quote, quote_len)

            if self.prefer_least_escapes:
                # escape the current quotes wrapping the string
                old_style = self._escape_quotes(orig_text, anti, quote_len)

                # if changing quote style would result in more escapes
                if self._count_escapes(text) > self._count_escapes(old_style):
                    # set everything back to the old style
                    text = old_style
                    new_quote = anti[0] * quote_len

        return updated_node.with_changes(value=f'{prefix}{new_quote}{text}{new_quote}')

    def leave_FormattedString(
        self, original_node: cst.FormattedString, updated_node: cst.FormattedString,
        depth = 1, meta: Optional[Dict[str, int]] = None
    ) -> cst.BaseExpression:
        '''
        Args:
            original_node: the node being visited
            updated_node: a deep clone of `original_node` where transformations can be applied
            depth: current recursion depth
            meta: dict used to keep track of info across recursions (eg: max recursion depth)
                without corrupting the return signature
        '''
        meta = meta if meta is not None else {}
        meta['max_depth'] = max(meta.get('max_depth', 1), depth)

        def get_quote(depth):
            '''Get appropriate quote given the f-string nest depth'''
            quote, anti = self._get_quote()
            if meta['max_depth'] <= 2:
                quote_order = [quote, anti]
            elif meta['max_depth'] == 3:
                quote_order = [quote * 3, quote, anti]
            else:
                quote_order = [quote * 3, anti * 3, quote, anti]

            return quote_order[depth - 1] if version_lt(self._target_python, '3.12') else quote

        if version_lt(self._target_python, '3.12') and depth > 4:
            # quit after 4 levels on <=3.11 because you can't reuse quotes in f-string expressions.
            # since there are only 4 kinds of quotes (single, double and triple versions of each)
            # there can only be 4 levels (see also point 3 in https://peps.python.org/pep-0701/#rationale)
            return super().leave_FormattedString(original_node, updated_node)

        new_parts = []
        for part in original_node.parts:
            # it would be better to split this block into the corresponding `leave_<NodeType>`.
            # Each nested fstring gets visited separately before the top-level one, meaning we will
            # traverse it multiple times. However, we may lose the depth tracking info that way.
            # Performance not critical atm since I haven't tested a large file. Something to look into
            if isinstance(part, cst.FormattedStringText):
                value = re.sub(
                    r'(\\*)(["\']{%d,})' % 1,
                    self._escape_quote_sub,
                    part.value,
                    flags=re.MULTILINE,
                )
                new_parts.append(part.with_changes(value=value))
            elif isinstance(part, cst.FormattedStringExpression):
                expression = part.expression
                if isinstance(expression, FormattedString):
                    new_parts.append(
                        part.with_changes(
                            expression=self.leave_FormattedString(
                                expression, expression.deep_clone(), depth + 1, meta
                            )
                        )
                    )
                elif isinstance(expression, cst.Subscript):
                    new_slices = []
                    for slice in expression.slice:
                        if not isinstance(slice.slice, cst.Index):
                            new_slices.append(slice)
                            continue

                        value = slice.slice.value
                        new_value = value
                        if isinstance(value, cst.SimpleString):
                            # bump max_depth because simple string is another layer
                            meta['max_depth'] = max(meta.get('max_depth', 1), depth + 1)
                            new_value = self.leave_SimpleString(
                                value, value.deep_clone(), get_quote(depth + 1)
                            )
                        elif isinstance(value, FormattedString):
                            new_value = self.leave_FormattedString(
                                value, value.deep_clone(), depth + 1, meta
                            )

                        new_slices.append(slice.with_changes(
                            slice=slice.slice.with_changes(
                                value=new_value
                            )
                        ))
                    new_parts.append(
                        part.with_changes(
                            expression=expression.with_changes(slice=new_slices)
                        )
                    )
                elif isinstance(expression, cst.SimpleString):
                    # bump max_depth because simple string is another layer
                    meta['max_depth'] = max(meta.get('max_depth', 1), depth + 1)
                    new_parts.append(
                        part.with_changes(
                            expression=self.leave_SimpleString(
                                expression, expression.deep_clone(), get_quote(depth + 1)
                            )
                        )
                    )
                else:
                    new_parts.append(part)
            else:
                new_parts.append(part)

        quote = get_quote(depth)
        return updated_node.with_changes(parts=new_parts, start=f'{original_node.prefix}{quote}', end=quote)


def replace_quotes(code: str, **kwargs) -> str:
    module = parse_module(code)
    transformer = QuoteTransformer(**kwargs)
    modified_module = module.visit(transformer)
    return modified_module.code


def process_file(file: Path, config: Config, base_dir: Optional[Path] = None):
    assert file.is_file()
    base_dir = base_dir or file.parent
    print('Processing:', file)
    with open(file) as f:
        code = f.read()

    modified = replace_quotes(code, target_python=config['target_version'], prefer_least_escapes=config['prefer_least_escapes'], quote_style=config['quote_style'])

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


def file_is_ignored(file: Path, ignore: Optional[List[Path]], include: Optional[List[Path]]):
    file = file.absolute()
    is_ignored = False
    is_included = False

    if ignore:
        for ignore_path in ignore:
            ignore_path = ignore_path.absolute()
            if ignore_path == file or ignore_path in file.parents:
                is_ignored = True
                break

    if include:
        for include_path in include:
            include_path = include_path.absolute()
            if include_path == file or include_path in file.parents:
                is_included = True
                break

    return is_ignored and not is_included
