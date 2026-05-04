#!/usr/bin/env python3
"""
GTK Directory Tree Viewer - Cross-platform directory tree viewer with file content preview
Supports Linux, macOS, and Windows with traditional browser-style tabs
"""

import os
import stat
import sys
import fnmatch
import getpass
from pathlib import Path
import gi

# Check GTK availability before proceeding
def check_gtk_available():
    """Check if GTK is available on the system"""
    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, Gdk, Pango, GLib
        return True
    except (ImportError, ValueError) as e:
        print(f"GTK not available: {e}")
        print("Please install GTK3 for your platform:")
        print("  Linux: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        print("  macOS: brew install gtk+3 py3cairo pygobject3")
        print("  Windows: Use MSYS2: pacman -S mingw-w64-x86_64-gtk3 python3-gobject")
        return False

if not check_gtk_available():
    sys.exit(1)

from gi.repository import Gtk, Gdk, Pango, GLib

# Platform detection
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform.startswith('darwin')
IS_LINUX = not IS_WINDOWS and not IS_MACOS

# Display platform info (optional but helpful)
if IS_WINDOWS:
    print("Running on Windows - permissions/group features disabled")
elif IS_MACOS:
    print("Running on macOS - full features available")
else:
    print("Running on Linux - full features available")

# Conditional imports for Unix-only features
if IS_LINUX or IS_MACOS:
    try:
        import pwd
        import grp
        HAS_UNIX_OWNER = True
    except ImportError:
        HAS_UNIX_OWNER = False
else:
    HAS_UNIX_OWNER = False

# Check for ctypes on Windows
if IS_WINDOWS:
    try:
        import ctypes
        HAS_CTYPES = True
    except ImportError:
        HAS_CTYPES = False
        print("Warning: ctypes not available, hidden file detection may be limited")
else:
    HAS_CTYPES = False


class AboutDialog(Gtk.Dialog):
    """About dialog with donation information"""
    
    def __init__(self, parent=None):
        super().__init__(title="About pystruct", parent=parent, flags=0)
        self.set_default_size(600, 500)
        self.set_border_width(10)
        
        # Create main layout
        vbox = self.get_content_area()
        vbox.set_spacing(10)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(10)
        
        # About text (using a scrolled window for long text)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 300)
        
        about_text = Gtk.TextView()
        about_text.set_editable(False)
        about_text.set_cursor_visible(False)
        about_text.set_wrap_mode(Gtk.WrapMode.WORD)
        about_text.set_margin_start(10)
        about_text.set_margin_end(10)
        about_text.set_margin_top(10)
        about_text.set_margin_bottom(10)
        
        # Apply font using CSS instead of deprecated override_font
        css_provider = Gtk.CssProvider()
        css = """
        textview {
            font-family: Monospace;
            font-size: 10pt;
        }
        """
        css_provider.load_from_data(css.encode())
        about_text.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        about_buffer = about_text.get_buffer()
        about_text_content = """pystruct - Directory Tree Viewer

Created by Mike Reinert, a self-taught developer from Philadelphia who has faced extraordinary challenges.

Growing up on the tough streets of Philly and later struggling to survive with no stable residency since 18, he's experienced homelessness, unstable housing, and countless days wondering where the next meal would come from.

Now based in the Philippines, he continues to face daily hardships—living without running water and electricity, and the constant uncertainty that comes with unstable residency.

Despite these circumstances, Mike taught himself Linux—specifically Gentoo—and software engineering from the ground up. Every line of code in pystruct was written on hardware most would consider obsolete, against odds that would have stopped most people.

But what keeps him going is his girlfriend, who works as a kasambahay (stay-in domestic helper) for an abusive boss that only lets her take off one day every month. She endures long hours while dreaming of a better life for herself and her family. Her strength reminds Mike every day why he can't give up.

The streets of Philadelphia taught him resilience; Gentoo taught him that you can build something powerful from the ground up if you're willing to put in the work.

pystruct exists because Mike refuses to let his circumstances define his future—and because he dreams of a day when his girlfriend no longer has to work for someone who mistreats her, when her family has enough, and when they can finally build a life together with dignity and stability.

This project is dedicated to everyone who has ever been told they can't, shouldn't, or won't make it—the underdogs, the overlooked, the ones grinding in the dark when no one's watching.

It's for the kasambahay working through abuse, for the families who go without, and for anyone fighting for something better. If a guy from Philly with no running water can build this, imagine what you can do.

If you find value in pystruct, consider supporting its creator. Your support helps Mike continue developing and improving this tool, and moves him—and the woman who inspires him—closer to basic necessities many take for granted: stable electricity, running water, reliable internet, freedom from abuse, and a place to finally call home together."""
        
        about_buffer.set_text(about_text_content)
        scrolled.add(about_text)
        vbox.pack_start(scrolled, True, True, 0)
        
        # BTC Section
        btc_frame = Gtk.Frame(label="Bitcoin (BTC)")
        btc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btc_box.set_margin_start(10)
        btc_box.set_margin_end(10)
        btc_box.set_margin_top(10)
        btc_box.set_margin_bottom(10)
        
        btc_address = Gtk.Label(label="3GtCgHhMP7NTxsdNjcDs7TUNSBK6EXoAzz")
        btc_address.set_selectable(True)
        btc_address.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        
        btc_copy_btn = Gtk.Button(label="Copy")
        btc_copy_btn.set_size_request(60, -1)
        btc_copy_btn.connect("clicked", lambda w: self._copy_to_clipboard("3GtCgHhMP7NTxsdNjcDs7TUNSBK6EXoAzz", btc_copy_btn))
        
        btc_box.pack_start(btc_address, True, True, 0)
        btc_box.pack_start(btc_copy_btn, False, False, 0)
        btc_frame.add(btc_box)
        vbox.pack_start(btc_frame, False, False, 0)
        
        # ETH Section
        eth_frame = Gtk.Frame(label="Ethereum (ETH)")
        eth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        eth_box.set_margin_start(10)
        eth_box.set_margin_end(10)
        eth_box.set_margin_top(10)
        eth_box.set_margin_bottom(10)
        
        eth_address = Gtk.Label(label="0x5f1ed610a96c648478a775644c9244bf4e78631e")
        eth_address.set_selectable(True)
        eth_address.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        
        eth_copy_btn = Gtk.Button(label="Copy")
        eth_copy_btn.set_size_request(60, -1)
        eth_copy_btn.connect("clicked", lambda w: self._copy_to_clipboard("0x5f1ed610a96c648478a775644c9244bf4e78631e", eth_copy_btn))
        
        eth_box.pack_start(eth_address, True, True, 0)
        eth_box.pack_start(eth_copy_btn, False, False, 0)
        eth_frame.add(eth_box)
        vbox.pack_start(eth_frame, False, False, 0)
        
        # Close button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        close_btn = Gtk.Button(label="Close")
        close_btn.set_size_request(100, -1)
        close_btn.connect("clicked", lambda w: self.destroy())
        button_box.pack_start(close_btn, False, False, 0)
        vbox.pack_start(button_box, False, False, 0)
        
        self.show_all()
    
    def _copy_to_clipboard(self, text, button):
        """Copy text to clipboard and show temporary feedback"""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        
        # Temporarily change button text to show feedback
        original_label = button.get_label()
        button.set_label("Copied!")
        
        # Reset button text after 1 second
        GLib.timeout_add(1000, self._reset_button, button, original_label)
    
    def _reset_button(self, button, original_label):
        """Reset button text"""
        if button:
            button.set_label(original_label)
        return False


class TreeTab:
    """Represents a single tab with its own tree view and state"""
    
    def __init__(self, tab_id, title="New Tab"):
        self.id = tab_id
        self.title = title
        self.current_path = ""
        self.show_hidden = False
        self.show_groups = False
        self.show_permissions = False
        self.max_depth = 3
        self.selected_file_path = None
        self.ignore_patterns = None
        self.tree_store = None
        self.tree_view = None
        self.content_view = None
        self.file_info_label = None
        self.status_label = None
        self.selected_file_label = None
        self.tab_content = None
        self.tab_button = None
        self.tab_label = None
        self.stack_id = None
        self.tab_widget = None
        
    def create_tab_content(self, parent_window):
        """Create the content for this tab (tree view and preview)"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Main content area (split pane)
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(paned, True, True, 0)
        
        # Tree view (top section)
        tree_scrolled = self._create_tree_view(parent_window)
        paned.pack1(tree_scrolled, True, False)
        
        # Content view (bottom section)
        content_frame = self._create_content_view(parent_window)
        paned.pack2(content_frame, True, False)
        
        # Set divider position
        paned.set_position(600)
        
        # Status bar
        status_frame = self._create_status_bar(parent_window)
        vbox.pack_start(status_frame, False, False, 0)
        
        self.tab_content = vbox
        return vbox
    
    def _create_tree_view(self, parent_window):
        """Create the directory tree view with ASCII pipe connectors"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Tree model: (display_text, full_path, is_file, ascii_prefix)
        self.tree_store = Gtk.TreeStore(str, str, bool, str)
        self.tree_view = Gtk.TreeView(model=self.tree_store)
        self.tree_view.set_headers_visible(False)
        self.tree_view.set_activate_on_single_click(True)
        
        # Disable built-in indentation
        self.tree_view.set_level_indentation(0)
        self.tree_view.set_show_expanders(False)
        self.tree_view.set_expander_column(None)
        
        # Column with monospace font
        renderer = Gtk.CellRendererText()
        renderer.set_property("font", "Monospace 10")
        
        column = Gtk.TreeViewColumn("Directory Tree", renderer)
        
        def cell_data_func(column, cell, model, iter_pos, data):
            prefix = model.get_value(iter_pos, 3)
            text = model.get_value(iter_pos, 0)
            cell.set_property("text", prefix + text)
        
        column.set_cell_data_func(renderer, cell_data_func)
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.tree_view.append_column(column)
        
        # Connect signals
        selection = self.tree_view.get_selection()
        selection.connect("changed", lambda s: self._on_tree_selection_changed(parent_window, s))
        self.tree_view.connect("row-activated", self._on_row_activated)
        
        scrolled.add(self.tree_view)
        return scrolled
    
    def _create_content_view(self, parent_window):
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
        copy_content_btn.connect("clicked", lambda w: self._on_copy_content_clicked(parent_window))
        button_box.pack_start(copy_content_btn, False, False, 0)
        
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.set_can_focus(False)
        clear_btn.connect("clicked", lambda w: self._on_clear_content_clicked())
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
        
        return frame
    
    def _create_status_bar(self, parent_window):
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
    
    def clear_tab(self):
        """Clear all content from the tab"""
        # Clear tree store
        if self.tree_store:
            self.tree_store.clear()
        
        # Clear content view
        if self.content_view:
            buffer = self.content_view.get_buffer()
            buffer.set_text("")
        
        # Reset file info label
        if self.file_info_label:
            self.file_info_label.set_text("No file selected")
        
        # Reset selected file path
        self.selected_file_path = None
        
        # Clear current path
        self.current_path = ""
        
        # Update status
        self._update_status("New tab created - select a directory and click Generate Tree")
    
    def update_tab_label(self):
        """Update the tab label with the current directory name"""
        if self.tab_label:
            if self.current_path:
                dir_name = os.path.basename(self.current_path)
                if not dir_name:
                    dir_name = self.current_path
                if len(dir_name) > 10:
                    dir_name = dir_name[:8] + "..."
                label_text = dir_name
                tooltip = self.current_path
            else:
                label_text = "New Tab"
                tooltip = "Empty tab - select a directory"
            
            self.tab_label.set_text(label_text)
            self.tab_label.set_tooltip_text(tooltip)
    
    def _on_tree_selection_changed(self, parent_window, selection):
        """Handle selection change in the tree view"""
        model, iter_pos = selection.get_selected()
        
        if not iter_pos:
            return
        
        file_path = model.get_value(iter_pos, 1)
        is_file = model.get_value(iter_pos, 2)
        
        if is_file and file_path and os.path.isfile(file_path):
            self.selected_file_path = file_path
            self.selected_file_label.set_text(f"Selected: {os.path.basename(file_path)}")
            self._update_status(f"Selected: {os.path.basename(file_path)}")
            self._load_file_content(file_path)
            parent_window._update_copy_button_sensitivity()
        elif file_path and os.path.isdir(file_path):
            self.selected_file_path = None
            self.selected_file_label.set_text(f"Directory: {os.path.basename(file_path)}")
            self._update_status(f"Directory selected: {os.path.basename(file_path)}")
            self._on_clear_content_clicked()
            parent_window._update_copy_button_sensitivity()
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click to expand/collapse directories"""
        iter_pos = self.tree_store.get_iter(path)
        if not iter_pos:
            return
        
        is_file = self.tree_store.get_value(iter_pos, 2)
        if not is_file:
            if tree_view.row_expanded(path):
                tree_view.collapse_row(path)
            else:
                tree_view.expand_row(path, False)
    
    def _on_copy_content_clicked(self, parent_window):
        """Copy selected file content to clipboard"""
        if not self.selected_file_path:
            parent_window._show_error_dialog("No file selected. Click on a file in the tree first.")
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
                parent_window._show_error_dialog("Cannot copy binary file content")
        
        except Exception as e:
            parent_window._show_error_dialog(f"Error copying file: {str(e)}")
    
    def _on_clear_content_clicked(self):
        """Clear the content view"""
        buffer = self.content_view.get_buffer()
        buffer.set_text("")
        self.file_info_label.set_text("No file selected")
        self.selected_file_path = None
    
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
    
    def _is_hidden_file_windows(self, path):
        """Check if file is hidden on Windows"""
        if not IS_WINDOWS or not HAS_CTYPES:
            return False
        
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return attrs != -1 and bool(attrs & 2)
        except:
            return False
    
    def _is_hidden_file_macos(self, path):
        """Check if file is hidden on macOS"""
        if not IS_MACOS:
            return False
        
        if os.path.basename(path).startswith('.'):
            return True
        
        try:
            import subprocess
            result = subprocess.run(['ls', '-lO', str(path)], 
                                   capture_output=True, text=True, timeout=1)
            return 'hidden' in result.stdout
        except:
            return False
    
    def _should_ignore(self, name, full_path=None):
        """Check if a file/directory should be ignored"""
        if IS_WINDOWS and full_path:
            if self._is_hidden_file_windows(full_path):
                return not self.show_hidden
        elif IS_MACOS and full_path:
            if self._is_hidden_file_macos(full_path):
                return not self.show_hidden
        else:
            if name.startswith("."):
                return not self.show_hidden
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name + "/", pattern):
                return True
        
        return False
    
    def _get_permissions_string(self, path):
        """Get permissions string (Unix only)"""
        if IS_WINDOWS:
            return ""
        
        try:
            st = os.stat(path)
            mode = st.st_mode
            perms = []
            
            perms.append('r' if mode & stat.S_IRUSR else '-')
            perms.append('w' if mode & stat.S_IWUSR else '-')
            perms.append('x' if mode & stat.S_IXUSR else '-')
            perms.append('r' if mode & stat.S_IRGRP else '-')
            perms.append('w' if mode & stat.S_IWGRP else '-')
            perms.append('x' if mode & stat.S_IXGRP else '-')
            perms.append('r' if mode & stat.S_IROTH else '-')
            perms.append('w' if mode & stat.S_IWOTH else '-')
            perms.append('x' if mode & stat.S_IXOTH else '-')
            
            return ''.join(perms)
        except:
            return '---------'
    
    def _get_owner_string(self, path):
        """Get owner and group (Unix only)"""
        if IS_WINDOWS:
            try:
                return getpass.getuser()
            except:
                return os.environ.get('USERNAME', 'unknown')
        
        if not HAS_UNIX_OWNER:
            return "unknown"
        
        try:
            st = os.stat(path)
            owner = pwd.getpwuid(st.st_uid).pw_name
            if self.show_groups:
                group = grp.getgrgid(st.st_gid).gr_name
                return f"{owner}:{group}"
            return owner
        except:
            return "unknown"
    
    def _add_to_tree_store(self, parent_iter, path, prefix="", is_last=True, depth=0):
        """Recursively add items to tree store with ASCII pipe connectors"""
        if depth >= self.max_depth:
            return
        
        try:
            items = []
            for item in Path(path).iterdir():
                if not self._should_ignore(item.name, str(item)):
                    items.append(item)
            
            if IS_WINDOWS:
                files = sorted([i for i in items if i.is_file()], key=lambda x: x.name.lower())
                dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name.lower())
            else:
                files = sorted([i for i in items if i.is_file()], key=lambda x: x.name)
                dirs = sorted([i for i in items if i.is_dir()], key=lambda x: x.name)
            
            sorted_items = dirs + files
            
            for i, item in enumerate(sorted_items):
                last = i == len(sorted_items) - 1
                branch = "└── " if last else "├── "
                ascii_prefix = prefix + branch
                extension = "    " if last else "│   "
                next_prefix = prefix + extension
                
                name = item.name + "/" if item.is_dir() else item.name
                is_file = item.is_file()
                
                metadata = ""
                if (self.show_permissions or self.show_groups) and not IS_WINDOWS:
                    perm_str = self._get_permissions_string(str(item)) if self.show_permissions else ""
                    owner_str = self._get_owner_string(str(item)) if (self.show_permissions or self.show_groups) else ""
                    
                    if self.show_permissions and self.show_groups and perm_str and owner_str:
                        metadata = f" [{perm_str}] [{owner_str}]"
                    elif self.show_permissions and perm_str:
                        metadata = f" [{perm_str}]"
                    elif self.show_groups and owner_str:
                        metadata = f" [{owner_str}]"
                
                display_text = name + metadata
                
                child_iter = self.tree_store.append(parent_iter, [display_text, str(item), is_file, ascii_prefix])
                
                if item.is_dir():
                    self._add_to_tree_store(child_iter, str(item), next_prefix, last, depth + 1)
        
        except PermissionError:
            self.tree_store.append(parent_iter, ["[Permission Denied]", None, False, prefix + "└── "])
        except Exception as e:
            self.tree_store.append(parent_iter, [f"[Error: {str(e)[:50]}]", None, False, prefix + "└── "])
    
    def generate_tree(self):
        """Generate the directory tree with ASCII pipe connectors"""
        if not self.current_path:
            self._update_status("No directory selected. Please select a directory first.")
            return
        
        self.tree_store.clear()
        
        root_name = os.path.basename(self.current_path) or self.current_path
        root_iter = self.tree_store.append(None, [root_name, self.current_path, False, ""])
        
        self._add_to_tree_store(root_iter, self.current_path, "", True, 1)
        self.tree_view.expand_all()
        
        self.update_tab_label()
        
        self._update_status("Tree generated successfully")
    
    def refresh(self):
        """Refresh the current tab's tree view"""
        if self.current_path and os.path.exists(self.current_path):
            self.generate_tree()
            self._update_status("Tree refreshed successfully")
        else:
            self._update_status("No directory selected. Please select a directory first.")
    
    def _tree_to_text(self):
        """Convert tree store to ASCII text for copying - respects expanded/collapsed state"""
        def iter_to_text(model, iter_pos, prefix="", is_last=True):
            lines = []
            text = model.get_value(iter_pos, 0)
            
            # Get current path for this node
            path = model.get_path(iter_pos)
            
            # Check if this node is expanded (has visible children)
            # We need to check if the tree view has this row expanded
            is_expanded = self.tree_view.row_expanded(path)
            
            # Always add current node
            lines.append(prefix + ("└── " if is_last else "├── ") + text)
            
            # Only process children if this node is expanded
            if is_expanded:
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
        if self.show_permissions and not IS_WINDOWS:
            settings.append("Permissions shown")
        if self.show_groups and not IS_WINDOWS:
            settings.append("Groups shown")
        if settings:
            header += f"Options: {', '.join(settings)}\n"
        
        header += "\n" + "=" * 80 + "\n\n"
        
        # Build tree - only expanded nodes will be included
        root_lines = []
        root_iter = self.tree_store.get_iter_first()
        while root_iter:
            root_lines.extend(iter_to_text(self.tree_store, root_iter, "", True))
            root_iter = self.tree_store.iter_next(root_iter)
        
        return header + "\n".join(root_lines)
    
    def _update_status(self, message):
        """Update status bar message"""
        if self.status_label:
            self.status_label.set_text(message)
    
    def copy_tree_to_clipboard(self):
        """Copy tree to clipboard"""
        tree_text = self._tree_to_text()
        if tree_text:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(tree_text, -1)
            self._update_status("✓ Tree copied to clipboard!")
            return True
        return False


class DirectoryTreeViewer(Gtk.Window):
    """Main application window with traditional browser-style tabs"""
    
    def __init__(self):
        super().__init__(title="pystruct - Directory Tree Viewer")
        self.set_default_size(900, 1000)
        self.set_border_width(0)
        
        # Tab management
        self.tabs = []
        self.next_tab_id = 1
        self.current_tab = None
        self.stack = None
        self.tab_bar = None
        
        # Default ignore patterns
        self.default_ignore_patterns = self._get_default_ignore_patterns()
        
        self._setup_ui()
        self._connect_signals()
        
        # Create initial tab
        self._add_new_tab()
        
        # Apply minimal CSS that respects system theme
        self._apply_minimal_css()
    
    def _apply_minimal_css(self):
        """Apply minimal CSS that enhances but doesn't override system theme"""
        css_provider = Gtk.CssProvider()
        css = """
        /* Style for tab buttons */
        .tab-button {
            transition: all 0.2s ease;
            border: 1px solid transparent;
            border-radius: 3px;
            background: transparent;
            background-color: transparent;
            padding: 4px 8px;
            margin: 2px;
        }
        
        /* Active tab styling - bold border */
        .tab-button.active {
            font-weight: bold;
            border: 2px solid @theme_selected_bg_color;
            background: transparent;
            background-color: transparent;
        }
        
        /* Hover effect - border only */
        .tab-button:hover {
            border: 2px solid alpha(@theme_selected_bg_color, 0.8);
            background: transparent;
            background-color: transparent;
        }
        
        /* Close button inside tab styling */
        .close-button {
            border: none;
            padding: 0;
            margin: 0 2px;
            background: transparent;
            min-width: 20px;
            min-height: 20px;
        }
        
        .close-button:hover {
            background: alpha(@theme_selected_bg_color, 0.2);
            border-radius: 3px;
        }
        
        /* Plus button styling */
        .plus-button {
            font-weight: bold;
            background: transparent;
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 4px 8px;
            margin: 2px;
        }
        
        .plus-button:hover {
            border: 2px solid @theme_selected_bg_color;
            background: transparent;
            background-color: transparent;
        }
        """
        css_provider.load_from_data(css.encode())
        
        # Apply to the application
        screen = Gdk.Screen.get_default()
        style_context = self.get_style_context()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def _setup_ui(self):
        """Build the user interface"""
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Control panel (shared across all tabs)
        control_frame = self._create_control_panel()
        main_vbox.pack_start(control_frame, False, False, 0)
        
        # Tab bar (custom)
        self.tab_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.tab_bar.set_margin_top(5)
        self.tab_bar.set_margin_bottom(0)
        self.tab_bar.set_margin_start(5)
        self.tab_bar.set_margin_end(5)
        main_vbox.pack_start(self.tab_bar, False, False, 0)
        
        # Add separator line under tab bar
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_vbox.pack_start(separator, False, False, 0)
        
        # Stack for tab content
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(200)
        main_vbox.pack_start(self.stack, True, True, 0)
    
    def _create_control_panel(self):
        """Create the shared control panel with directory selection and options"""
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        control_box.set_border_width(10)
        frame.add(control_box)
        
        # Directory selection row
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        control_box.pack_start(dir_box, False, False, 0)
        
        dir_label = Gtk.Label(label="Path:")
        dir_label.set_xalign(0)
        dir_label.set_size_request(30, -1)
        dir_box.pack_start(dir_label, False, False, 0)
        
        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_hexpand(True)
        self.dir_entry.connect("activate", lambda w: self._on_generate_clicked())
        dir_box.pack_start(self.dir_entry, True, True, 0)
        
        browse_btn = Gtk.Button(label="Browse")
        browse_btn.set_can_focus(False)
        browse_btn.connect("clicked", lambda w: self._on_browse_clicked())
        browse_btn.set_size_request(80, -1)
        dir_box.pack_start(browse_btn, False, False, 0)
        
        generate_btn = Gtk.Button(label="Generate")
        generate_btn.set_can_focus(False)
        generate_btn.connect("clicked", lambda w: self._on_generate_clicked())
        generate_btn.set_size_request(80, -1)
        dir_box.pack_start(generate_btn, False, False, 0)
        
        # About button - next to Generate
        about_btn = Gtk.Button(label="About")
        about_btn.set_can_focus(False)
        about_btn.connect("clicked", lambda w: self._on_about_clicked())
        about_btn.set_size_request(80, -1)
        dir_box.pack_start(about_btn, False, False, 0)
        
        # Options row
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        control_box.pack_start(options_box, False, False, 0)
        
        self.hidden_check = Gtk.CheckButton(label="Hidden Files")
        self.hidden_check.set_can_focus(False)
        self.hidden_check.connect("toggled", lambda w: self._on_hidden_toggled())
        options_box.pack_start(self.hidden_check, False, False, 0)
        
        self.groups_check = Gtk.CheckButton(label="Groups")
        self.groups_check.set_can_focus(False)
        self.groups_check.connect("toggled", lambda w: self._on_groups_toggled())
        options_box.pack_start(self.groups_check, False, False, 0)
        
        self.permissions_check = Gtk.CheckButton(label="Permissions")
        self.permissions_check.set_can_focus(False)
        self.permissions_check.connect("toggled", lambda w: self._on_permissions_toggled())
        options_box.pack_start(self.permissions_check, False, False, 0)
        
        # Disable Unix-only features on Windows
        if IS_WINDOWS:
            self.permissions_check.set_sensitive(False)
            self.groups_check.set_sensitive(False)
            self.permissions_check.set_tooltip_text("Not available on Windows")
            self.groups_check.set_tooltip_text("Not available on Windows")
        
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
        self.depth_spinner.connect("value-changed", lambda w: self._on_depth_changed())
        depth_box.pack_start(self.depth_spinner, False, False, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_halign(Gtk.Align.END)
        options_box.pack_end(action_box, False, False, 0)
        
        # Refresh button - left of Copy Selected File
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.set_can_focus(False)
        refresh_btn.connect("clicked", lambda w: self._on_refresh_clicked())
        refresh_btn.set_size_request(80, -1)
        action_box.pack_start(refresh_btn, False, False, 0)
        
        self.copy_selected_btn = Gtk.Button(label="Copy Selected File")
        self.copy_selected_btn.set_sensitive(False)
        self.copy_selected_btn.connect("clicked", lambda w: self._on_copy_selected_clicked())
        action_box.pack_start(self.copy_selected_btn, False, False, 0)
        
        copy_tree_btn = Gtk.Button(label="Copy Tree")
        copy_tree_btn.connect("clicked", lambda w: self._on_copy_tree_clicked())
        action_box.pack_start(copy_tree_btn, False, False, 0)
        
        ignore_btn = Gtk.Button(label="Ignore Rules")
        ignore_btn.connect("clicked", lambda w: self._on_ignore_rules_clicked())
        action_box.pack_start(ignore_btn, False, False, 0)
        
        return frame
    
    def _on_about_clicked(self):
        """Open about dialog"""
        dialog = AboutDialog(self)
        dialog.run()
        dialog.destroy()
    
    def _on_refresh_clicked(self):
        """Refresh the current tab"""
        if self.current_tab:
            self.current_tab.refresh()
    
    def _create_tab_widget(self, tab):
        """Create a complete tab widget using EventBox for click control"""
        # Use EventBox instead of Button for better click control
        event_box = Gtk.EventBox()
        
        # Create a horizontal box for the content
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_start(8)
        button_box.set_margin_end(8)
        button_box.set_margin_top(4)
        button_box.set_margin_bottom(4)
        
        # Tab label
        label = Gtk.Label(label="New Tab")
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_width_chars(10)
        label.set_max_width_chars(10)
        
        # Close button with fallback for cross-platform compatibility
        try:
            close_btn = Gtk.Button.new_from_icon_name("window-close", Gtk.IconSize.MENU)
        except:
            close_btn = Gtk.Button(label="×")
            close_btn.set_size_request(20, 20)
        
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.set_focus_on_click(False)
        close_btn.set_tooltip_text("Close tab")
        close_btn.set_size_request(16, 16)
        
        # Add style class to close button
        close_style = close_btn.get_style_context()
        close_style.add_class("close-button")
        
        # Pack widgets into the button box
        button_box.pack_start(label, True, True, 0)
        button_box.pack_start(close_btn, False, False, 0)
        
        # Add the box to the event box
        event_box.add(button_box)
        
        # Add style class to event box
        style_context = event_box.get_style_context()
        style_context.add_class("tab-button")
        
        # Store references
        tab.tab_button = event_box
        tab.tab_label = label
        tab.tab_widget = event_box
        
        # Connect events
        event_box.connect("button-press-event", self._on_tab_click, tab)
        close_btn.connect("clicked", self._on_tab_close_clicked, tab)
        
        return event_box
    
    def _on_tab_click(self, widget, event, tab):
        """Handle tab click - only if not clicking on close button"""
        self._switch_to_tab(tab)
        return True
    
    def _add_new_tab(self, title=None, switch_to=True):
        """Add a new tab to the tab bar"""
        if title is None:
            title = f"Tab {self.next_tab_id}"
        
        # Create new tab
        tab = TreeTab(self.next_tab_id, title)
        tab.ignore_patterns = self.default_ignore_patterns.copy()
        
        # Create tab content
        tab_content = tab.create_tab_content(self)
        
        # Create tab widget (EventBox with integrated close button)
        tab_widget = self._create_tab_widget(tab)
        
        # Clear the tab content (make it blank)
        tab.clear_tab()
        
        # Add to tab bar (before the plus button)
        self.tab_bar.pack_start(tab_widget, False, False, 0)
        
        # Add to stack
        stack_id = f"tab_{self.next_tab_id}"
        tab.stack_id = stack_id
        self.stack.add_named(tab_content, stack_id)
        
        # Store tab reference
        self.tabs.append(tab)
        
        # Show all new widgets
        tab_widget.show_all()
        tab_content.show_all()
        
        self.next_tab_id += 1
        
        # Ensure plus button is at the end
        self._ensure_plus_button()
        
        # Switch to new tab if requested
        if switch_to:
            self._switch_to_tab(tab)
            
            # Clear the directory entry field
            self.dir_entry.set_text("")
            
            # Show status
            self._update_status("New tab created - select a directory and click Generate Tree")
        
        return tab
    
    def _ensure_plus_button(self):
        """Ensure the plus button is always the last item in the tab bar"""
        # Remove existing plus button if any
        for child in self.tab_bar.get_children():
            if hasattr(child, 'is_plus_button') and child.is_plus_button:
                self.tab_bar.remove(child)
                break
        
        # Create plus button
        plus_button = Gtk.Button()
        plus_button.set_label("+")
        plus_button.set_tooltip_text("Open new tab")
        plus_button.set_focus_on_click(False)
        plus_button.set_size_request(35, -1)
        plus_button.is_plus_button = True
        plus_button.connect("clicked", self._on_plus_button_clicked)
        
        # Add style class
        style_context = plus_button.get_style_context()
        style_context.add_class("plus-button")
        
        # Add to tab bar
        self.tab_bar.pack_start(plus_button, False, False, 0)
        plus_button.show()
    
    def _on_plus_button_clicked(self, button):
        """Handle plus button click"""
        self._add_new_tab()
    
    def _on_tab_close_clicked(self, button, tab):
        """Close the selected tab"""
        if len(self.tabs) <= 1:
            self._show_error_dialog("Cannot close the last tab. Create a new tab first if needed.")
            return
        
        # Remove from tab bar
        if tab.tab_widget:
            self.tab_bar.remove(tab.tab_widget)
        
        # Remove from stack
        if tab.stack_id:
            child = self.stack.get_child_by_name(tab.stack_id)
            if child:
                self.stack.remove(child)
        
        # Remove from tabs list
        self.tabs.remove(tab)
        
        # Switch to another tab if this was current
        if self.current_tab == tab and self.tabs:
            self._switch_to_tab(self.tabs[0])
    
    def _switch_to_tab(self, tab):
        """Switch to a specific tab with proper highlighting"""
        self.current_tab = tab
        
        # Update stack visibility
        if tab.stack_id:
            self.stack.set_visible_child_name(tab.stack_id)
        
        # Update button styling
        for t in self.tabs:
            if t.tab_button:
                style_context = t.tab_button.get_style_context()
                
                if t == tab:
                    # Add active class to current tab
                    style_context.add_class("active")
                else:
                    # Remove active class from others
                    style_context.remove_class("active")
        
        # Update controls
        self._update_controls_from_tab(tab)
        
        # Update copy button sensitivity
        self._update_copy_button_sensitivity()
    
    def _update_controls_from_tab(self, tab):
        """Update control panel to reflect tab's current settings"""
        self.dir_entry.set_text(tab.current_path)
        self.hidden_check.set_active(tab.show_hidden)
        self.groups_check.set_active(tab.show_groups)
        self.permissions_check.set_active(tab.show_permissions)
        self.depth_spinner.set_value(tab.max_depth)
    
    def _on_browse_clicked(self):
        """Open directory chooser dialog"""
        if not self.current_tab:
            return
        
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            self.current_tab.current_path = dialog.get_filename()
            self.dir_entry.set_text(self.current_tab.current_path)
            self._update_status(f"Selected: {self.current_tab.current_path}")
        
        dialog.destroy()
    
    def _on_generate_clicked(self):
        """Generate directory tree for current tab"""
        if not self.current_tab:
            return
        
        directory = self.dir_entry.get_text()
        
        if not directory or not os.path.exists(directory):
            self._show_error_dialog("Please select a valid directory.")
            return
        
        self.current_tab.current_path = directory
        self.current_tab.generate_tree()
        
        # Clear file preview
        if self.current_tab.content_view:
            buffer = self.current_tab.content_view.get_buffer()
            buffer.set_text("")
            if self.current_tab.file_info_label:
                self.current_tab.file_info_label.set_text("No file selected")
        self._update_copy_button_sensitivity()
    
    def _on_hidden_toggled(self):
        """Toggle hidden files for current tab"""
        if self.current_tab:
            self.current_tab.show_hidden = self.hidden_check.get_active()
            if self.current_tab.current_path:
                self.current_tab.generate_tree()
    
    def _on_groups_toggled(self):
        """Toggle groups for current tab"""
        if self.current_tab and not IS_WINDOWS:
            self.current_tab.show_groups = self.groups_check.get_active()
            if self.current_tab.current_path:
                self.current_tab.generate_tree()
    
    def _on_permissions_toggled(self):
        """Toggle permissions for current tab"""
        if self.current_tab and not IS_WINDOWS:
            self.current_tab.show_permissions = self.permissions_check.get_active()
            if self.current_tab.current_path:
                self.current_tab.generate_tree()
    
    def _on_depth_changed(self):
        """Change max depth for current tab"""
        if self.current_tab:
            self.current_tab.max_depth = int(self.depth_spinner.get_value())
            if self.current_tab.current_path:
                self.current_tab.generate_tree()
    
    def _on_copy_selected_clicked(self):
        """Copy selected file content"""
        if self.current_tab and self.current_tab.selected_file_path:
            self.current_tab._on_copy_content_clicked(self)
    
    def _on_copy_tree_clicked(self):
        """Copy entire tree to clipboard"""
        if self.current_tab:
            self.current_tab.copy_tree_to_clipboard()
    
    def _on_ignore_rules_clicked(self):
        """Open ignore rules editor dialog for current tab"""
        if not self.current_tab:
            return
        
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
        buffer.set_text("\n".join(self.current_tab.ignore_patterns))
        scrolled.add(textview)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            start, end = buffer.get_bounds()
            text = buffer.get_text(start, end, False)
            new_patterns = [
                line.strip() for line in text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            self.current_tab.ignore_patterns = new_patterns
            self._update_status("Ignore rules updated for current tab.")
            
            # Regenerate tree if needed
            if self.current_tab.current_path:
                self.current_tab.generate_tree()
        
        dialog.destroy()
    
    def _update_copy_button_sensitivity(self):
        """Update the sensitivity of the copy selected button"""
        if self.current_tab and self.current_tab.selected_file_path:
            self.copy_selected_btn.set_sensitive(True)
        else:
            self.copy_selected_btn.set_sensitive(False)
    
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
    
    def _connect_signals(self):
        """Connect main window signals"""
        self.connect("destroy", Gtk.main_quit)
    
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
        """Update status bar of current tab"""
        if self.current_tab and self.current_tab.status_label:
            self.current_tab.status_label.set_text(message)


def main():
    """Application entry point"""
    app = DirectoryTreeViewer()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()