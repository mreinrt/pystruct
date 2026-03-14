# Changelog

## [1.2.0] - 2026-03-15

### Added
- New "Ignore Rules" button allowing users to configure file and directory exclusion patterns
- Editable ignore rules dialog using .gitignore-style glob patterns
- Built-in Python project .gitignore preset (covers venv, caches, build artifacts, IDE files, logs, etc.)

### Changed
- Tree generation now respects user-defined ignore patterns
- Improved filtering logic allowing both hidden-file filtering and pattern-based ignores simultaneously

## [1.1.0] - 2026-03-12

### Added
- New "Show Groups" checkbox option to display file/directory owner and group information
- New "Show Permissions" checkbox option to display file/directory permissions in ls -l format

### Changed
- Improved file/directory sorting: files now appear before directories at each level
