# Changelog

All continued notable changes to the **pystruct** project will be documented in this file.

## [4.0.0] - 2026-05-02

### Added
- **Full cross-platform compatibility** with automatic platform detection system supporting Linux, macOS, and Windows.
- **Multi-tab support** with traditional browser-style tabs for managing multiple directory views simultaneously.
- **About dialog** featuring project information, creator story, and cryptocurrency donation addresses (BTC/ETH) with copy functionality.
- **Refresh button** to reload the current tab's directory tree without changing settings.

### Changed
- **Platform-specific features** (Permissions/Groups) are automatically disabled on Windows with informative tooltips.
- **Cross-platform hidden file detection** using appropriate APIs for each operating system (Windows API, macOS BSD flags, Linux dot-files).
- **Theme-aware tab styling** using CSS that respects system GTK themes across all platforms.
- **Active tab visual feedback** with bold border using system theme colors (no hardcoded colors).

## [3.0.0] - 2026-04-27

### Added
- **File content preview panel** that displays the contents of a selected file.
- **Copy selected file content** button to copy file contents directly to the clipboard.
- **Full-width row highlighting** in the directory tree using native GTK theme colors.
- **Refactored ASCII pipe connectors** (`├──`, `└──`, `│`) in the GUI tree view for better visual hierarchy.

### Changed
- Refactored the tree display from `Gtk.TextView` to `Gtk.TreeView` for native selection, full‑row highlighting, and better performance.
- Improved overall UI layout by splitting the main area into a directory tree (top) and file preview (bottom).

### Fixed
- Fixed alignment problems in the generated ASCII tree when copying to the clipboard.
- Handled `UnicodeDecodeError` gracefully when trying to preview binary files.

## [2.0.0] - 2026-04-20

### Added
- **Show Hidden Files**, **Show Permissions**, and **Show Groups** options.
- **Gitignore-style ignore rules editor** for customizing ignore patterns.
- **Max Depth** spin box to limit tree expansion.

### Changed
- Updated default ignore patterns to be more Python-focused (`.venv/`, `__pycache__/`, etc.).
- Switched from `os.listdir()` to `pathlib.Path.iterdir()` for better cross-platform compatibility.

## [1.0.0] - 2026-04-15

### Added
- Initial release with GTK3 directory browser and ASCII tree generation.
- Browse and select directories using file chooser.
- Copy generated tree to clipboard.