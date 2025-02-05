# Change Log

## [Unreleased]


## [0.5.0] - 2025-01-19

### Added

- Added ability to convert f-string with no placeholders into simple strings (F541)

### Fixed

- Fix target parent folder check when config root is `./`
- Fix default argument values overriding local config values
- Fix multiline triple strings being replaced with single quotes

## [0.4.1] - 2025-01-19

### Fixed

- Fix `AttributeError` when merging CLI args with local config

## [0.4.0] - 2024-06-27


### Added

- `--dry-run` CLI arg now has an inverse argument: `--no-dry-run`
- Ability to override preferred quote character via `quote_style` setting

### Changed

- CLI args will now override any `pyproject.toml` settings
- `prefer_least_escapes` now defaults to `True`

### Fixed

- Errors being thrown for non-strict glob syntaxes


## [0.3.0] - 2024-06-12

### Added

- `prefer_least_escapes` config option for preferring quote style deviations over additional escapes

### Fixed

- r-string contents being modified due to overzealous quote escaping

## [0.2.0] - 2024-05-05

### Added

- `include` config option for overriding `ignore`
- Support for populating the `ignore` config from `.gitignore` files
- Sensible default value for `ignore` config option
- Support for r-strings, rf-strings and even u-strings
- CLI option for setting `target_version`

### Fixed

- Insufficient checks for if a file was ignored/included
- Config files not loading correctly for deep directory trees

## [0.1.0] - 2024-04-28

### Added

- Support for f-strings
- `target_version` config option to adjust output compatibility with older Python versions

## [0.0.1] - 2024-04-23

- Initial release


[unreleased]: https://github.com/Crozzers/string-fixer/compare/lib/0.5.0...HEAD
[0.5.0]: https://github.com/Crozzers/string-fixer/compare/lib/0.4.1...lib/0.5.0
[0.4.1]: https://github.com/Crozzers/string-fixer/compare/lib/0.4.0...lib/0.4.1
[0.4.0]: https://github.com/Crozzers/string-fixer/compare/lib/0.3.0...lib/0.4.0
[0.3.0]: https://github.com/Crozzers/string-fixer/compare/lib/0.2.0...lib/0.3.0
[0.2.0]: https://github.com/Crozzers/string-fixer/compare/lib/0.1.0...lib/0.2.0
[0.1.0]: https://github.com/Crozzers/string-fixer/compare/lib/0.0.1...lib/0.1.0
[0.0.1]: https://github.com/Crozzers/string-fixer/releases/tag/lib/0.0.1
