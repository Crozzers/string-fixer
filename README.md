# String Fixer

Simple tool to replace "double quotes" with 'single quotes' in Python files.

There are many tools out there to lint and format Python code. The most popular formatter, Black,
[prefers double quotes to single quotes](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#strings).
Ruff is a bit more flexible, but doesn't format docstrings with single quotes
(it [lets you skip formatting them](https://github.com/astral-sh/ruff/issues/7615#issuecomment-1831179705) to preserve your own quotation style).

Neither project seems likely to add the option for entirely single-quoted code, so this tool can work as a post-processor to fix that.

## Usage

### CLI

```bash
# run against single file
python -m string-fixer --target my_file.py
# run against directory
python -m string-fixer --target lib/src/
# run against working dir
python -m string-fixer
```

### IDE Plugins

This project has an accompanying [VSCode extension](https://github.com/Crozzers/string-fixer/tree/main/extensions/vscode).
