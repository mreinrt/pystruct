#!/usr/bin/env python3
"""
GTK Directory Tree Viewer
Run in virtual environment with: python gtk_directory_tree.py
"""

import os
import sys
import gi

# Check if running in venv
if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
    print("Warning: Not running in a virtual environment")
    print("Continue anyway? (y/n)")
    if input().lower() != 'y':
        sys.exit(1)

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
from pathlib import Path

class DirectoryTreeViewer(Gtk.Window):
    def __init__(self):
        super().__init__(title="pystruct - Directory ASCII Tree Viewer")
        self.set_default_size(900, 700)
        self.set_border_width(10)
        
        # Variables
        self.current_path = ""
        self.show_hidden = False
        self.max_depth = 3
        self.use_light_theme = False
        self.css_provider = Gtk.CssProvider()
        self.style_context = None
        
        self.setup_ui()
        self.setup_themes()
        self.apply_css()
        
    def setup_ui(self):
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        
        # Control frame
        control_frame = Gtk.Frame()
        control_frame.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(control_frame, False, False, 0)
        
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        control_box.set_border_width(10)
        control_frame.add(control_box)
        
        # Directory selection row
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        control_box.pack_start(dir_box, False, False, 0)
        
        dir_label = Gtk.Label(label="Directory:")
        dir_label.set_xalign(0)
        dir_box.pack_start(dir_label, False, False, 0)
        
        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_hexpand(True)
        self.dir_entry.set_placeholder_text("Select a directory...")
        dir_box.pack_start(self.dir_entry, True, True, 0)
        
        # All buttons now use the same style class
        browse_button = Gtk.Button(label="Browse")
        browse_button.set_can_focus(False)
        browse_button.get_style_context().add_class("standard-button")
        browse_button.connect("clicked", self.on_browse_clicked)
        dir_box.pack_start(browse_button, False, False, 0)
        
        generate_button = Gtk.Button(label="Generate Tree")
        generate_button.set_can_focus(False)
        generate_button.get_style_context().add_class("standard-button")
        generate_button.connect("clicked", self.on_generate_clicked)
        dir_box.pack_start(generate_button, False, False, 0)
        
        # Options row
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        control_box.pack_start(options_box, False, False, 0)
        
        # Hidden files checkbox
        self.hidden_check = Gtk.CheckButton(label="Show Hidden Files")
        self.hidden_check.set_can_focus(False)
        self.hidden_check.get_style_context().add_class("standard-check")
        self.hidden_check.connect("toggled", self.on_hidden_toggled)
        options_box.pack_start(self.hidden_check, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        options_box.pack_start(separator, False, False, 0)
        
        # Max depth spinner
        depth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        options_box.pack_start(depth_box, False, False, 0)
        
        depth_label = Gtk.Label(label="Max Depth:")
        depth_box.pack_start(depth_label, False, False, 0)
        
        self.depth_spinner = Gtk.SpinButton()
        self.depth_spinner.set_can_focus(False)
        self.depth_spinner.get_style_context().add_class("standard-spin")
        self.depth_spinner.set_range(1, 10)
        self.depth_spinner.set_increments(1, 2)
        self.depth_spinner.set_value(3)
        self.depth_spinner.connect("value-changed", self.on_depth_changed)
        depth_box.pack_start(self.depth_spinner, False, False, 0)
        
        # Right side buttons
        right_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        options_box.pack_end(right_button_box, False, False, 0)
        
        # Theme toggle button
        self.theme_button = Gtk.Button(label="Switch to Light Theme")
        self.theme_button.set_can_focus(False)
        self.theme_button.get_style_context().add_class("standard-button")
        self.theme_button.connect("clicked", self.on_theme_toggled)
        right_button_box.pack_start(self.theme_button, False, False, 0)
        
        # Copy button
        copy_button = Gtk.Button(label="Copy to Clipboard")
        copy_button.set_can_focus(False)
        copy_button.get_style_context().add_class("standard-button")
        copy_button.connect("clicked", self.on_copy_clicked)
        right_button_box.pack_start(copy_button, False, False, 0)
        
        # Scrolled window with text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Text view for displaying tree
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.text_view.set_monospace(True)
        
        # Set font
        font_desc = Pango.FontDescription("Monospace 10")
        self.text_view.modify_font(font_desc)
        
        scrolled.add(self.text_view)
        
        # Status bar - made more visible with custom styling
        status_frame = Gtk.Frame()
        status_frame.set_shadow_type(Gtk.ShadowType.IN)
        status_frame.get_style_context().add_class("status-frame")
        vbox.pack_start(status_frame, False, False, 0)
        
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_border_width(2)
        status_frame.add(status_box)
        
        # Status icon
        self.status_icon = Gtk.Image.new_from_icon_name("dialog-information", Gtk.IconSize.MENU)
        status_box.pack_start(self.status_icon, False, False, 5)
        
        # Status label
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        self.status_label.get_style_context().add_class("status-label")
        status_box.pack_start(self.status_label, True, True, 0)
        
        # Connect signals
        self.connect("destroy", Gtk.main_quit)
        
    def setup_themes(self):
        """Setup dark theme (hacker green) and light theme CSS"""
        # Dark theme - solid hacker green text, no glow
        self.dark_theme_css = """
        window {
            background-color: #0a0a0a;
        }
        
        frame {
            border-radius: 6px;
            background-color: #1a1a1a;
            border: 1px solid #33ff33;
        }
        
        /* Remove focus indicators from all widgets */
        *:focus {
            outline: none;
            box-shadow: none;
        }
        
        /* Standard button style - solid hacker green text */
        .standard-button {
            background-image: linear-gradient(to bottom, #2a2a2a, #1a1a1a);
            color: #33ff33;
            border: 1px solid #33ff33;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: bold;
            text-shadow: none;
        }
        
        .standard-button:hover {
            background-image: linear-gradient(to bottom, #3a3a3a, #2a2a2a);
            border-color: #33ff33;
            color: #33ff33;
        }
        
        .standard-button:active {
            background-image: linear-gradient(to bottom, #1a1a1a, #0a0a0a);
        }
        
        /* Checkbutton styling */
        .standard-check {
            color: #33ff33;
        }
        
        .standard-check:hover {
            color: #33ff33;
        }
        
        /* Spinbutton styling */
        .standard-spin {
            background-image: linear-gradient(to bottom, #2a2a2a, #1a1a1a);
            color: #33ff33;
            border: 1px solid #33ff33;
            border-radius: 3px;
        }
        
        .standard-spin:hover {
            background-image: linear-gradient(to bottom, #3a3a3a, #2a2a2a);
        }
        
        entry {
            border-radius: 4px;
            padding: 5px;
            border: 1px solid #33ff33;
            background-image: linear-gradient(to bottom, #2a2a2a, #1a1a1a);
            color: #33ff33;
        }
        
        entry:focus {
            border: 2px solid #33ff33;
        }
        
        label {
            color: #33ff33;
        }
        
        textview {
            background-color: #0a0a0a;
            border: 1px solid #33ff33;
            border-radius: 4px;
        }
        
        textview text {
            background-color: #0a0a0a;
            color: #33ff33;
        }
        
        /* Status bar - solid green text */
        .status-frame {
            background-image: linear-gradient(to bottom, #1a1a1a, #0a0a0a);
            border: 1px solid #33ff33;
            border-radius: 4px;
        }
        
        .status-label {
            color: #33ff33;
            font-weight: bold;
            text-shadow: none;
        }
        
        separator {
            background-color: #33ff33;
        }
        """
        
        # Light theme (explicit light colors)
        self.light_theme_css = """
        window {
            background-color: #f0f0f0;
        }
        
        frame {
            border-radius: 6px;
            background-color: #ffffff;
            border: 1px solid #a0a0a0;
        }
        
        /* Remove focus indicators */
        *:focus {
            outline: none;
            box-shadow: none;
        }
        
        /* Standard button style */
        .standard-button {
            background-image: linear-gradient(to bottom, #f0f0f0, #d0d0d0);
            color: #202020;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
            padding: 5px 10px;
            font-weight: normal;
            text-shadow: none;
        }
        
        .standard-button:hover {
            background-image: linear-gradient(to bottom, #ffffff, #e0e0e0);
        }
        
        .standard-button:active {
            background-image: linear-gradient(to bottom, #d0d0d0, #b0b0b0);
        }
        
        /* Checkbutton styling */
        .standard-check {
            color: #202020;
        }
        
        /* Spinbutton styling */
        .standard-spin {
            background-image: linear-gradient(to bottom, #ffffff, #f0f0f0);
            color: #202020;
            border: 1px solid #a0a0a0;
            border-radius: 3px;
        }
        
        .standard-spin:hover {
            background-image: linear-gradient(to bottom, #ffffff, #f8f8f8);
        }
        
        entry {
            border-radius: 4px;
            padding: 5px;
            border: 1px solid #a0a0a0;
            background-color: #ffffff;
            color: #202020;
        }
        
        entry:focus {
            border: 2px solid #4a90d9;
        }
        
        textview {
            background-color: #ffffff;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
        }
        
        textview text {
            background-color: #ffffff;
            color: #202020;
        }
        
        /* Status bar */
        .status-frame {
            background-image: linear-gradient(to bottom, #e0e0e0, #c0c0c0);
            border: 1px solid #a0a0a0;
            border-radius: 4px;
        }
        
        .status-label {
            color: #202020;
            font-weight: bold;
            text-shadow: none;
        }
        
        separator {
            background-color: #c0c0c0;
        }
        """
        
    def apply_css(self):
        """Apply CSS based on current theme"""
        # Remove old CSS provider
        if self.style_context:
            self.style_context.remove_provider_for_screen(
                Gdk.Screen.get_default(),
                self.css_provider
            )
        
        # Load new CSS
        if self.use_light_theme:
            self.css_provider.load_from_data(self.light_theme_css.encode())
            self.theme_button.set_label("Switch to Dark Theme")
        else:
            self.css_provider.load_from_data(self.dark_theme_css.encode())
            self.theme_button.set_label("Switch to Light Theme")
        
        # Apply new CSS
        self.style_context = Gtk.StyleContext()
        self.style_context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Force redraw of all widgets
        self.queue_draw()
        
    def on_theme_toggled(self, widget):
        """Handle theme toggle button click"""
        self.use_light_theme = not self.use_light_theme
        self.apply_css()
        theme_name = "dark" if not self.use_light_theme else "light"
        self.update_status(f"Switched to {theme_name} theme")
        
    def on_browse_clicked(self, widget):
        """Handle browse button click"""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        if self.current_path:
            dialog.set_current_folder(self.current_path)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.current_path = dialog.get_filename()
            self.dir_entry.set_text(self.current_path)
            self.update_status(f"Selected: {self.current_path}")
            
        dialog.destroy()
        
    def on_generate_clicked(self, widget):
        """Handle generate button click"""
        directory = self.dir_entry.get_text()
        
        if not directory:
            self.show_error_dialog("Please select a directory first.")
            return
        
        if not os.path.exists(directory):
            self.show_error_dialog("Directory does not exist.")
            return
        
        self.generate_tree()
        
    def on_hidden_toggled(self, widget):
        """Handle hidden files checkbox toggle"""
        self.show_hidden = widget.get_active()
        
    def on_depth_changed(self, widget):
        """Handle depth spinner change"""
        self.max_depth = int(widget.get_value())
        
    def on_copy_clicked(self, widget):
        """Handle copy button click"""
        try:
            buffer = self.text_view.get_buffer()
            start, end = buffer.get_bounds()
            tree_text = buffer.get_text(start, end, False)
            
            if tree_text:
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(tree_text, -1)
                self.update_status("Tree copied to clipboard!")
                GLib.timeout_add_seconds(2, lambda: self.update_status("Ready"))
            else:
                self.show_error_dialog("No tree to copy. Generate one first.")
                
        except Exception as e:
            self.show_error_dialog(f"Failed to copy: {str(e)}")
            
    def should_ignore(self, name):
        """Check if file/directory should be ignored based on hidden files setting"""
        if not self.show_hidden and name.startswith('.'):
            return True
        return False
    
    def generate_ascii_tree(self, path, prefix="", depth=0, is_last=True):
        """Generate ASCII tree structure"""
        if depth > self.max_depth:
            return [prefix + "└── ... (max depth reached)"]
        
        lines = []
        path_obj = Path(path)
        
        try:
            # Get all items in directory
            items = sorted([item for item in path_obj.iterdir() 
                           if not self.should_ignore(item.name)])
            
            for i, item in enumerate(items):
                is_last_item = (i == len(items) - 1)
                
                # Choose the correct prefix for the current item
                if depth == 0:
                    current_prefix = ""
                    next_prefix = ""
                else:
                    current_prefix = "└── " if is_last_item else "├── "
                    next_prefix = "    " if is_last_item else "│   "
                
                # Add the current item
                if item.is_dir():
                    lines.append(f"{prefix}{current_prefix}{item.name}/")
                    # Recursively process subdirectories
                    sub_lines = self.generate_ascii_tree(
                        item, 
                        prefix + next_prefix, 
                        depth + 1,
                        is_last_item
                    )
                    lines.extend(sub_lines)
                else:
                    lines.append(f"{prefix}{current_prefix}{item.name}")
                    
        except PermissionError:
            lines.append(f"{prefix}└── [Permission Denied]")
        except Exception as e:
            lines.append(f"{prefix}└── [Error: {str(e)}]")
            
        return lines
    
    def generate_tree(self):
        """Generate and display the directory tree"""
        directory = self.current_path
        
        try:
            # Clear the text view
            buffer = self.text_view.get_buffer()
            buffer.set_text("")
            
            # Generate the tree
            self.update_status(f"Generating tree for: {directory}")
            
            tree_lines = self.generate_ascii_tree(directory)
            
            # Add header
            header = f"Directory Tree: {directory}\n"
            header += "=" * 50 + "\n\n"
            
            # Create text buffer with the tree
            full_text = header + "\n".join(tree_lines)
            buffer.set_text(full_text)
            
            # Scroll to top
            self.text_view.scroll_to_iter(buffer.get_start_iter(), 0, False, 0, 0)
            
            self.update_status(f"Tree generated successfully. {len(tree_lines)} items displayed.")
            
        except Exception as e:
            self.show_error_dialog(f"Failed to generate tree: {str(e)}")
            self.update_status("Error generating tree")
    
    def show_error_dialog(self, message):
        """Show error dialog"""
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
        """Update status bar"""
        self.status_label.set_text(message)
        
        # Update icon based on message type
        if "Error" in message:
            self.status_icon.set_from_icon_name("dialog-error", Gtk.IconSize.MENU)
        elif "successfully" in message:
            self.status_icon.set_from_icon_name("dialog-ok-apply", Gtk.IconSize.MENU)
        else:
            self.status_icon.set_from_icon_name("dialog-information", Gtk.IconSize.MENU)
            
        return False  # For GLib.timeout_add

def check_dependencies():
    """Check if all dependencies are available"""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        return True
    except (ImportError, ValueError) as e:
        print(f"Dependency error: {e}")
        print("\nMake sure you have installed PyGObject in your venv:")
        print("pip install PyGObject")
        print("\nAnd system GTK libraries:")
        print("- Ubuntu/Debian: sudo apt-get install gir1.2-gtk-3.0")
        print("- Fedora: sudo dnf install gtk3")
        print("- Arch: sudo pacman -S gtk3")
        return False

def main():
    """Main function"""
    # Check if running in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix
    
    print(f"Python: {sys.executable}")
    print(f"Virtual Environment: {'Yes' if in_venv else 'No'}")
    
    if not check_dependencies():
        sys.exit(1)
    
    try:
        app = DirectoryTreeViewer()
        app.show_all()
        Gtk.main()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()