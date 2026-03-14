#!/usr/bin/env python3
"""
GTK Directory Tree Viewer - GUI only, no terminal prompts
"""

import os
import stat
import pwd
import grp
import fnmatch
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib


class DirectoryTreeViewer(Gtk.Window):
    def __init__(self):
        super().__init__(title="pystruct - Directory ASCII Tree Viewer")
        self.set_default_size(900, 700)
        self.set_border_width(10)

        self.current_path = ""
        self.show_hidden = False
        self.show_groups = False
        self.show_permissions = False
        self.max_depth = 3

        self.ignore_patterns = self.get_default_gitignore()

        self.css_provider = Gtk.CssProvider()
        self.style_context = None

        self.setup_ui()
        self.setup_css()
        self.apply_css()

    # ---------------------------------------------------------
    # Default Python gitignore preset
    # ---------------------------------------------------------

    def get_default_gitignore(self):
        return [
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "*.egg-info/",
            "*.egg",
            ".installed.cfg",
            "*.manifest",
            "*.spec",
            "pip-log.txt",
            "pip-delete-this-directory.txt",
            ".tox/",
            ".nox/",
            ".coverage",
            ".coverage.*",
            ".cache",
            "nosetests.xml",
            "coverage.xml",
            "*.cover",
            "*.log",
            ".pytest_cache/",
            ".mypy_cache/",
            ".pyre/",
            ".hypothesis/",
            ".venv/",
            "venv/",
            "ENV/",
            "env/",
            ".env",
            ".env.*",
            ".idea/",
            ".vscode/",
            "*.swp",
            "*.swo",
            "*~"
        ]

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def setup_ui(self):

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        control_frame = Gtk.Frame()
        control_frame.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(control_frame, False, False, 0)

        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        control_box.set_border_width(10)
        control_frame.add(control_box)

        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        control_box.pack_start(dir_box, False, False, 0)

        dir_label = Gtk.Label(label="Directory:")
        dir_label.set_xalign(0)
        dir_box.pack_start(dir_label, False, False, 0)

        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_hexpand(True)
        dir_box.pack_start(self.dir_entry, True, True, 0)

        browse_button = Gtk.Button(label="Browse")
        browse_button.set_can_focus(False)
        browse_button.connect("clicked", self.on_browse_clicked)
        dir_box.pack_start(browse_button, False, False, 0)

        generate_button = Gtk.Button(label="Generate Tree")
        generate_button.set_can_focus(False)
        generate_button.connect("clicked", self.on_generate_clicked)
        dir_box.pack_start(generate_button, False, False, 0)

        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        control_box.pack_start(options_box, False, False, 0)

        self.hidden_check = Gtk.CheckButton(label="Show Hidden Files")
        self.hidden_check.set_can_focus(False)
        self.hidden_check.connect("toggled", self.on_hidden_toggled)
        options_box.pack_start(self.hidden_check, False, False, 0)

        self.groups_check = Gtk.CheckButton(label="Show Groups")
        self.groups_check.set_can_focus(False)
        self.groups_check.connect("toggled", self.on_groups_toggled)
        options_box.pack_start(self.groups_check, False, False, 0)

        self.permissions_check = Gtk.CheckButton(label="Show Permissions")
        self.permissions_check.set_can_focus(False)
        self.permissions_check.connect("toggled", self.on_permissions_toggled)
        options_box.pack_start(self.permissions_check, False, False, 0)

        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        options_box.pack_start(separator, False, False, 0)

        depth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        options_box.pack_start(depth_box, False, False, 0)

        depth_label = Gtk.Label(label="Max Depth:")
        depth_box.pack_start(depth_label, False, False, 0)

        self.depth_spinner = Gtk.SpinButton()
        self.depth_spinner.set_range(1, 10)
        self.depth_spinner.set_value(3)
        self.depth_spinner.connect("value-changed", self.on_depth_changed)
        depth_box.pack_start(self.depth_spinner, False, False, 0)

        right_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        options_box.pack_end(right_button_box, False, False, 0)

        copy_button = Gtk.Button(label="Copy to Clipboard")
        copy_button.set_can_focus(False)
        copy_button.connect("clicked", self.on_copy_clicked)
        right_button_box.pack_start(copy_button, False, False, 0)

        ignore_button = Gtk.Button(label="Ignore Rules")
        ignore_button.set_can_focus(False)
        ignore_button.connect("clicked", self.on_ignore_rules_clicked)
        right_button_box.pack_start(ignore_button, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        scrolled.add(self.text_view)

        status_frame = Gtk.Frame()
        vbox.pack_start(status_frame, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        status_frame.add(status_box)

        self.status_label = Gtk.Label(label="Ready")
        status_box.pack_start(self.status_label, True, True, 5)

        self.connect("destroy", Gtk.main_quit)

    # ---------------------------------------------------------
    # Ignore dialog
    # ---------------------------------------------------------

    def on_ignore_rules_clicked(self, widget):

        dialog = Gtk.Dialog(
            title="Ignore Rules (.gitignore style)",
            parent=self,
            flags=0
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY,
            Gtk.ResponseType.OK
        )

        dialog.set_default_size(500, 400)

        box = dialog.get_content_area()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        box.add(scrolled)

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
                line.strip()
                for line in text.splitlines()
                if line.strip() and not line.startswith("#")
            ]

            self.update_status("Ignore rules updated.")

        dialog.destroy()

    # ---------------------------------------------------------
    # Event handlers
    # ---------------------------------------------------------

    def on_browse_clicked(self, widget):

        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK
        )

        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            self.current_path = dialog.get_filename()
            self.dir_entry.set_text(self.current_path)
            self.update_status(f"Selected: {self.current_path}")

        dialog.destroy()

    def on_generate_clicked(self, widget):

        directory = self.dir_entry.get_text()

        if not directory or not os.path.exists(directory):

            self.show_error_dialog("Please select a valid directory.")
            return

        self.current_path = directory
        self.generate_tree()

    def on_hidden_toggled(self, widget):
        self.show_hidden = widget.get_active()

    def on_groups_toggled(self, widget):
        self.show_groups = widget.get_active()

    def on_permissions_toggled(self, widget):
        self.show_permissions = widget.get_active()

    def on_depth_changed(self, widget):
        self.max_depth = int(widget.get_value())

    def on_copy_clicked(self, widget):

        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, False)

        if text:

            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)

            self.update_status("Tree copied to clipboard!")

    # ---------------------------------------------------------
    # Ignore logic
    # ---------------------------------------------------------

    def should_ignore(self, name):

        if not self.show_hidden and name.startswith("."):
            return True

        for pattern in self.ignore_patterns:

            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name + "/", pattern):
                return True

        return False

    # ---------------------------------------------------------
    # Tree generation
    # ---------------------------------------------------------

    def generate_ascii_tree(self, path, prefix="", depth=0, is_root=False):

        if depth > self.max_depth:
            return [prefix + "└── ..."]

        lines = []

        try:

            if is_root:

                root = os.path.basename(path) or path
                lines.append(root)
                prefix += "    "
                depth += 1

            items = [
                item for item in Path(path).iterdir()
                if not self.should_ignore(item.name)
            ]

            files = sorted([i for i in items if i.is_file()], key=lambda x: x.name)
            dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name)

            sorted_items = files + dirs

            for i, item in enumerate(sorted_items):

                last = i == len(sorted_items) - 1
                branch = "└── " if last else "├── "
                extension = "    " if last else "│   "

                name = item.name + "/" if item.is_dir() else item.name

                lines.append(prefix + branch + name)

                if item.is_dir():

                    lines.extend(
                        self.generate_ascii_tree(
                            item,
                            prefix + extension,
                            depth + 1
                        )
                    )

        except PermissionError:

            lines.append(prefix + "└── [Permission Denied]")

        return lines

    def generate_tree(self):

        buffer = self.text_view.get_buffer()

        tree_lines = self.generate_ascii_tree(
            self.current_path,
            is_root=True
        )

        header = f"Parent Directory: {os.path.basename(self.current_path)}\n"
        header += f"Full Path: {self.current_path}\n"
        header += f"Max Depth: {self.max_depth}\n\n"

        buffer.set_text(header + "\n".join(tree_lines))

        self.update_status(
            f"Tree generated ({len(tree_lines)} items)"
        )

    # ---------------------------------------------------------
    # UI helpers
    # ---------------------------------------------------------

    def show_error_dialog(self, message):

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )

        dialog.run()
        dialog.destroy()

    def update_status(self, message):

        self.status_label.set_text(message)

    # ---------------------------------------------------------
    # CSS
    # ---------------------------------------------------------

    def setup_css(self):

        self.green_text_css = """
        label { color:#00ff00; }
        textview text { color:#00ff00; }
        entry { color:#00ff00; }
        spinbutton { color:#00ff00; }
        """

    def apply_css(self):

        self.css_provider.load_from_data(self.green_text_css.encode())

        screen = Gdk.Screen.get_default()

        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def check_dependencies():

    try:
        import gi
        gi.require_version('Gtk', '3.0')
        return True
    except Exception:
        return False


def main():

    if not check_dependencies():
        return

    app = DirectoryTreeViewer()
    app.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()