# Changelog

All notable changes to this project are documented in this file.

The format is based on https://keepachangelog.com/en/1.0.0/
and this project loosely follows https://semver.org/spec/v2.0.0.html.

---

## [3.0.0] - 2026-04-27

### Added
- Full-width row highlighting in the directory tree using native GTK theme colors.
- File content preview panel that displays the contents of a selected file.
- Copy selected file content button to copy file contents directly to the clipboard.
- Refactored ASCII pipe connectors (`├──`, `└──`, `│`) in the GUI tree view for better visual hierarchy.
- Persistence of the horizontal divider position for improved layout control.
- Proper spin button increment/decrement for the Max Depth control (step increment of 1).

### Changed
- Refactored the tree display from `Gtk.TextView` to `Gtk.TreeView` for native selection, full-row highlighting, and improved performance.
- Updated UI layout using `Gtk.Paned` to separate directory tree (top) and file preview (bottom).
- Reorganized source code with improved structure, naming, and added docstrings.
- Disabled TreeView indentation to rely entirely on ASCII prefixes for alignment.

### Fixed
- Fixed spin button not responding to `+` / `-` controls for Max Depth.
- Fixed ASCII tree alignment issues in clipboard output.
- Resolved GTK warning caused by adding a widget to a container multiple times.
- Handled `UnicodeDecodeError` when previewing binary files by displaying a message.
- Corrected ASCII pipe connector alignment.

### Removed
- Removed deprecated per-line text-tag highlighting in favor of native TreeView selection.

---

## [1.2.0] - 2026-03-15

### Added
- New "Ignore Rules" button allowing users to configure file and directory exclusion patterns.
- Editable ignore rules dialog using `.gitignore`-style glob patterns.
- Built-in Python project `.gitignore` preset (venv, caches, build artifacts, IDE files, logs, etc.).

### Changed
- Tree generation now respects user-defined ignore patterns.
- Improved filtering logic allowing both hidden-file filtering and pattern-based ignores simultaneously.

---

## [1.1.0] - 2026-03-12

### Added
- New "Show Groups" checkbox option to display file/directory owner and group information.
- New "Show Permissions" checkbox option to display file/directory permissions in `ls -l` format.

### Changed
- Improved file/directory sorting: files now appear before directories at each level.

---

## [1.0.0] - 2026-02-22

### Added
- Initial release.
- GTK3-based directory browser.
- ASCII tree generation and clipboard copy support.
- Basic error handling for filesystem access.
