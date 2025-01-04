# lib-rust

This is an experimental re-write of the library in Rust.

#### Why?

Currently, installing the VSCode extension requires the user to also manually install `string-fixer` in their venv. The way to smooth this over would be to bundle the library with the extension, but you can't run python code from a zip/wheel file without installing it.

The other way to handle this is to bundle an exe with the extension.

#### Why Rust?

Allows us to compile an exe that executes on most platforms. Fast, performant, memory safe. Also just a fun project