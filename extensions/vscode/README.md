# string-fixer VSCode Extension

This folder hosts the [`string-fixer` VSCode extension](https://marketplace.visualstudio.com/items?itemName=Crozzers.string-fixer), which just provides an easy way to run `string-fixer` through your IDE.

## Features

- Run string-fixer against your workspace using the `string-fixer: Run` command in the command pallette (`CTRL`+`Shift`+`p`).
- Use string-fixer as a Python formatter

## Requirements

`ms-python.python` extension is required.
Your selected interpreter also needs to have `string-fixer` installed as a module. You can install it by running `python -m pip install string-fixer`.

## Extension Settings

This extension contributes the following settings:

* `string-fixer.folder`
  - The folder containing the `pyproject.toml` file used to configure the library. Defaults to the current workspace folder.
  - This should be relative to the root of the workspace folder.
* `string-fixer.preFormatter`
  - Run another formatting extension against the code before running string-fixer. Ruff and Black are supported. Defaults to doing nothing.
