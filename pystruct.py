#!/usr/bin/env python3
"""
GTK Directory Tree Viewer - GUI only, no terminal prompts
"""

import os
import stat
import pwd
import grp
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class DirectoryTreeViewer(Gtk.Window):
    def __init__(self):
        super().__init__(title="pystruct - Directory ASCII Tree Viewer")
        self.set_default_size(900, 700)
        self.set_border_width(10)

        # Variables
        self.current_path = ""
        self.show_hidden = False
        self.show_groups = False
        self.show_permissions = False
        self.max_depth = 3
        self.css_provider = Gtk.CssProvider()
        self.style_context = None

        self.setup_ui()
        self.setup_css()
        self.apply_css()

    def setup_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        control_frame = Gtk.Frame()
        control_frame.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(control_frame, False, False, 0)

        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        control_box.set_border_width(10)
        control_frame.add(control_box)

        # Directory row
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        control_box.pack_start(dir_box, False, False, 0)

        dir_label = Gtk.Label(label="Directory:")
        dir_label.set_xalign(0)
        dir_box.pack_start(dir_label, False, False, 0)

        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_hexpand(True)
        self.dir_entry.set_placeholder_text("Select a directory...")
        dir_box.pack_start(self.dir_entry, True, True, 0)

        browse_button = Gtk.Button(label="Browse")
        browse_button.set_can_focus(False)
        browse_button.connect("clicked", self.on_browse_clicked)
        dir_box.pack_start(browse_button, False, False, 0)

        generate_button = Gtk.Button(label="Generate Tree")
        generate_button.set_can_focus(False)
        generate_button.connect("clicked", self.on_generate_clicked)
        dir_box.pack_start(generate_button, False, False, 0)

        # Options row
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
        self.depth_spinner.set_can_focus(False)
        self.depth_spinner.set_range(1, 10)
        self.depth_spinner.set_increments(1, 2)
        self.depth_spinner.set_value(3)
        self.depth_spinner.connect("value-changed", self.on_depth_changed)
        depth_box.pack_start(self.depth_spinner, False, False, 0)

        # Right-side buttons
        right_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        options_box.pack_end(right_button_box, False, False, 0)

        copy_button = Gtk.Button(label="Copy to Clipboard")
        copy_button.set_can_focus(False)
        copy_button.connect("clicked", self.on_copy_clicked)
        right_button_box.pack_start(copy_button, False, False, 0)

        # Text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(scrolled, True, True, 0)

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.text_view.set_monospace(True)

        scrolled.add(self.text_view)

        # Status bar
        status_frame = Gtk.Frame()
        status_frame.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(status_frame, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_border_width(2)
        status_frame.add(status_box)

        self.status_icon = Gtk.Image.new_from_icon_name("dialog-information", Gtk.IconSize.MENU)
        status_box.pack_start(self.status_icon, False, False, 5)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        status_box.pack_start(self.status_label, True, True, 0)

        self.connect("destroy", Gtk.main_quit)

    # --- Event Handlers ---
    def on_browse_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if self.current_path:
            dialog.set_current_folder(self.current_path)
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
            GLib.timeout_add_seconds(2, lambda: self.update_status("Ready"))
        else:
            self.show_error_dialog("Nothing to copy.")

    # --- Core Functionality ---
    def should_ignore(self, name):
        return not self.show_hidden and name.startswith(".")

    def get_file_info(self, path):
        """Get file permissions and group information"""
        info = {}
        try:
            stat_info = os.stat(path)
            
            if self.show_permissions:
                # Get permissions in ls -l format
                mode = stat_info.st_mode
                perms = stat.filemode(mode)
                info['permissions'] = perms
            
            if self.show_groups:
                # Get owner and group
                try:
                    owner = pwd.getpwuid(stat_info.st_uid).pw_name
                except KeyError:
                    owner = str(stat_info.st_uid)
                
                try:
                    group = grp.getgrgid(stat_info.st_gid).gr_name
                except KeyError:
                    group = str(stat_info.st_gid)
                
                info['owner'] = owner
                info['group'] = group
                
        except (PermissionError, OSError):
            pass
        
        return info

    def format_item_name(self, name, is_dir, info):
        """Format item name with optional permissions and group info"""
        if is_dir:
            formatted = f"{name}/"
        else:
            formatted = name
        
        # Add permissions and group info if requested
        details = []
        if self.show_permissions and 'permissions' in info:
            details.append(info['permissions'])
        if self.show_groups and 'owner' in info and 'group' in info:
            details.append(f"{info['owner']}:{info['group']}")
        
        if details:
            formatted = f"{formatted}  [{', '.join(details)}]"
        
        return formatted

    def generate_ascii_tree(self, path, prefix="", depth=0, is_root=False):
        if depth > self.max_depth:
            return [prefix + "└── ... (max depth reached)"]
        
        lines = []
        try:
            # For root directory, just get the directory name
            if is_root:
                dir_name = os.path.basename(path)
                if not dir_name:  # Handle case when at filesystem root
                    dir_name = path
                
                # Get root directory info
                root_info = self.get_file_info(path)
                formatted_name = self.format_item_name(dir_name, True, root_info)
                lines.append(f"{prefix}{formatted_name}")
                prefix = prefix + "    "
                depth += 1
            
            # Get all items and filter hidden files if needed
            items = []
            for item in Path(path).iterdir():
                if not self.should_ignore(item.name):
                    items.append(item)
            
            # Separate files and directories
            files = [item for item in items if item.is_file()]
            dirs = [item for item in items if item.is_dir()]
            
            # Sort each group alphabetically
            files.sort(key=lambda x: x.name.lower())
            dirs.sort(key=lambda x: x.name.lower())
            
            # Combine files first, then directories
            sorted_items = files + dirs
            
            for i, item in enumerate(sorted_items):
                last = i == len(sorted_items) - 1
                current_prefix = "└── " if last else "├── "
                next_prefix = "    " if last else "│   "
                
                # Get file/directory info
                item_info = self.get_file_info(item)
                
                if item.is_dir():
                    formatted_name = self.format_item_name(item.name, True, item_info)
                    lines.append(f"{prefix}{current_prefix}{formatted_name}")
                    lines.extend(self.generate_ascii_tree(item, prefix + next_prefix, depth + 1))
                else:
                    formatted_name = self.format_item_name(item.name, False, item_info)
                    lines.append(f"{prefix}{current_prefix}{formatted_name}")
                    
        except PermissionError:
            lines.append(prefix + "└── [Permission Denied]")
        except Exception as e:
            lines.append(prefix + f"└── [Error: {e}]")
        return lines

    def generate_tree(self):
        buffer = self.text_view.get_buffer()
        buffer.set_text("")
        
        # Generate tree with root directory name
        tree_lines = self.generate_ascii_tree(self.current_path, is_root=True)
        
        # Create header with full path info and active options
        dir_name = os.path.basename(self.current_path)
        if not dir_name:  # Handle filesystem root
            dir_name = self.current_path
        
        header = f"Parent Directory: {dir_name}\n"
        header += f"Full Path: {self.current_path}\n"
        header += f"Options: {'Hidden' if self.show_hidden else 'No Hidden'}"
        if self.show_groups:
            header += ", Groups"
        if self.show_permissions:
            header += ", Permissions"
        header += f", Max Depth: {self.max_depth}\n\n"
        
        # Combine header and tree
        buffer.set_text(header + "\n".join(tree_lines))
        self.text_view.scroll_to_iter(buffer.get_start_iter(), 0, False, 0, 0)
        self.update_status(f"Tree generated successfully ({len(tree_lines)} items).")

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
        if "Error" in message:
            self.status_icon.set_from_icon_name("dialog-error", Gtk.IconSize.MENU)
        elif "successfully" in message or "copied" in message:
            self.status_icon.set_from_icon_name("dialog-ok-apply", Gtk.IconSize.MENU)
        else:
            self.status_icon.set_from_icon_name("dialog-information", Gtk.IconSize.MENU)
        return False

    # --- CSS ---
    def setup_css(self):
        # Only modify text colors to bright green, everything else uses system theme
        self.green_text_css = """
        /* Only modify text colors to bright green, everything else uses system theme */
        label {
            color: #00ff00;
        }
        
        button label {
            color: #00ff00;
        }
        
        checkbutton label {
            color: #00ff00;
        }
        
        entry {
            color: #00ff00;
        }
        
        entry selection {
            background-color: #00ff00;
            color: #000000;
        }
        
        textview text {
            color: #00ff00;
        }
        
        textview text selection {
            background-color: #00ff00;
            color: #000000;
        }
        
        .status-label {
            color: #00ff00;
        }
        
        spinbutton {
            color: #00ff00;
        }
        
        spinbutton entry {
            color: #00ff00;
        }
        """

    def apply_css(self):
        # Load and apply the green text CSS
        self.css_provider.load_from_data(self.green_text_css.encode())
        
        screen = Gdk.Screen.get_default()
        self.style_context = Gtk.StyleContext()
        self.style_context.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Force a UI refresh
        self.queue_draw()

def check_dependencies():
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        return True
    except (ImportError, ValueError):
        return False

def main():
    if not check_dependencies():
        return
    app = DirectoryTreeViewer()
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
