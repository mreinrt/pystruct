#!/usr/bin/env python3
"""
GTK Directory Tree Viewer - A graphical directory tree viewer with file content preview
"""

import os
import stat
import pwd
import grp
import fnmatch
from pathlib import Path
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


class DirectoryTreeViewer(Gtk.Window):
    """Main application window for directory tree viewing"""

    def __init__(self):
        super().__init__(title="pystruct - Directory Tree Viewer")
        self.set_default_size(900, 1000)
        self.set_border_width(10)

        # Application state
        self.current_path = ""
        self.show_hidden = False
        self.show_groups = False
        self.show_permissions = False
        self.max_depth = 3
        self.selected_file_path = None

        # Ignore patterns (Python-centric .gitignore style)
        self.ignore_patterns = self._get_default_ignore_patterns()

        self._setup_ui()
        self._connect_signals()

    # -------------------------------------------------------------------------
    # UI Setup
    # -------------------------------------------------------------------------

    def _setup_ui(self):
        """Build the user interface"""
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(main_vbox)

        # Control panel
        control_frame = self._create_control_panel()
        main_vbox.pack_start(control_frame, False, False, 0)

        # Main content area (split pane)
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        main_vbox.pack_start(paned, True, True, 0)

        # Tree view (top section)
        tree_scrolled = self._create_tree_view()
        paned.pack1(tree_scrolled, True, False)

        # Content view (bottom section)
        content_frame = self._create_content_view()
        paned.pack2(content_frame, True, False)

        # Set divider position (600px from top for 1000px window height)
        paned.set_position(600)

        # Status bar
        status_frame = self._create_status_bar()
        main_vbox.pack_start(status_frame, False, False, 0)

    def _create_control_panel(self):
        """Create the control panel with directory selection and options"""
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)

        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        control_box.set_border_width(10)
        frame.add(control_box)

        # Directory selection row
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        control_box.pack_start(dir_box, False, False, 0)

        dir_label = Gtk.Label(label="Directory:")
        dir_label.set_xalign(0)
        dir_box.pack_start(dir_label, False, False, 0)

        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_hexpand(True)
        dir_box.pack_start(self.dir_entry, True, True, 0)

        browse_btn = Gtk.Button(label="Browse")
        browse_btn.set_can_focus(False)
        dir_box.pack_start(browse_btn, False, False, 0)

        generate_btn = Gtk.Button(label="Generate Tree")
        generate_btn.set_can_focus(False)
        dir_box.pack_start(generate_btn, False, False, 0)

        # Options row
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        control_box.pack_start(options_box, False, False, 0)

        self.hidden_check = Gtk.CheckButton(label="Show Hidden Files")
        self.hidden_check.set_can_focus(False)
        options_box.pack_start(self.hidden_check, False, False, 0)

        self.groups_check = Gtk.CheckButton(label="Show Groups")
        self.groups_check.set_can_focus(False)
        options_box.pack_start(self.groups_check, False, False, 0)

        self.permissions_check = Gtk.CheckButton(label="Show Permissions")
        self.permissions_check.set_can_focus(False)
        options_box.pack_start(self.permissions_check, False, False, 0)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        options_box.pack_start(separator, False, False, 0)

        # Depth selector
        depth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        options_box.pack_start(depth_box, False, False, 0)

        depth_label = Gtk.Label(label="Max Depth:")
        depth_box.pack_start(depth_label, False, False, 0)

        adjustment = Gtk.Adjustment(value=3, lower=1, upper=10,
                                    step_increment=1, page_increment=1, page_size=0)
        self.depth_spinner = Gtk.SpinButton(adjustment=adjustment)
        depth_box.pack_start(self.depth_spinner, False, False, 0)

        # Action buttons (right-aligned)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_halign(Gtk.Align.END)
        options_box.pack_end(action_box, False, False, 0)

        self.copy_selected_btn = Gtk.Button(label="Copy Selected File")
        self.copy_selected_btn.set_sensitive(False)
        action_box.pack_start(self.copy_selected_btn, False, False, 0)

        copy_tree_btn = Gtk.Button(label="Copy Tree")
        action_box.pack_start(copy_tree_btn, False, False, 0)

        ignore_btn = Gtk.Button(label="Ignore Rules")
        action_box.pack_start(ignore_btn, False, False, 0)

        # Store button references for signal connections
        self._browse_btn = browse_btn
        self._generate_btn = generate_btn
        self._copy_tree_btn = copy_tree_btn
        self._ignore_btn = ignore_btn

        return frame

    def _create_tree_view(self):
        """Create the directory tree view with ASCII pipe connectors"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # Tree model: (display_text, full_path, is_file, ascii_prefix)
        self.tree_store = Gtk.TreeStore(str, str, bool, str)
        self.tree_view = Gtk.TreeView(model=self.tree_store)
        self.tree_view.set_headers_visible(False)
        self.tree_view.set_activate_on_single_click(True)
        
        # CRITICAL: Disable the tree view's built-in indentation
        # We'll use our own ASCII prefixes instead
        self.tree_view.set_level_indentation(0)
        self.tree_view.set_show_expanders(False)  # Hide the default expanders
        
        # Enable expand/collapse with double-click only (no visual expanders)
        self.tree_view.set_expander_column(None)

        # Column with monospace font - use custom data function to combine prefix and text
        renderer = Gtk.CellRendererText()
        renderer.set_property("font", "Monospace 10")
        
        column = Gtk.TreeViewColumn("Directory Tree", renderer)
        
        # Custom data function to combine ASCII prefix with display text
        def cell_data_func(column, cell, model, iter_pos, data):
            prefix = model.get_value(iter_pos, 3)  # ASCII prefix
            text = model.get_value(iter_pos, 0)     # Display text
            cell.set_property("text", prefix + text)
        
        column.set_cell_data_func(renderer, cell_data_func)
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.tree_view.append_column(column)

        scrolled.add(self.tree_view)
        return scrolled

    def _create_content_view(self):
        """Create the file content preview panel"""
        frame = Gtk.Frame(label="File Content (Selected File)")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame.add(vbox)

        # Button bar
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_border_width(6)
        vbox.pack_start(button_box, False, False, 0)

        copy_content_btn = Gtk.Button(label="Copy Content")
        copy_content_btn.set_can_focus(False)
        button_box.pack_start(copy_content_btn, False, False, 0)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.set_can_focus(False)
        button_box.pack_start(clear_btn, False, False, 0)

        self.file_info_label = Gtk.Label(label="No file selected")
        self.file_info_label.set_xalign(0)
        self.file_info_label.set_hexpand(True)
        button_box.pack_start(self.file_info_label, True, True, 6)

        # Content text area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        vbox.pack_start(scrolled, True, True, 0)

        self.content_view = Gtk.TextView()
        self.content_view.set_editable(False)
        self.content_view.set_monospace(True)
        scrolled.add(self.content_view)

        # Store button references
        self._copy_content_btn = copy_content_btn
        self._clear_btn = clear_btn

        return frame

    def _create_status_bar(self):
        """Create the status bar at the bottom"""
        frame = Gtk.Frame()

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        frame.add(status_box)

        self.status_label = Gtk.Label(label="Ready")
        status_box.pack_start(self.status_label, True, True, 5)

        self.selected_file_label = Gtk.Label(label="")
        self.selected_file_label.set_halign(Gtk.Align.END)
        status_box.pack_start(self.selected_file_label, False, False, 5)

        return frame

    def _connect_signals(self):
        """Connect all signal handlers"""
        # Control panel signals
        self._browse_btn.connect("clicked", self._on_browse_clicked)
        self._generate_btn.connect("clicked", self._on_generate_clicked)
        self._copy_tree_btn.connect("clicked", self._on_copy_tree_clicked)
        self._ignore_btn.connect("clicked", self._on_ignore_rules_clicked)

        # Option toggles
        self.hidden_check.connect("toggled", self._on_hidden_toggled)
        self.groups_check.connect("toggled", self._on_groups_toggled)
        self.permissions_check.connect("toggled", self._on_permissions_toggled)
        self.depth_spinner.connect("value-changed", self._on_depth_changed)

        # Content view signals
        self._copy_content_btn.connect("clicked", self._on_copy_content_clicked)
        self._clear_btn.connect("clicked", self._on_clear_content_clicked)
        self.copy_selected_btn.connect("clicked", self._on_copy_selected_clicked)

        # Tree view signals
        selection = self.tree_view.get_selection()
        selection.connect("changed", self._on_tree_selection_changed)
        self.tree_view.connect("row-activated", self._on_row_activated)

        # Window signal
        self.connect("destroy", Gtk.main_quit)

    # -------------------------------------------------------------------------
    # Default Ignore Patterns
    # -------------------------------------------------------------------------

    def _get_default_ignore_patterns(self):
        """Return default Python-centric ignore patterns"""
        return [
            "__pycache__/", "*.py[cod]", "*$py.class", "*.so", ".Python",
            "build/", "develop-eggs/", "dist/", "downloads/", "eggs/",
            ".eggs/", "lib/", "lib64/", "parts/", "sdist/", "var/",
            "*.egg-info/", "*.egg", ".installed.cfg", "*.manifest", "*.spec",
            "pip-log.txt", "pip-delete-this-directory.txt", ".tox/", ".nox/",
            ".coverage", ".coverage.*", ".cache", "nosetests.xml",
            "coverage.xml", "*.cover", "*.log", ".pytest_cache/",
            ".mypy_cache/", ".pyre/", ".hypothesis/", ".venv/", "venv/",
            "ENV/", "env/", ".env", ".env.*", ".idea/", ".vscode/",
            "*.swp", "*.swo", "*~"
        ]

    # -------------------------------------------------------------------------
    # Tree Selection Handlers
    # -------------------------------------------------------------------------

    def _on_tree_selection_changed(self, selection):
        """Handle selection change in the tree view"""
        model, iter_pos = selection.get_selected()

        if not iter_pos:
            return

        file_path = model.get_value(iter_pos, 1)
        is_file = model.get_value(iter_pos, 2)

        if is_file and file_path and os.path.isfile(file_path):
            self.selected_file_path = file_path
            self.copy_selected_btn.set_sensitive(True)
            self.selected_file_label.set_text(f"Selected: {os.path.basename(file_path)}")
            self._update_status(f"Selected: {os.path.basename(file_path)}")
            self._load_file_content(file_path)
        elif file_path and os.path.isdir(file_path):
            self.selected_file_path = None
            self.copy_selected_btn.set_sensitive(False)
            self.selected_file_label.set_text(f"Directory: {os.path.basename(file_path)}")
            self._update_status(f"Directory selected: {os.path.basename(file_path)}")
            self._on_clear_content_clicked(None)

    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click to expand/collapse directories"""
        iter_pos = self.tree_store.get_iter(path)
        if not iter_pos:
            return

        is_file = self.tree_store.get_value(iter_pos, 2)
        if not is_file:
            if self.tree_view.row_expanded(path):
                self.tree_view.collapse_row(path)
            else:
                self.tree_view.expand_row(path, False)

    # -------------------------------------------------------------------------
    # File Content Handlers
    # -------------------------------------------------------------------------

    def _load_file_content(self, file_path):
        """Load and display file content"""
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            buffer = self.content_view.get_buffer()

            if content is not None:
                buffer.set_text(content)
                file_size = os.path.getsize(file_path)
                self.file_info_label.set_text(
                    f"File: {os.path.basename(file_path)} | Size: {file_size} bytes | Path: {file_path}"
                )
            else:
                buffer.set_text("[Binary file - cannot display content]")
                self.file_info_label.set_text(
                    f"File: {os.path.basename(file_path)} (Binary file) | Path: {file_path}"
                )

        except Exception as e:
            buffer = self.content_view.get_buffer()
            buffer.set_text(f"Error reading file: {str(e)}")
            self.file_info_label.set_text(f"Error: {os.path.basename(file_path)}")

    def _on_copy_content_clicked(self, widget):
        """Copy selected file content to clipboard"""
        if not self.selected_file_path:
            self._show_error_dialog("No file selected. Click on a file in the tree first.")
            return

        try:
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None

            for encoding in encodings:
                try:
                    with open(self.selected_file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is not None:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(content, -1)
                self._update_status(f"✓ Copied content of {os.path.basename(self.selected_file_path)}")
                self.selected_file_label.set_text(f"Copied: {os.path.basename(self.selected_file_path)}")
            else:
                self._show_error_dialog("Cannot copy binary file content")

        except Exception as e:
            self._show_error_dialog(f"Error copying file: {str(e)}")

    def _on_clear_content_clicked(self, widget):
        """Clear the content view"""
        buffer = self.content_view.get_buffer()
        buffer.set_text("")
        self.file_info_label.set_text("No file selected")
        self.selected_file_path = None

    def _on_copy_selected_clicked(self, widget):
        """Copy selected file content"""
        self._on_copy_content_clicked(widget)

    def _on_copy_tree_clicked(self, widget):
        """Copy entire tree to clipboard"""
        tree_text = self._tree_to_text()
        if tree_text:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(tree_text, -1)
            self._update_status("✓ Tree copied to clipboard!")

    # -------------------------------------------------------------------------
    # Ignore Rules Dialog
    # -------------------------------------------------------------------------

    def _on_ignore_rules_clicked(self, widget):
        """Open ignore rules editor dialog"""
        dialog = Gtk.Dialog(
            title="Ignore Rules (.gitignore style)",
            parent=self,
            flags=0
        )

        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_APPLY, Gtk.ResponseType.OK)
        dialog.set_default_size(500, 400)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        dialog.get_content_area().add(scrolled)

        textview = Gtk.TextView()
        textview.set_monospace(True)
        buffer = textview.get_buffer()
        buffer.set_text("\n".join(self.ignore_patterns))
        scrolled.add(textview)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            start, end = buffer.get_bounds()
            text = buffer.get_text(start, end, False)
            self.ignore_patterns = [
                line.strip() for line in text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            self._update_status("Ignore rules updated.")

        dialog.destroy()

    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------

    def _on_browse_clicked(self, widget):
        """Open directory chooser dialog"""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )

        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.current_path = dialog.get_filename()
            self.dir_entry.set_text(self.current_path)
            self._update_status(f"Selected: {self.current_path}")

        dialog.destroy()

    def _on_generate_clicked(self, widget):
        """Generate directory tree"""
        directory = self.dir_entry.get_text()

        if not directory or not os.path.exists(directory):
            self._show_error_dialog("Please select a valid directory.")
            return

        self.current_path = directory
        self._generate_tree()
        self._on_clear_content_clicked(widget)

    def _on_hidden_toggled(self, widget):
        self.show_hidden = widget.get_active()

    def _on_groups_toggled(self, widget):
        self.show_groups = widget.get_active()

    def _on_permissions_toggled(self, widget):
        self.show_permissions = widget.get_active()

    def _on_depth_changed(self, widget):
        self.max_depth = int(widget.get_value())

    # -------------------------------------------------------------------------
    # Ignore Logic
    # -------------------------------------------------------------------------

    def _should_ignore(self, name):
        """Check if a file/directory should be ignored"""
        if name.startswith("."):
            return not self.show_hidden

        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name + "/", pattern):
                return True

        return False

    # -------------------------------------------------------------------------
    # File Info Helpers
    # -------------------------------------------------------------------------

    def _get_permissions_string(self, path):
        """Get Unix permissions string like 'rwxr-xr-x'"""
        try:
            st = os.stat(path)
            mode = st.st_mode
            perms = []

            # User
            perms.append('r' if mode & stat.S_IRUSR else '-')
            perms.append('w' if mode & stat.S_IWUSR else '-')
            perms.append('x' if mode & stat.S_IXUSR else '-')
            # Group
            perms.append('r' if mode & stat.S_IRGRP else '-')
            perms.append('w' if mode & stat.S_IWGRP else '-')
            perms.append('x' if mode & stat.S_IXGRP else '-')
            # Other
            perms.append('r' if mode & stat.S_IROTH else '-')
            perms.append('w' if mode & stat.S_IWOTH else '-')
            perms.append('x' if mode & stat.S_IXOTH else '-')

            return ''.join(perms)
        except:
            return '---------'

    def _get_owner_string(self, path):
        """Get owner and group as string"""
        try:
            st = os.stat(path)
            owner = pwd.getpwuid(st.st_uid).pw_name
            if self.show_groups:
                group = grp.getgrgid(st.st_gid).gr_name
                return f"{owner}:{group}"
            return owner
        except:
            return "unknown"

    # -------------------------------------------------------------------------
    # Tree Generation with ASCII Pipe Connectors
    # -------------------------------------------------------------------------

    def _add_to_tree_store(self, parent_iter, path, prefix="", is_last=True, depth=0):
        """Recursively add items to tree store with ASCII pipe connectors"""
        if depth >= self.max_depth:
            return

        try:
            items = []
            for item in Path(path).iterdir():
                if not self._should_ignore(item.name):
                    items.append(item)

            files = sorted([i for i in items if i.is_file()], key=lambda x: x.name)
            dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name)
            sorted_items = dirs + files

            for i, item in enumerate(sorted_items):
                last = i == len(sorted_items) - 1
                
                # Determine the branch character for this item
                branch = "└── " if last else "├── "
                
                # Build the ASCII prefix for this item
                ascii_prefix = prefix + branch
                
                # Prepare next level's prefix
                extension = "    " if last else "│   "
                next_prefix = prefix + extension

                # Build the display name with optional metadata
                name = item.name + "/" if item.is_dir() else item.name
                is_file = item.is_file()

                # Add metadata if requested
                metadata = ""
                if self.show_permissions or self.show_groups:
                    perm_str = self._get_permissions_string(str(item)) if self.show_permissions else ""
                    owner_str = self._get_owner_string(str(item)) if (self.show_permissions or self.show_groups) else ""

                    if self.show_permissions and self.show_groups:
                        metadata = f" [{perm_str}] [{owner_str}]"
                    elif self.show_permissions:
                        metadata = f" [{perm_str}]"
                    elif self.show_groups:
                        metadata = f" [{owner_str}]"

                display_text = name + metadata
                
                # Add to tree store
                child_iter = self.tree_store.append(parent_iter, [display_text, str(item), is_file, ascii_prefix])

                # Recurse into directories
                if item.is_dir():
                    self._add_to_tree_store(child_iter, str(item), next_prefix, last, depth + 1)

        except PermissionError:
            self.tree_store.append(parent_iter, ["[Permission Denied]", None, False, prefix + "└── "])

    def _generate_tree(self):
        """Generate the directory tree with ASCII pipe connectors"""
        self.tree_store.clear()

        # Root node has no prefix
        root_name = os.path.basename(self.current_path) or self.current_path
        root_iter = self.tree_store.append(None, [root_name, self.current_path, False, ""])

        # Add children with ASCII prefixes
        self._add_to_tree_store(root_iter, self.current_path, "", True, 1)
        
        # Expand all nodes
        self.tree_view.expand_all()

        self._update_status("Tree generated successfully")

    def _tree_to_text(self):
        """Convert tree store to ASCII text for copying"""
        def iter_to_text(model, iter_pos, prefix="", is_last=True):
            lines = []
            text = model.get_value(iter_pos, 0)
            lines.append(prefix + ("└── " if is_last else "├── ") + text)

            new_prefix = prefix + ("    " if is_last else "│   ")
            child_iter = model.iter_children(iter_pos)
            n_children = model.iter_n_children(iter_pos)

            for i in range(n_children):
                child_lines = iter_to_text(model, child_iter, new_prefix, i == n_children - 1)
                lines.extend(child_lines)
                child_iter = model.iter_next(child_iter)

            return lines

        # Build header
        header = f"Parent Directory: {os.path.basename(self.current_path)}\n"
        header += f"Full Path: {self.current_path}\n"
        header += f"Max Depth: {self.max_depth}\n"

        settings = []
        if self.show_hidden:
            settings.append("Hidden files shown")
        if self.show_permissions:
            settings.append("Permissions shown")
        if self.show_groups:
            settings.append("Groups shown")
        if settings:
            header += f"Options: {', '.join(settings)}\n"

        header += "\n" + "=" * 80 + "\n\n"

        # Build tree
        root_lines = []
        root_iter = self.tree_store.get_iter_first()
        while root_iter:
            root_lines.extend(iter_to_text(self.tree_store, root_iter, "", True))
            root_iter = self.tree_store.iter_next(root_iter)

        return header + "\n".join(root_lines)

    # -------------------------------------------------------------------------
    # UI Helpers
    # -------------------------------------------------------------------------

    def _show_error_dialog(self, message):
        """Display an error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def _update_status(self, message):
        """Update status bar message"""
        self.status_label.set_text(message)


def main():
    """Application entry point"""
    app = DirectoryTreeViewer()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()