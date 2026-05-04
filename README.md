# GTK Directory Tree Viewer (pystruct)

**pystruct** is a Python-based GTK3 application that allows you to visually browse and generate ASCII-style directory trees. Designed for system administrators, developers, and anyone who wants a clear textual representation of a file hierarchy.

---

## Features

### Core Functionality
- **Browse and select directories** via GTK3 file chooser.
- **ASCII directory tree** with `├──`, `└──`, and `│` connectors in the GUI.
- **File content preview** – click any file to view its contents in a bottom panel.
- **Copy selected file content** to clipboard.
- **Copy entire ASCII tree** to clipboard (respects collapsed/expanded state).
- **Configurable max depth** (1-10) to limit tree expansion.
- **Show/hide hidden files** (overrides ignore patterns).
- **Show permissions** (Unix-style `rwxr-xr-x`) and **show groups** (owner:group) on Linux/macOS.
- **Ignore rules editor** – edit built-in Python-centric patterns (`.venv/`, `__pycache__/`, etc.) via a dialog.

### Multi-Tab Management
- **Multiple tabs** – work with different directories simultaneously.
- **"+" button** to create new tabs with independent state and settings.
- **Close button (X)** on each tab (last tab cannot be closed).
- **Tab labels** display directory names (truncated to 10 characters with tooltips).
- **Active tab highlighting** with bold border using system theme colors.

### Cross-Platform Support
- **Runs on Linux, macOS, and Windows** with identical functionality.
- **Platform detection** automatically disables unsupported features (Permissions/Groups on Windows).
- **Theme-aware styling** respects system GTK themes on all platforms.

### User Interface
- **Full-width row highlighting** using your system's native GTK theme colors.
- **Resizable split view** – drag the divider to adjust tree vs. preview area size.
- **Refresh button** – reload the current tab's tree without changing settings.
- **About dialog** with project information, creator story, and donation addresses.
- **Status bar** with real-time feedback and error reporting.

---

## Requirements

- Python 3.6+
- PyGObject (GTK3)
- System GTK3 libraries

### Installing Dependencies

Use a virtual environment and install PyGObject:

    # Activate your virtual environment first
    pip install PyGObject

    # System packages (example for Ubuntu/Debian)
    sudo apt-get install gir1.2-gtk-3.0

    # Fedora
    sudo dnf install gtk3

    # Arch Linux
    sudo pacman -S gtk3

---

## Running the Application

    # Make sure you are in a virtual environment
    python pystruct.py

---

## Usage

1. **Select a directory**: Use the text entry or click **Browse**.
2. **Set options**:
   - Toggle **Hidden Files** to show/hide hidden files/directories
   - Toggle **Permissions** (Linux/macOS only)
   - Toggle **Groups** (Linux/macOS only)
   - Adjust **Max Depth** to limit tree expansion
3. **Generate tree**: Click **Generate Tree**.
4. **Copy tree**: Click **Copy Tree** to copy ASCII tree text.
5. **Copy file content**: Click any file, then click **Copy Selected File**.
6. **Refresh**: Click **Refresh** to reload the current tab's tree.

The status bar will provide feedback, including errors and success messages.

---

## Key Implementation Details

- **Gtk.TreeView with TreeStore** – Efficient tree rendering with native full-row highlighting and selection.
- **Gtk.Paned split view** – Resizable divider between directory tree (top) and file preview (bottom).
- **Custom browser-style tabs** – Traditional tab interface using Gtk.EventBox for independent click handling...
- **Gtk.Stack** – Manages tab content switching with smooth crossfade transitions.
- **ASCII pipe connectors** – Visual tree lines (`├──`, `└──`, `│`) are stored as prefixes in the TreeStore and combined with cell data functions.
- **Platform detection** – Automatically detects Linux, macOS, or Windows and disables unsupported features (Permissions/Groups on Windows).
- **Cross-platform hidden file detection** – Windows uses `GetFileAttributesW` API; macOS checks dot-files and BSD hidden flags; Linux uses standard dot-file detection.
- **Theme-aware CSS** – Uses GTK theme variables (`@theme_selected_bg_color`) instead of hardcoded colors, respecting system themes across all platforms.
- **Recursive tree generation** – Stops at `max_depth` and respects collapse/expand state for WYSIWYG copying.
- **Multi-encoding file preview** – Attempts UTF-8, Latin-1, and CP1252 fallbacks for text files; displays "[Binary file - cannot display content]" for binaries.
- **Gitignore-style ignore patterns** – Supports pattern matching (e.g., `*.pyc`, `__pycache__/`, `.venv/`) with an editable ignore rules dialog.
- **Clipboard integration** – Cross-platform clipboard support using `Gtk.Clipboard` for copying tree output and file contents.
- **Graceful error handling** – Permission errors show `[Permission Denied]` in the tree; file read errors display descriptive messages in the preview panel.

---

## Project Structure

    pystruct.py   # Main application script

- All logic is contained in a single Python file for portability.
- No external configuration files are required.

---

## Notes

- Tested on Linux systems with GTK3 support.
- Virtual environment recommended for dependency isolation.
- The app is designed for local file browsing; no network file access is implemented.
- Exception handling included for permission issues, missing directories, and clipboard failures.

---

## License

MIT License — free to use, modify, and distribute.

---

## Contact / Support

For issues or suggestions, please open an issue in the repository or contact the maintainer directly.

## About the Developer

Created by **Mike Reinert (BigSlimThic)** – a self-taught developer who built this tool despite facing extraordinary challenges, including homelessness and living without basic utilities. Every line of code was written against the odds. This project is dedicated to everyone fighting for a better life.

## Donate

Donate to BigSlimThic: Help fund his lifelong quest to buy an ergonomic chair, 
a better Wi-Fi router, and possibly a vacation somewhere that isn't just his imagination.

BTC: 3GtCgHhMP7NTxsdNjcDs7TUNSBK6EXoAzz

ETH: 0x5f1ed610a96c648478a775644c9244bf4e78631e