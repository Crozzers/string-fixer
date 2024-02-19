# String Fixer

Simple tool to replace "double quotes" with 'single quotes' in Python files.

There are many tools out there to lint and format Python code. The most popular formatter, Black,
[prefers double quotes to single quotes](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#strings).
Ruff is a bit more flexible, but doesn't format docstrings with single quotes
(it [lets you skip formatting them](https://github.com/astral-sh/ruff/issues/7615#issuecomment-1831179705) to preserve your own quotation style).

Neither project seems likely to add the option for entirely single-quoted code, so this tool can work as a post-processor to fix that.

## Usage

```bash
# run against single file
python src/main.py --target my_file.py
# run against directory
python src/main.py --target src/
# run against working dir
python src/main.py
```


## Planned features

- PyPI package
- Smarter string replacement (not just proof-of-concept `str.replace(...)`)
- Controls over what types of string get replaced
    - Docstrings
    - Multi-line string literals
    - Single line string literals
- Configuration support via `pyproject.toml`
