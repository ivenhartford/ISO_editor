import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import struct
from datetime import datetime
import tempfile
import shutil
import math
import traceback

class ISOEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ISO Editor")
        self.root.geometry("800x600")

        # Current ISO data
        self.current_iso_path = None
        self.iso_data = None
        self.volume_descriptor = None
        self.root_directory = None
        self.directory_tree = None
        self.tree_item_map = {}
        self.show_hidden = False
        self.selected_node = None
        self.iso_modified = False
        self.next_extent_location = 0
        self.iso_file_handle = None

        # Create GUI
        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()

    def create_menu(self):
        """Create the main menu bar"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open ISO...", command=self.open_iso)
        file_menu.add_command(label="New ISO...", command=self.new_iso)
        file_menu.add_separator()
        file_menu.add_command(label="Save ISO", command=self.save_iso)
        file_menu.add_command(label="Save ISO As...", command=self.save_iso_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add File...", command=self.add_file)
        edit_menu.add_command(label="Add Folder...", command=self.add_folder)
        edit_menu.add_command(label="Import Directory...", command=self.import_directory)
        edit_menu.add_separator()
        edit_menu.add_command(label="Remove Selected", command=self.remove_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="ISO Properties...", command=self.show_iso_properties)

        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_view)
        view_menu.add_command(label="Show Hidden Files", command=self.toggle_hidden_files)

    def create_main_interface(self):
        """Create the main interface with file explorer"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - ISO Properties
        left_frame = ttk.LabelFrame(main_frame, text="ISO Properties", width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)

        # ISO Info display
        self.iso_info = tk.Text(left_frame, width=30, height=15, wrap=tk.WORD)
        self.iso_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Volume name editing
        ttk.Label(left_frame, text="Volume Name:").pack(anchor=tk.W, padx=5)
        self.volume_name_var = tk.StringVar()
        self.volume_name_entry = ttk.Entry(left_frame, textvariable=self.volume_name_var)
        self.volume_name_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.volume_name_entry.bind('<Return>', self.update_volume_name)

        ttk.Button(left_frame, text="Update Volume Name",
                  command=self.update_volume_name).pack(pady=5)

        # Right panel - File Explorer
        right_frame = ttk.LabelFrame(main_frame, text="ISO Contents")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Add File", command=self.add_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Add Folder", command=self.add_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Import Dir", command=self.import_directory).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Remove", command=self.remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Extract", command=self.extract_selected).pack(side=tk.LEFT, padx=(0, 5))

        # File tree view
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, columns=('Size', 'Date', 'Type'), show='tree headings')
        self.tree.heading('#0', text='Name')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Date', text='Date Modified')
        self.tree.heading('Type', text='Type')

        # Configure column widths
        self.tree.column('#0', width=300)
        self.tree.column('Size', width=100)
        self.tree.column('Date', width=150)
        self.tree.column('Type', width=100)

        # Add scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        # Pack tree and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)

    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        """Update status bar message"""
        modified_indicator = " [Modified]" if self.iso_modified else ""
        self.status_bar.config(text=f"{message}{modified_indicator}")
        self.root.update_idletasks()

    def mark_modified(self):
        """Mark ISO as modified"""
        self.iso_modified = True
        if self.current_iso_path:
            filename = os.path.basename(self.current_iso_path)
            self.root.title(f"ISO Editor - {filename} [Modified]")
        else:
            self.root.title("ISO Editor [Modified]")
        self.update_status("ISO modified")

    def close_iso(self):
        """Close the currently open ISO file handle, if it exists."""
        if self.iso_file_handle:
            self.iso_file_handle.close()
            self.iso_file_handle = None

    def open_iso(self):
        """Open an ISO file"""
        file_path = filedialog.askopenfilename(
            title="Open ISO File",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.load_iso(file_path)
                self.update_status(f"Loaded ISO: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ISO: {str(e)}")
                self.update_status("Error loading ISO")

    def load_iso(self, file_path):
        """Load and parse ISO file using streaming."""
        self.close_iso() # Close any existing file
        self.current_iso_path = file_path

        self.iso_file_handle = open(file_path, 'rb')
        self.iso_data = None # Ensure old data is cleared

        # Parse ISO 9660 structure
        self.parse_iso_structure()
        self.update_iso_info()
        self.populate_file_tree()

    def parse_iso_structure(self):
        """Parse ISO 9660 file system structure, looking for PVD and Joliet SVD."""
        pvd = None
        joliet_svd = None
        self.is_joliet = False

        lba = 16
        while True:
            offset = lba * 2048
            self.iso_file_handle.seek(offset)
            vd = self.iso_file_handle.read(2048)
            if len(vd) < 2048:
                break

            vd_type = vd[0]

            if vd[1:6] != b'CD001':
                break

            if vd_type == 1:
                pvd = vd
            elif vd_type == 2:
                escape_seq = vd[88:120]
                if b'%/@' in escape_seq or b'%/C' in escape_seq or b'%/E' in escape_seq:
                    joliet_svd = vd
            elif vd_type == 255:
                break

            lba += 1

        pvd_data = joliet_svd if joliet_svd is not None else pvd
        if pvd_data is None:
            raise ValueError("No valid Primary or Joliet Volume Descriptor found.")

        if joliet_svd is not None:
            self.is_joliet = True
            print("Joliet SVD found. Using Joliet names.")

        id_encoding = 'utf-16-be' if self.is_joliet else 'ascii'

        self.volume_descriptor = {
            'system_id': pvd_data[8:40].decode(id_encoding, errors='ignore').strip('\x00'),
            'volume_id': pvd_data[40:72].decode(id_encoding, errors='ignore').strip('\x00'),
            'volume_size': struct.unpack('<L', pvd_data[80:84])[0],
            'volume_set_size': struct.unpack('<H', pvd_data[120:122])[0],
            'volume_sequence_number': struct.unpack('<H', pvd_data[124:126])[0],
            'logical_block_size': struct.unpack('<H', pvd_data[128:130])[0],
            'path_table_size': struct.unpack('<L', pvd_data[132:136])[0],
            'root_dir_record': pvd_data[156:190]
        }

        self.root_directory = self.parse_directory_record(self.volume_descriptor['root_dir_record'])

        # Build complete directory tree
        self.directory_tree = self.build_directory_tree()

        # Calculate next available extent location for new files
        self.calculate_next_extent_location()

    def _parse_susp_entries(self, system_use_data):
        """Parse SUSP and Rock Ridge entries from the System Use Area."""
        entries = {}
        i = 0
        while i < len(system_use_data) - 4:
            try:
                signature = system_use_data[i:i+2]
                length = system_use_data[i+2]
                version = system_use_data[i+3]

                if length == 0: break

                data = system_use_data[i+4:i+length]

                if signature == b'NM':
                    entries['name'] = data.decode('ascii', 'ignore')
                elif signature == b'PX':
                    entries['posix'] = data
                elif signature == b'SL':
                    link_parts = []
                    j = 0
                    while j < len(data):
                        flags = data[j]
                        j += 1
                        component_len = data[j]
                        j += 1
                        component = data[j:j+component_len].decode('ascii', 'ignore')
                        if component == '.': pass # Current dir, do nothing
                        elif component == '..':
                            if link_parts: link_parts.pop()
                        elif component:
                            link_parts.append(component)
                        j += component_len
                    entries['symlink'] = '/'.join(link_parts)
                elif signature == b'TF':
                    entries['timestamps'] = data
                elif signature == b'SP':
                    if data == b'\xbe\xef': entries['susp_present'] = True

                i += length
            except Exception:
                # Malformed entry, stop parsing this area
                break

        return entries

    def parse_directory_record(self, record_data):
        """Parse a directory record"""
        if len(record_data) < 33:
            return None

        record_length = record_data[0]
        if record_length == 0:
            return None

        # Extract directory record fields
        extent_location = struct.unpack('<L', record_data[2:6])[0]
        data_length = struct.unpack('<L', record_data[10:14])[0]

        # Recording date (7 bytes)
        recording_date = record_data[18:25]

        # File flags
        file_flags = record_data[25]
        is_directory = bool(file_flags & 0x02)
        is_hidden = bool(file_flags & 0x01)

        # File identifier length and name
        file_id_length = record_data[32]
        file_id_bytes = record_data[33:33 + file_id_length]

        # System Use Area starts after the file identifier and optional padding
        system_use_offset = 33 + file_id_length
        if file_id_length % 2 == 0:
            system_use_offset += 1
        system_use_data = record_data[system_use_offset:]

        # Parse Rock Ridge extensions
        rr_entries = self._parse_susp_entries(system_use_data)

        # Decode filename based on volume type (Joliet or standard)
        if self.is_joliet:
            if file_id_bytes == b'\x00':
                file_id = '.'
            elif file_id_bytes == b'\x01':
                file_id = '..'
            else:
                file_id = file_id_bytes.decode('utf-16-be', 'ignore')
        else:
            file_id = file_id_bytes.decode('ascii', 'ignore')

        # Rock Ridge 'NM' entry overrides the standard filename
        if 'name' in rr_entries:
            file_id = rr_entries['name']

        # Parse recording date
        date_str = "Unknown"
        if recording_date[0] > 0:  # Year since 1900
            try:
                year = recording_date[0] + 1900
                month = recording_date[1]
                day = recording_date[2]
                hour = recording_date[3]
                minute = recording_date[4]
                second = recording_date[5]
                date_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            except:
                date_str = "Invalid Date"

        return {
            'extent_location': extent_location,
            'data_length': data_length,
            'is_directory': is_directory,
            'is_hidden': is_hidden,
            'file_id': file_id,
            'record_length': record_length,
            'recording_date': date_str,
            'raw_data': record_data
        }

    def build_directory_tree(self):
        """Build complete directory tree from ISO"""
        if not self.root_directory:
            return {}

        tree = {'name': '/', 'is_directory': True, 'children': [], 'parent': None}

        # Parse root directory contents
        root_entries = self.read_directory_entries(self.root_directory['extent_location'])

        for entry in root_entries:
            if entry['file_id'] in ['.', '..']:
                continue

            node = {
                'name': entry['file_id'],
                'is_directory': entry['is_directory'],
                'is_hidden': entry['is_hidden'],
                'size': entry['data_length'],
                'date': entry['recording_date'],
                'extent_location': entry['extent_location'],
                'children': [],
                'parent': tree
            }

            if entry['is_directory']:
                # Recursively build subdirectories
                self.build_directory_subtree(node)

            tree['children'].append(node)

        return tree

    def build_directory_subtree(self, parent_node):
        """Recursively build subdirectory tree"""
        try:
            entries = self.read_directory_entries(parent_node['extent_location'])

            for entry in entries:
                if entry['file_id'] in ['.', '..']:
                    continue

                node = {
                    'name': entry['file_id'],
                    'is_directory': entry['is_directory'],
                    'is_hidden': entry['is_hidden'],
                    'size': entry['data_length'],
                    'date': entry['recording_date'],
                    'extent_location': entry['extent_location'],
                    'children': [],
                    'parent': parent_node
                }

                if entry['is_directory'] and len(parent_node['name']) < 50:  # Prevent infinite recursion
                    self.build_directory_subtree(node)

                parent_node['children'].append(node)

        except Exception as e:
            print(f"Error building subtree for {parent_node['name']}: {e}")

    def read_directory_entries(self, extent_location):
        """Read all entries from a directory using file streaming."""
        entries = []
        if not self.iso_file_handle:
            return entries

        block_size = self.volume_descriptor['logical_block_size']
        offset = extent_location * block_size

        try:
            self.iso_file_handle.seek(offset)
            directory_data = self.iso_file_handle.read(block_size)
        except (IOError, ValueError):
            return entries # Failed to seek/read

        # Parse directory records
        pos = 0
        while pos < len(directory_data):
            if pos >= len(directory_data) or directory_data[pos] == 0:
                break

            record_length = directory_data[pos]
            if record_length == 0:
                break

            if pos + record_length > len(directory_data):
                break

            record_data = directory_data[pos:pos + record_length]
            entry = self.parse_directory_record(record_data)

            if entry:
                entries.append(entry)

            pos += record_length

        return entries

    def format_file_size(self, size):
        """Format file size in human readable format"""
        if size == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def update_iso_info(self):
        """Update the ISO information display"""
        if not self.volume_descriptor:
            return

        info_text = f"System ID: {self.volume_descriptor['system_id']}\n"
        info_text += f"Volume ID: {self.volume_descriptor['volume_id']}\n"
        info_text += f"Volume Size: {self.volume_descriptor['volume_size']} blocks\n"
        info_text += f"Block Size: {self.volume_descriptor['logical_block_size']} bytes\n"
        info_text += f"Total Size: {self.volume_descriptor['volume_size'] * self.volume_descriptor['logical_block_size'] / 1024 / 1024:.1f} MB\n"
        info_text += f"Path Table Size: {self.volume_descriptor['path_table_size']} bytes\n"

        self.iso_info.delete(1.0, tk.END)
        self.iso_info.insert(1.0, info_text)

        # Update volume name entry
        self.volume_name_var.set(self.volume_descriptor['volume_id'])

    def populate_file_tree(self):
        """Populate the file tree view with actual ISO contents"""
        # Clear existing items
        self.tree.delete(*self.tree.get_children())

        if not hasattr(self, 'directory_tree') or not self.directory_tree:
            return

        # Add root directory
        root_item = self.tree.insert('', 'end', text='/', values=('Directory', '', ''))
        self.tree.set(root_item, 'Size', 'Directory')
        self.tree.set(root_item, 'Date', '')
        self.tree.set(root_item, 'Type', 'Directory')

        # Store reference to tree node in item
        self.tree_item_map = {root_item: self.directory_tree}

        # Populate root directory contents
        self.populate_tree_node(root_item, self.directory_tree)

        # Expand root directory
        self.tree.item(root_item, open=True)

    def populate_tree_node(self, tree_item, node):
        """Populate a tree node with its children"""
        for child in node['children']:
            # Skip hidden files unless shown
            if child['is_hidden'] and not getattr(self, 'show_hidden', False):
                continue

            # Format size
            size_text = self.format_file_size(child['size']) if not child['is_directory'] else ''
            file_type = 'Directory' if child['is_directory'] else 'File'

            # Mark new/modified items
            display_name = child['name']
            if child.get('is_new', False):
                display_name += " [NEW]"
            elif child.get('is_modified', False):
                display_name += " [MODIFIED]"

            # Add tree item
            child_item = self.tree.insert(tree_item, 'end', text=display_name)
            self.tree.set(child_item, 'Size', size_text)
            self.tree.set(child_item, 'Date', child['date'])
            self.tree.set(child_item, 'Type', file_type)

            # Store reference
            self.tree_item_map[child_item] = child

            # Add children if directory
            if child['is_directory'] and child['children']:
                self.populate_tree_node(child_item, child)

    def get_selected_node(self):
        """Get the selected tree node data"""
        selection = self.tree.selection()
        if not selection:
            return None

        item = selection[0]
        return self.tree_item_map.get(item)

    def get_node_path(self, node):
        """Get full path of a node"""
        path_parts = []
        current = node

        while current and current['parent']:
            path_parts.append(current['name'])
            current = current['parent']

        path_parts.reverse()
        return '/' + '/'.join(path_parts) if path_parts else '/'

    def _perform_save(self, file_path):
        """Core logic to build and save the ISO to a given path."""
        if not self.directory_tree:
            messagebox.showwarning("Empty ISO", "Cannot save an empty or uninitialized ISO.")
            return

        try:
            self.update_status("Building ISO, please wait...")
            self.root.update_idletasks()

            builder = ISOBuilder(self.directory_tree, file_path, self.volume_descriptor.get('volume_id', 'TK_ISO_VOL'), use_joliet=True, use_rock_ridge=True)
            builder.build()

            self.current_iso_path = file_path
            self.iso_modified = False
            self.root.title(f"ISO Editor - {os.path.basename(self.current_iso_path)}")
            self.update_status(f"Successfully saved to {os.path.basename(file_path)}")
            messagebox.showinfo("Success", "ISO file has been saved successfully.")

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error Saving ISO", f"An error occurred while saving the ISO:\n{str(e)}")
            self.update_status("Error saving ISO.")

    def new_iso(self):
        """Create a new, empty ISO in memory"""
        if self.iso_modified:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Would you like to save them before creating a new ISO?")
            if response is True:  # Yes
                self.save_iso()
                if self.iso_modified:  # Check if save was cancelled
                    return
            elif response is None:  # Cancel
                return

        # Reset state
        self.current_iso_path = None
        self.iso_data = b''  # Empty data
        self.iso_modified = False
        self.tree_item_map = {}

        # Create default structures
        self.volume_descriptor = {
            'system_id': 'TK_ISO_EDITOR',
            'volume_id': 'NEW_ISO',
            'volume_size': 0,
            'logical_block_size': 2048,
            'path_table_size': 0,
            'root_dir_record': b''
        }

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.directory_tree = {
            'name': '/',
            'is_directory': True,
            'is_hidden': False,
            'size': 0,
            'date': now_str,
            'extent_location': 0,
            'children': [],
            'parent': None
        }
        # The root directory's parent is itself in the tree structure logic
        self.directory_tree['parent'] = self.directory_tree

        self.root_directory = self.directory_tree  # For consistency

        # Update GUI
        self.root.title("ISO Editor - New ISO")
        self.update_iso_info()
        self.populate_file_tree()
        self.update_status("Created new empty ISO.")

    def save_iso(self):
        """Save current ISO"""
        if not self.current_iso_path:
            self.save_iso_as()
        else:
            self._perform_save(self.current_iso_path)

    def save_iso_as(self):
        """Save ISO with new name"""
        file_path = filedialog.asksaveasfilename(
            title="Save ISO As",
            defaultextension=".iso",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
        )

        if file_path:
            self._perform_save(file_path)

    def update_volume_name(self, event=None):
        """Update the volume name"""
        new_name = self.volume_name_var.get()
        if self.volume_descriptor:
            self.volume_descriptor['volume_id'] = new_name
            self.update_iso_info()
            self.update_status(f"Volume name updated to: {new_name}")

    def show_iso_properties(self):
        """Show ISO properties dialog"""
        if not self.volume_descriptor:
            messagebox.showwarning("No ISO", "No ISO file loaded")
            return

        # Create properties dialog
        props_window = tk.Toplevel(self.root)
        props_window.title("ISO Properties")
        props_window.geometry("400x300")
        props_window.grab_set()

        # Add property fields
        ttk.Label(props_window, text="Volume Properties", font=('Arial', 12, 'bold')).pack(pady=10)

        # Volume ID
        frame = ttk.Frame(props_window)
        frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frame, text="Volume ID:").pack(side=tk.LEFT)
        vol_id_var = tk.StringVar(value=self.volume_descriptor['volume_id'])
        ttk.Entry(frame, textvariable=vol_id_var).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # System ID
        frame = ttk.Frame(props_window)
        frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frame, text="System ID:").pack(side=tk.LEFT)
        sys_id_var = tk.StringVar(value=self.volume_descriptor['system_id'])
        ttk.Entry(frame, textvariable=sys_id_var).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Buttons
        button_frame = ttk.Frame(props_window)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        def apply_changes():
            self.volume_descriptor['volume_id'] = vol_id_var.get()
            self.volume_descriptor['system_id'] = sys_id_var.get()
            self.update_iso_info()
            props_window.destroy()

        ttk.Button(button_frame, text="Apply", command=apply_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=props_window.destroy).pack(side=tk.RIGHT)

    def calculate_next_extent_location(self):
        """Calculate the next available extent location for new files"""
        max_extent = 0

        def find_max_extent(node):
            nonlocal max_extent
            if node['extent_location'] > max_extent:
                max_extent = node['extent_location']
            for child in node.get('children', []):
                find_max_extent(child)

        if self.directory_tree:
            find_max_extent(self.directory_tree)

        # Add some padding for safety
        self.next_extent_location = max_extent + 10

    def add_file(self):
        """Add file to ISO"""
        # Get target directory
        selected_node = self.get_selected_node()
        if not selected_node:
            target_node = self.directory_tree  # Add to root
        elif selected_node['is_directory']:
            target_node = selected_node
        else:
            target_node = selected_node['parent']  # Add to parent directory

        # Choose files to add
        file_paths = filedialog.askopenfilenames(
            title="Select files to add to ISO",
            filetypes=[("All files", "*.*")]
        )

        if not file_paths:
            return

        try:
            for file_path in file_paths:
                self.add_file_to_directory(file_path, target_node)

            self.mark_modified()
            self.populate_file_tree()
            self.update_status(f"Added {len(file_paths)} file(s)")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add files: {str(e)}")

    def add_file_to_directory(self, file_path, target_node):
        """Add a single file to a directory node"""
        filename = os.path.basename(file_path)

        # Check if file already exists
        for child in target_node['children']:
            if child['name'].lower() == filename.lower():
                if not messagebox.askyesno("File Exists",
                    f"File '{filename}' already exists. Replace it?"):
                    return
                # Remove existing file
                target_node['children'].remove(child)
                break

        # Read file data
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Get file stats
        file_stats = os.stat(file_path)
        file_date = datetime.fromtimestamp(file_stats.st_mtime)

        # Create new file node
        new_node = {
            'name': filename,
            'is_directory': False,
            'is_hidden': False,
            'size': len(file_data),
            'date': file_date.strftime("%Y-%m-%d %H:%M:%S"),
            'extent_location': self.next_extent_location,
            'children': [],
            'parent': target_node,
            'file_data': file_data,  # Store actual file data
            'is_new': True  # Mark as new file
        }

        target_node['children'].append(new_node)
        self.next_extent_location += (len(file_data) + 2047) // 2048  # Round up to blocks

    def add_folder(self):
        """Add folder to ISO"""
        # Get target directory
        selected_node = self.get_selected_node()
        if not selected_node:
            target_node = self.directory_tree  # Add to root
        elif selected_node['is_directory']:
            target_node = selected_node
        else:
            target_node = selected_node['parent']  # Add to parent directory

        # Get folder name
        folder_name = tk.simpledialog.askstring(
            "New Folder",
            "Enter folder name:",
            parent=self.root
        )

        if not folder_name:
            return

        # Validate folder name
        if not self.validate_filename(folder_name):
            messagebox.showerror("Invalid Name",
                "Folder name contains invalid characters")
            return

        # Check if folder already exists
        for child in target_node['children']:
            if child['name'].lower() == folder_name.lower():
                messagebox.showerror("Folder Exists",
                    f"Folder '{folder_name}' already exists")
                return

        try:
            self.add_folder_to_directory(folder_name, target_node)
            self.mark_modified()
            self.populate_file_tree()
            self.update_status(f"Added folder '{folder_name}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add folder: {str(e)}")

    def add_folder_to_directory(self, folder_name, target_node):
        """Add a new folder to a directory node"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create new folder node
        new_node = {
            'name': folder_name,
            'is_directory': True,
            'is_hidden': False,
            'size': 0,
            'date': current_time,
            'extent_location': self.next_extent_location,
            'children': [],
            'parent': target_node,
            'is_new': True  # Mark as new folder
        }

        target_node['children'].append(new_node)
        self.next_extent_location += 1  # One block for directory

    def remove_selected(self):
        """Remove selected item"""
        selected_node = self.get_selected_node()
        if not selected_node:
            messagebox.showwarning("No Selection", "Please select a file or folder to remove")
            return

        # Don't allow removing root directory
        if selected_node == self.directory_tree:
            messagebox.showwarning("Cannot Remove", "Cannot remove root directory")
            return

        # Confirm deletion
        item_type = "folder" if selected_node['is_directory'] else "file"
        if not messagebox.askyesno("Confirm Removal",
            f"Are you sure you want to remove {item_type} '{selected_node['name']}'?"):
            return

        try:
            self.remove_node(selected_node)
            self.mark_modified()
            self.populate_file_tree()
            self.update_status(f"Removed {item_type} '{selected_node['name']}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove {item_type}: {str(e)}")

    def remove_node(self, node):
        """Remove a node from the directory tree"""
        if node['parent']:
            node['parent']['children'].remove(node)

    def validate_filename(self, filename):
        """Validate filename for ISO compatibility"""
        # Basic ISO 9660 filename validation
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        return not any(char in filename for char in invalid_chars)

    def import_directory(self):
        """Import entire directory structure"""
        # Get target directory
        selected_node = self.get_selected_node()
        if not selected_node:
            target_node = self.directory_tree  # Add to root
        elif selected_node['is_directory']:
            target_node = selected_node
        else:
            target_node = selected_node['parent']  # Add to parent directory

        # Choose directory to import
        source_dir = filedialog.askdirectory(
            title="Select directory to import"
        )

        if not source_dir:
            return

        try:
            self.import_directory_recursive(source_dir, target_node)
            self.mark_modified()
            self.populate_file_tree()
            self.update_status(f"Imported directory '{os.path.basename(source_dir)}'")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import directory: {str(e)}")

    def import_directory_recursive(self, source_path, target_node):
        """Recursively import directory structure"""
        dir_name = os.path.basename(source_path)

        # Create directory node
        self.add_folder_to_directory(dir_name, target_node)
        new_dir_node = target_node['children'][-1]  # Get the just-added directory

        # Import all contents
        for item in os.listdir(source_path):
            item_path = os.path.join(source_path, item)

            if os.path.isfile(item_path):
                self.add_file_to_directory(item_path, new_dir_node)
            elif os.path.isdir(item_path):
                self.import_directory_recursive(item_path, new_dir_node)

    def extract_selected(self):
        """Extract selected item"""
        selected_node = self.get_selected_node()
        if not selected_node:
            messagebox.showwarning("No Selection", "Please select a file or folder to extract")
            return

        # Choose extraction location
        if selected_node['is_directory']:
            extract_path = filedialog.askdirectory(title="Choose extraction location")
            if extract_path:
                extract_path = os.path.join(extract_path, selected_node['name'])
        else:
            extract_path = filedialog.asksaveasfilename(
                title="Save extracted file as",
                initialname=selected_node['name']
            )

        if extract_path:
            try:
                self.extract_node(selected_node, extract_path)
                self.update_status(f"Extracted {selected_node['name']} to {extract_path}")
                messagebox.showinfo("Success", f"Successfully extracted {selected_node['name']}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract: {str(e)}")

    def on_tree_double_click(self, event):
        """Handle double-click on tree item"""
        selected_node = self.get_selected_node()
        if not selected_node:
            return

        if selected_node['is_directory']:
            # Toggle directory expansion
            item = self.tree.selection()[0]
            if self.tree.item(item, 'open'):
                self.tree.item(item, open=False)
            else:
                self.tree.item(item, open=True)
        else:
            # For files, show file info
            self.show_file_info(selected_node)

    def show_file_info(self, node):
        """Show detailed file information"""
        path = self.get_node_path(node)

        info_window = tk.Toplevel(self.root)
        info_window.title(f"File Information - {node['name']}")
        info_window.geometry("400x300")
        info_window.grab_set()

        # File information
        info_text = f"Name: {node['name']}\n"
        info_text += f"Path: {path}\n"
        info_text += f"Size: {self.format_file_size(node['size'])}\n"
        info_text += f"Date: {node['date']}\n"
        info_text += f"Type: {'Directory' if node['is_directory'] else 'File'}\n"
        info_text += f"Hidden: {'Yes' if node['is_hidden'] else 'No'}\n"
        info_text += f"Extent Location: {node['extent_location']}\n"

        text_widget = tk.Text(info_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, info_text)
        text_widget.config(state=tk.DISABLED)

        # Close button
        ttk.Button(info_window, text="Close",
                  command=info_window.destroy).pack(pady=10)

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Get the item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

        selected_node = self.get_selected_node()

        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)

        if selected_node:
            context_menu.add_command(label=f"Properties of {selected_node['name']}",
                                   command=lambda: self.show_file_info(selected_node))
            context_menu.add_separator()

            if selected_node['is_directory']:
                context_menu.add_command(label="Add File to Folder...", command=self.add_file)
                context_menu.add_command(label="Add Subfolder...", command=self.add_folder)
                context_menu.add_command(label="Import Directory...", command=self.import_directory)
            else:
                context_menu.add_command(label="Extract File...", command=self.extract_selected)

            context_menu.add_separator()
            context_menu.add_command(label="Remove", command=self.remove_selected)
        else:
            context_menu.add_command(label="Add File...", command=self.add_file)
            context_menu.add_command(label="Add Folder...", command=self.add_folder)
            context_menu.add_command(label="Import Directory...", command=self.import_directory)

        context_menu.add_separator()
        context_menu.add_command(label="Refresh", command=self.refresh_view)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def refresh_view(self):
        """Refresh the file tree view"""
        if self.current_iso_path:
            # Reload the ISO to refresh
            try:
                self.load_iso(self.current_iso_path)
                self.update_status("View refreshed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to refresh: {str(e)}")
        else:
            self.update_status("No ISO loaded")

    def toggle_hidden_files(self):
        """Toggle display of hidden files"""
        self.show_hidden = not self.show_hidden
        self.populate_file_tree()

        status = "shown" if self.show_hidden else "hidden"
        self.update_status(f"Hidden files {status}")

    def extract_selected(self):
        """Extract selected file or folder"""
        selected_node = self.get_selected_node()
        if not selected_node:
            messagebox.showwarning("No Selection", "Please select a file or folder to extract")
            return

        # Choose extraction location
        if selected_node['is_directory']:
            extract_path = filedialog.askdirectory(title="Choose extraction location")
        else:
            extract_path = filedialog.asksaveasfilename(
                title="Save extracted file as",
                initialname=selected_node['name']
            )

        if extract_path:
            try:
                self.extract_node(selected_node, extract_path)
                self.update_status(f"Extracted {selected_node['name']} to {extract_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract: {str(e)}")

    def extract_node(self, node, extract_path):
        """Extract a node (file or directory) to local filesystem"""
        if node['is_directory']:
            # Create directory and extract all contents
            os.makedirs(extract_path, exist_ok=True)

            for child in node['children']:
                child_path = os.path.join(extract_path, child['name'])
                self.extract_node(child, child_path)
        else:
            # Extract file
            file_data = self.get_file_data(node)

            # Ensure directory exists
            os.makedirs(os.path.dirname(extract_path), exist_ok=True)

            with open(extract_path, 'wb') as f:
                f.write(file_data)

    def get_file_data(self, node):
        """Get file data from ISO or new file data"""
        if node['is_directory']:
            return b''

        # If it's a new file, return stored data
        if node.get('is_new', False) and 'file_data' in node:
            return node['file_data']

        # Otherwise, read from original ISO using the file handle
        if not self.iso_file_handle:
            return b''

        block_size = self.volume_descriptor['logical_block_size']
        offset = node['extent_location'] * block_size
        size = node['size']

        try:
            self.iso_file_handle.seek(offset)
            return self.iso_file_handle.read(size)
        except (IOError, ValueError):
            messagebox.showerror("Read Error", f"Failed to read data for file '{node['name']}'.")
            return b''

# ==============================================================================
# ISO 9660 Building Logic
# ==============================================================================

def _pack_both_endian_16(n):
    return struct.pack('<H', n) + struct.pack('>H', n)

def _pack_both_endian_32(n):
    return struct.pack('<L', n) + struct.pack('>L', n)

def _format_pvd_date(dt=None):
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y%m%d%H%M%S00').encode('ascii') + b'\x00'

def _format_dir_date(dt=None):
    if dt is None:
        dt = datetime.now()
    # Zone is offset from GMT in 15min intervals. 0 = GMT.
    return struct.pack('BBBBBBb', dt.year - 1900, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0)

def _format_str_d(s, length):
    s = s.upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    s = ''.join(c for c in s if c in allowed)
    return s.ljust(length, ' ').encode('ascii')

def _format_str_a(s, length):
    # This is a simplified version. The spec is more complex.
    s = s.upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_!\"%&'()*+,-./:;<=>?"
    s = ''.join(c for c in s if c in allowed)
    return s.ljust(length, ' ').encode('ascii')

class ISOBuilder:
    def __init__(self, root_node, output_path, volume_id="TK_ISO_VOL", use_joliet=True, use_rock_ridge=True):
        self.root_node = root_node
        self.output_path = output_path
        self.volume_id = volume_id
        self.use_joliet = use_joliet
        self.use_rock_ridge = use_rock_ridge
        self.logical_block_size = 2048
        self.next_lba = 0
        self.temp_file = None

    def build(self):
        """Main method to build the ISO by writing to a temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        try:
            # Reserve space for system area by seeking past it
            self.temp_file.seek(16 * self.logical_block_size)
            self.next_lba = 16

            pvd_lba = self.next_lba; self.next_lba += 1
            svd_lba = self.next_lba if self.use_joliet else 0; self.next_lba += (1 if self.use_joliet else 0)
            terminator_lba = self.next_lba; self.next_lba += 1

            # Layout pass for PVD to place files and get their LBAs
            pvd_path_records, file_map = self._layout_hierarchy(is_joliet=False)

            # Write PVD hierarchy
            pvd_l_path, pvd_m_path = self._generate_path_tables(pvd_path_records, False)
            pvd_l_path_lba = self._write_data_block(pvd_l_path)
            pvd_m_path_lba = self._write_data_block(pvd_m_path)
            self._write_directory_records_recursively(self.root_node, False)

            # Write SVD (Joliet) hierarchy
            if self.use_joliet:
                svd_path_records, _ = self._layout_hierarchy(is_joliet=True, file_map=file_map)
                svd_l_path, svd_m_path = self._generate_path_tables(svd_path_records, True)
                svd_l_path_lba = self._write_data_block(svd_l_path)
                svd_m_path_lba = self._write_data_block(svd_m_path)
                self._write_directory_records_recursively(self.root_node, True)

            volume_size_in_blocks = self.next_lba

            # Write volume descriptors now that we have all locations
            pvd_data = self._generate_pvd(volume_size_in_blocks, pvd_l_path_lba, pvd_m_path_lba, len(pvd_l_path), False)
            self._write_data_at_lba(pvd_lba, pvd_data)

            if self.use_joliet:
                svd_data = self._generate_pvd(volume_size_in_blocks, svd_l_path_lba, svd_m_path_lba, len(svd_l_path), True)
                self._write_data_at_lba(svd_lba, svd_data)

            terminator_data = self._generate_terminator()
            self._write_data_at_lba(terminator_lba, terminator_data)

        finally:
            if self.temp_file:
                self.temp_file.close()
                shutil.move(self.temp_file.name, self.output_path)

    def _write_data_at_lba(self, lba, data):
        self.temp_file.seek(lba * self.logical_block_size)
        self.temp_file.write(data)

    def _write_data_block(self, data):
        """Writes data to the next available LBA and returns the LBA."""
        lba = self.next_lba
        self._write_data_at_lba(lba, data)
        self.next_lba += math.ceil(len(data) / self.logical_block_size) if data else 1
        return lba

    def _get_short_name(self, name):
        """Generates an ISO 9660 compliant 8.3 filename."""
        name = name.upper()
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        name = ''.join(c for c in name if c in allowed_chars)
        parts = name.split('.')
        if len(parts) > 1 and parts[-1]:
            base = ''.join(parts[:-1])
            ext = parts[-1]
            return base[:8] + '.' + ext[:3]
        else:
            return name[:11].split('.')[0][:8]

    def _layout_hierarchy(self, is_joliet, file_map=None):
        path_table_records = []
        if file_map is None: file_map = {}

        def _recursive_layout(node, parent_dir_num):
            dir_num = len(path_table_records) + 1
            path_table_records.append({'node': node, 'parent_dir_num': parent_dir_num})

            for child in sorted(node['children'], key=lambda x: x['name']):
                if child['is_directory']:
                    _recursive_layout(child, dir_num)

            if not is_joliet:
                for child in sorted(node['children'], key=lambda x: x['name']):
                    if not child['is_directory']:
                        child_id = id(child)
                        if child_id not in file_map:
                            file_data = child.get('file_data', b'')
                            child['extent_location'] = self._write_data_block(file_data)
                            file_map[child_id] = child['extent_location']
                        else:
                            child['extent_location'] = file_map[child_id]
            else:
                 for child in sorted(node['children'], key=lambda x: x['name']):
                    if not child['is_directory']:
                        child['extent_location'] = file_map[id(child)]

            dir_records_data = self._generate_directory_records_for_node(node, is_joliet)
            data_len_key = 'joliet_data_length' if is_joliet else 'pvd_data_length'
            extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'
            node[data_len_key] = len(dir_records_data)
            node[extent_loc_key] = self._write_data_block(b'\x00' * node[data_len_key]) # Reserve space

        _recursive_layout(self.root_node, 1)
        return path_table_records, file_map

    def _generate_path_tables(self, path_table_records, is_joliet):
        path_table_records.sort(key=lambda r: self.get_node_path(r['node']))
        dir_num_map = {self.get_node_path(r['node']): i + 1 for i, r in enumerate(path_table_records)}

        l_table, m_table = bytearray(), bytearray()
        for record in path_table_records:
            node = record['node']
            path = self.get_node_path(node)
            parent_path = os.path.dirname(path).replace('\\', '/') if path != '/' else '/'
            parent_dir_num = dir_num_map.get(parent_path, 1)
            extent_loc = node['joliet_extent_location' if is_joliet else 'pvd_extent_location']
            name = self._get_short_name(node['name']) if not is_joliet else node['name']

            dir_id = b'\x00' if name == '/' else name.encode('utf-16-be' if is_joliet else 'ascii')
            id_len = len(dir_id)

            l_rec = struct.pack('<BB<L<H', id_len, 0, extent_loc, parent_dir_num) + dir_id
            if id_len % 2 != 0: l_rec += b'\x00'
            l_table.extend(l_rec)
            m_rec = struct.pack('<BB>L>H', id_len, 0, extent_loc, parent_dir_num) + dir_id
            if id_len % 2 != 0: m_rec += b'\x00'
            m_table.extend(m_rec)
        return bytes(l_table), bytes(m_table)

    def _write_directory_records_recursively(self, node, is_joliet):
        records_data = self._generate_directory_records_for_node(node, is_joliet)
        extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'
        self._write_data_at_lba(node[extent_loc_key], records_data)
        for child in node['children']:
            if child['is_directory']:
                self._write_directory_records_recursively(child, is_joliet)

    def _generate_directory_records_for_node(self, node, is_joliet):
        all_records = bytearray()
        all_records.extend(self._create_dir_record(node, is_joliet, is_self=True))
        all_records.extend(self._create_dir_record(node.get('parent', node), is_joliet, is_parent=True))
        for child in sorted(node['children'], key=lambda x: x['name']):
            all_records.extend(self._create_dir_record(child, is_joliet))
        return bytes(all_records)

    def _create_dir_record(self, node, is_joliet, is_self=False, is_parent=False):
        file_flags = 0x02 if node.get('is_directory') else 0
        if node.get('is_hidden', False): file_flags |= 0x01

        extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'
        data_len_key = 'joliet_data_length' if is_joliet else 'pvd_data_length'

        extent_loc = node.get(extent_loc_key, node.get('extent_location', 0))
        data_len = node.get(data_len_key, 0) if node.get('is_directory') else node.get('size', 0)

        system_use_data = b''

        if is_self: file_id_bytes = b'\x00'
        elif is_parent: file_id_bytes = b'\x01'
        else:
            if is_joliet:
                file_id_bytes = node['name'].encode('utf-16-be')
            else:
                short_name = self._get_short_name(node['name'])
                if not node['is_directory']: short_name += ';1'
                file_id_bytes = short_name.encode('ascii')
                if self.use_rock_ridge and node['name'].upper() != short_name.split(';')[0]:
                    nm_data = node['name'].encode('ascii', 'ignore')
                    system_use_data += b'NM' + struct.pack('<BB', len(nm_data) + 5, 1) + nm_data

        file_id_len = len(file_id_bytes)
        record_len = 33 + file_id_len + len(system_use_data)
        if record_len % 2 != 0: record_len += 1

        rec = bytearray(record_len)
        struct.pack_into('<B', rec, 0, record_len)
        rec[2:10] = _pack_both_endian_32(extent_loc)
        rec[10:18] = _pack_both_endian_32(data_len)
        rec[18:25] = _format_dir_date(datetime.strptime(node['date'], "%Y-%m-%d %H:%M:%S") if node.get('date') else datetime.now())
        struct.pack_into('<B', rec, 25, file_flags)
        rec[28:32] = _pack_both_endian_16(1)
        struct.pack_into('<B', rec, 32, file_id_len)
        rec[33:33 + file_id_len] = file_id_bytes
        if system_use_data:
            offset = 33 + file_id_len
            if file_id_len % 2 == 0: offset += 1
            rec[offset:offset+len(system_use_data)] = system_use_data
        return bytes(rec)

    def _generate_pvd(self, volume_size, lba_l, lba_m, path_table_size, is_joliet=False):
        vd = bytearray(self.logical_block_size)
        vd_type = 2 if is_joliet else 1
        encoding = 'utf-16-be' if is_joliet else 'ascii'
        root_record_data = self._create_dir_record(self.root_node, is_joliet, is_self=True)
        vd[0:1] = struct.pack('B', vd_type)
        vd[1:6] = b'CD001'; vd[6:7] = b'\x01'
        if is_joliet: vd[88:91] = b'%/@'
        vd[8:40] = _format_str_a("PYTHON TK ISO EDITOR", 32)
        vd[40:72] = self.volume_id.encode(encoding, 'ignore').ljust(32, b'\x00' if is_joliet else b' ')
        vd[80:88] = _pack_both_endian_32(volume_size)
        vd[120:124] = _pack_both_endian_16(1)
        vd[124:128] = _pack_both_endian_16(1)
        vd[128:132] = _pack_both_endian_16(self.logical_block_size)
        vd[132:140] = _pack_both_endian_32(path_table_size)
        vd[140:144] = struct.pack('<L', lba_l)
        vd[148:152] = struct.pack('>L', lba_m)
        vd[156:190] = root_record_data[:34]
        vd[190:318] = "ISO_SET".encode(encoding, 'ignore').ljust(128, b'\x00' if is_joliet else b' ')
        vd[881:882] = b'\x01'
        return vd

    def _generate_terminator(self):
        terminator = bytearray(self.logical_block_size)
        terminator[0:1] = b'\xff'; terminator[1:6] = b'CD001'; terminator[6:7] = b'\x01'
        return terminator

    def get_node_path(self, node):
        if not node.get('parent'): return '/'
        path_parts = []
        current = node
        while current and current.get('parent'):
            path_parts.append(current['name'])
            current = current['parent']
        return '/' + '/'.join(reversed(path_parts))

    def _get_short_name(self, name):
        """Generates an ISO 9660 compliant 8.3 filename."""
        name = name.upper()
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        name = ''.join(c for c in name if c in allowed_chars)

        parts = name.split('.')
        if len(parts) > 1:
            base = parts[0]
            ext = parts[-1]
            return base[:8] + '.' + ext[:3]
        else:
            return name[:8]

    def _layout_hierarchy(self, is_joliet, file_map=None):
        """Lays out one directory hierarchy (either PVD or SVD)."""
        path_table_records = []
        if file_map is None:
            file_map = {} # Cache file locations to avoid duplicating data

        def _recursive_layout(node, parent_dir_num):
            dir_num = len(path_table_records) + 1
            node_id = id(node)

            if is_joliet:
                node['joliet_dir_num'] = dir_num
            else:
                node['pvd_dir_num'] = dir_num

            path_table_records.append({'node': node, 'parent_dir_num': parent_dir_num})

            # Recurse into subdirectories first
            for child in sorted(node['children'], key=lambda x: x['name']):
                if child['is_directory']:
                    _recursive_layout(child, dir_num)

            # Lay out files, only if this is the primary pass
            if not is_joliet:
                for child in sorted(node['children'], key=lambda x: x['name']):
                    if not child['is_directory']:
                        file_data = child.get('file_data', b'')
                        num_blocks = math.ceil(child['size'] / self.logical_block_size)

                        child_id = id(child)
                        if child_id not in file_map:
                            child['extent_location'] = self.next_lba
                            file_map[child_id] = self.next_lba
                            self.file_and_dir_data[self.next_lba] = file_data
                            self.next_lba += num_blocks
                        else:
                            child['extent_location'] = file_map[child_id]
            else: # For Joliet, just copy extent locations
                 for child in sorted(node['children'], key=lambda x: x['name']):
                    if not child['is_directory']:
                        child['extent_location'] = file_map[id(child)]


            # Calculate this directory's record size and assign its LBA
            dir_records_data = self._generate_directory_records_for_node(node, is_joliet)
            data_len_key = 'joliet_data_length' if is_joliet else 'pvd_data_length'
            extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'

            node[data_len_key] = len(dir_records_data)
            num_blocks = math.ceil(node[data_len_key] / self.logical_block_size)
            if num_blocks == 0: num_blocks = 1

            node[extent_loc_key] = self.next_lba
            self.next_lba += num_blocks

        _recursive_layout(self.root_node, 1)
        return path_table_records, file_map

    def _generate_path_tables(self, path_table_records, is_joliet):
        # Sort records for path table
        path_table_records.sort(key=lambda r: self.get_node_path(r['node']))

        dir_num_map = {}
        for i, record in enumerate(path_table_records):
            path = self.get_node_path(record['node'])
            dir_num_map[path] = i + 1

        l_table, m_table = bytearray(), bytearray()
        for record in path_table_records:
            node = record['node']
            path = self.get_node_path(node)
            parent_path = os.path.dirname(path).replace('\\', '/') if path != '/' else '/'
            parent_dir_num = dir_num_map.get(parent_path, 1)
            extent_loc = node['joliet_extent_location'] if is_joliet else node['pvd_extent_location']

            if node['name'] == '/':
                dir_id = b'\x00'
            else:
                dir_id = node['name'].encode('utf-16-be' if is_joliet else 'ascii')

            id_len = len(dir_id)

            l_rec = struct.pack('<BB<L<H', id_len, 0, extent_loc, parent_dir_num) + dir_id
            if id_len % 2 != 0: l_rec += b'\x00'
            l_table.extend(l_rec)

            m_rec = struct.pack('<BB>L>H', id_len, 0, extent_loc, parent_dir_num) + dir_id
            if id_len % 2 != 0: m_rec += b'\x00'
            m_table.extend(m_rec)

        return bytes(l_table), bytes(m_table)

    def _generate_all_directory_records(self, node, is_joliet):
        records_data = self._generate_directory_records_for_node(node, is_joliet)
        extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'

        padded_data = bytearray(math.ceil(len(records_data) / self.logical_block_size) * self.logical_block_size)
        padded_data[:len(records_data)] = records_data

        self.file_and_dir_data[node[extent_loc_key]] = bytes(padded_data)

        for child in node['children']:
            if child['is_directory']:
                self._generate_all_directory_records(child, is_joliet)

    def _generate_directory_records_for_node(self, node, is_joliet):
        all_records = bytearray()
        all_records.extend(self._create_dir_record(node, is_joliet, is_self=True))
        all_records.extend(self._create_dir_record(node.get('parent', node), is_joliet, is_parent=True))
        for child in sorted(node['children'], key=lambda x: x['name']):
            all_records.extend(self._create_dir_record(child, is_joliet))
        return bytes(all_records)

    def _create_dir_record(self, node, is_joliet, is_self=False, is_parent=False):
        file_flags = 0x02 if node['is_directory'] else 0
        if node.get('is_hidden', False): file_flags |= 0x01

        extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'
        data_len_key = 'joliet_data_length' if is_joliet else 'pvd_data_length'

        extent_loc = node.get(extent_loc_key, node.get('extent_location', 0))
        data_len = node[data_len_key] if node['is_directory'] else node['size']

        system_use_data = b''

        if is_self:
            file_id_bytes = b'\x00'
        elif is_parent:
            file_id_bytes = b'\x01'
        else:
            if is_joliet:
                file_id_bytes = node['name'].encode('utf-16-be')
            else:
                short_name = self._get_short_name(node['name'])
                if not node['is_directory']: short_name += ';1'
                file_id_bytes = short_name.encode('ascii')

                if self.use_rock_ridge and node['name'].upper() != short_name.split(';')[0]:
                    # Add Rock Ridge NM entry for long name
                    nm_data = node['name'].encode('ascii', 'ignore')
                    # NM entry: 'N' 'M' len ver name
                    system_use_data += b'NM' + struct.pack('<BB', len(nm_data) + 4, 1) + nm_data

        file_id_len = len(file_id_bytes)
        record_len = 33 + file_id_len + len(system_use_data)
        if record_len % 2 != 0: record_len += 1

        rec = bytearray(record_len)
        struct.pack_into('<B', rec, 0, record_len)
        struct.pack_into('<B', rec, 1, 0)
        rec[2:10] = _pack_both_endian_32(extent_loc)
        rec[10:18] = _pack_both_endian_32(data_len)
        rec[18:25] = _format_dir_date(datetime.strptime(node['date'], "%Y-%m-%d %H:%M:%S") if node.get('date') else datetime.now())
        struct.pack_into('<B', rec, 25, file_flags)
        rec[28:32] = _pack_both_endian_16(1)
        struct.pack_into('<B', rec, 32, file_id_len)
        rec[33:33 + file_id_len] = file_id_bytes
        if system_use_data:
            offset = 33 + file_id_len
            if file_id_len % 2 == 0: offset += 1
            rec[offset:offset+len(system_use_data)] = system_use_data

        return bytes(rec)

    def _generate_pvd(self, volume_size, lba_l, lba_m, path_table_size, is_joliet=False):
        vd = bytearray(self.logical_block_size)
        vd_type = 2 if is_joliet else 1
        encoding = 'utf-16-be' if is_joliet else 'ascii'

        root_record_data = self._create_dir_record(self.root_node, is_joliet, is_self=True)

        vd[0:1] = struct.pack('B', vd_type)
        vd[1:6] = b'CD001'
        vd[6:7] = b'\x01'

        if is_joliet:
            vd[88:91] = b'%/@' # Joliet escape sequence

        vd[8:40] = _format_str_a("PYTHON TK ISO EDITOR", 32)
        vd[40:72] = self.volume_id.encode(encoding, 'ignore').ljust(32, b'\x00' if is_joliet else b' ')
        vd[80:88] = _pack_both_endian_32(volume_size)
        vd[120:124] = _pack_both_endian_16(1)
        vd[124:128] = _pack_both_endian_16(1)
        vd[128:132] = _pack_both_endian_16(self.logical_block_size)
        vd[132:140] = _pack_both_endian_32(path_table_size)
        vd[140:144] = struct.pack('<L', lba_l)
        vd[148:152] = struct.pack('>L', lba_m)
        vd[156:190] = root_record_data[:34]
        vd[190:318] = "ISO_SET".encode(encoding, 'ignore').ljust(128, b'\x00' if is_joliet else b' ')
        vd[881:882] = b'\x01'
        return vd

    def _generate_terminator(self):
        terminator = bytearray(self.logical_block_size)
        terminator[0:1] = b'\xff'
        terminator[1:6] = b'CD001'
        terminator[6:7] = b'\x01'
        return terminator

    def get_node_path(self, node):
        if not node.get('parent'): return '/'
        path_parts = []
        current = node
        while current and current.get('parent'):
            path_parts.append(current['name'])
            current = current['parent']
        return '/' + '/'.join(reversed(path_parts))

def main():
    root = tk.Tk()
    app = ISOEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
