# GTK Directory Tree Viewer (pystruct)

**pystruct** is a cross-platform Python GTK3 application for generating, viewing, and copying ASCII-style directory trees. It features multi-tab support, file content preview, full-width row highlighting, and a classic tree view with `├──`, `└──`, and `│` connectors – perfect for developers, sysadmins, and anyone who needs a quick textual overview of a file hierarchy.

![Main widget with options](media/screenshot.png)

---

## Features

### Core Functionality
- **Browse and select directories** via GTK3 file chooser.
- **ASCII directory tree** with `├──`, `└──`, and `│` connectors in the GUI.
- **File content preview** – click any file to view its contents in a bottom panel.
- **Copy selected file content** to clipboard.
- **Copy entire ASCII tree** to clipboard.
- **Configurable max depth** (1-10) to limit tree expansion.
- **Show/hide hidden files** (overrides ignore patterns).
- **Show permissions** (Unix-style `rwxr-xr-x`) and **show groups** (owner:group).
- **Ignore rules editor** – edit built-in Python-centric patterns (`.venv/`, `__pycache__/`, etc.) via a dialog.

### Multi-Tab Management
- **Multiple tabs** – work with different directories simultaneously.
- **"+" button** to create new tabs with independent state and settings.
- **Close button (X)** on each tab (last tab cannot be closed).
- **Tab labels** display directory names (truncated to 10 characters with tooltips).
- **Active tab highlighting** with bold border using system theme colors.

### Cross-Platform Support
- **Runs on Linux, macOS, and Windows** with identical functionality.
- **Platform detection system** automatically enables/disables platform-specific features.
- **Cross-platform hidden file detection**:
  - Windows: Uses native `GetFileAttributesW` API
  - macOS: Checks dot-files and BSD hidden flags
  - Linux: Standard dot-file detection
- **Theme-aware styling** respects system GTK themes on all platforms.
- **Cross-platform clipboard** operations work consistently.

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

### Platform-Specific Installation

**Linux (Debian/Ubuntu):**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
pip install PyGObject
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3-gobject gtk3
pip install PyGObject
```

**macOS:**
```bash
brew install gtk+3 py3cairo pygobject3
pip install PyGObject
```

**Windows (MSYS2):**
```bash
pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python3-gobject
pip install PyGObject
```

---

## Installation & Running

```bash
# Clone the repository
git clone https://github.com/mreinrt/pystruct.git
cd pystruct

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python pystruct.py
```

---

## Usage Guide

### Basic Workflow
1. Select a directory using the file chooser or type the path.
2. Configure options:
   - Hidden Files – show/hide hidden files/directories
   - Permissions – show Unix file permissions (Linux/macOS only)
   - Groups – show owner and group info (Linux/macOS only)
   - Max Depth – limit tree expansion depth
3. Click **Generate** to build the tree.
4. **Browse** – click files to preview contents, double-click directories to expand/collapse.
5. **Copy** – use `Copy Selected File` or `Copy Tree` buttons.

### Multi-Tab Workflow
- Click **"+"** to create a new tab for a different directory.
- Click any tab to switch between different directory views.
- Click **"X"** on a tab to close it (cannot close the last tab).
- Each tab maintains independent settings and tree views.

### Refresh
- Click **Refresh** to reload the current tab's directory tree.

### About Dialog
- Click **About** to view project information and donation addresses.

### Ignore Rules
- Click **Ignore Rules** to edit patterns like `__pycache__/`, `.venv/`, `*.pyc`.

---

## Key Implementation Details

- **Gtk.TreeView with TreeStore** for efficient tree rendering
- **ASCII export** preserves connector alignment
- **Multi-encoding preview** (UTF-8 → Latin-1 → CP1252)
- **Recursive ignore system** with `.gitignore`-style matching
- **Dynamic GTK CSS theming**
- **Platform detection layer**

---

## Project Structure

```text
pystruct/
├── pystruct.py
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── README.md
└── media/
    ├── screenshot.png
    ├── tree_view.png
    ├── file_preview.png
    └── ignore_rules.png
```

---

## Development & Contributing

```bash
git checkout -b feature/amazing
git commit -m "Add amazing feature"
git push origin feature/amazing
```

---

## License

MIT License – see [LICENSE](LICENSE)

---

## Acknowledgements

- GTK3 / PyGObject team
- Python ecosystem

---

## About the Developer

Created by **Mike Reinert (BigSlimThic)**.

---

## Donate

**Bitcoin (BTC):** `3GtCgHhMP7NTxsdNjcDs7TUNSBK6EXoAzz`  
**Ethereum (ETH):** `0x5f1ed610a96c648478a775644c9244bf4e78631e`

---

## Links

- Repository: https://github.com/mreinrt/pystruct
- Issues: https://github.com/mreinrt/pystruct/issues
- Changelog: [CHANGELOG.md](CHANGELOG.md)