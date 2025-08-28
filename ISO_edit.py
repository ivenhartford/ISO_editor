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
        """Load and parse ISO file"""
        self.current_iso_path = file_path

        with open(file_path, 'rb') as f:
            # Read the entire ISO into memory (for small-medium ISOs)
            self.iso_data = f.read()

        # Parse ISO 9660 structure
        self.parse_iso_structure()
        self.update_iso_info()
        self.populate_file_tree()

    def parse_iso_structure(self):
        """Parse ISO 9660 file system structure"""
        # Find Primary Volume Descriptor (sector 16, 2048 bytes per sector)
        pvd_offset = 16 * 2048

        if len(self.iso_data) < pvd_offset + 2048:
            raise ValueError("Invalid ISO file: too small")

        # Read Primary Volume Descriptor
        pvd_data = self.iso_data[pvd_offset:pvd_offset + 2048]

        # Check PVD signature
        if pvd_data[0:5] != b'\x01CD001':
            raise ValueError("Invalid ISO file: PVD signature not found")

        # Extract volume information
        self.volume_descriptor = {
            'system_id': pvd_data[8:40].decode('ascii', errors='ignore').strip(),
            'volume_id': pvd_data[40:72].decode('ascii', errors='ignore').strip(),
            'volume_size': struct.unpack('<L', pvd_data[80:84])[0],
            'volume_set_size': struct.unpack('<H', pvd_data[120:122])[0],
            'volume_sequence_number': struct.unpack('<H', pvd_data[124:126])[0],
            'logical_block_size': struct.unpack('<H', pvd_data[128:130])[0],
            'path_table_size': struct.unpack('<L', pvd_data[132:136])[0],
            'root_dir_record': pvd_data[156:190]
        }

        # Parse root directory
        self.root_directory = self.parse_directory_record(self.volume_descriptor['root_dir_record'])

        # Build complete directory tree
        self.directory_tree = self.build_directory_tree()

        # Calculate next available extent location for new files
        self.calculate_next_extent_location()

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
        file_id = record_data[33:33 + file_id_length].decode('ascii', errors='ignore')

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
        """Read all entries from a directory"""
        entries = []
        block_size = self.volume_descriptor['logical_block_size']

        # Read directory data
        offset = extent_location * block_size

        if offset >= len(self.iso_data):
            return entries

        # Read the directory block
        directory_data = self.iso_data[offset:offset + block_size]

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

            builder = ISOBuilder(self.directory_tree, self.volume_descriptor.get('volume_id', 'TK_ISO_VOL'))
            iso_data = builder.build()

            self.update_status(f"Writing to {os.path.basename(file_path)}...")
            self.root.update_idletasks()
            with open(file_path, 'wb') as f:
                f.write(iso_data)

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

        # Otherwise, read from original ISO
        block_size = self.volume_descriptor['logical_block_size']
        offset = node['extent_location'] * block_size
        size = node['size']

        if offset + size > len(self.iso_data):
            size = len(self.iso_data) - offset

        return self.iso_data[offset:offset + size]

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
    def __init__(self, root_node, volume_id="TK_ISO_VOL"):
        self.root_node = root_node
        self.volume_id = volume_id
        self.logical_block_size = 2048

        self.path_table_records = []
        self.l_path_table_data = b''
        self.m_path_table_data = b''

        self.l_path_table_lba = 0
        self.m_path_table_lba = 0

        self.next_lba = 0
        self.file_and_dir_data = {}  # LBA -> data bytes

    def build(self):
        """Main method to build the ISO byte stream."""
        # --- Pass 1: Layout and Path Table Generation ---
        # System Area (16 * 2048 = 32768 bytes) is reserved.
        self.next_lba = 16

        # Reserve space for Volume Descriptors
        pvd_lba = self.next_lba
        self.next_lba += 1 # PVD
        self.next_lba += 1 # Terminator

        # Recursively lay out directories and files, and collect path table info
        self._layout_pass(self.root_node, 1)

        # Now that layout is done, generate path tables.
        self._generate_path_tables()

        self.l_path_table_lba = self.next_lba
        self.next_lba += math.ceil(len(self.l_path_table_data) / self.logical_block_size)
        self.m_path_table_lba = self.next_lba
        self.next_lba += math.ceil(len(self.m_path_table_data) / self.logical_block_size)

        # --- Pass 2: Directory Record Generation ---
        # Now that all LBAs are known, generate the actual directory record data
        self._generate_all_directory_records(self.root_node)

        # --- Pass 3: Final Assembly ---
        volume_size_in_blocks = self.next_lba

        # Generate PVD with all final locations and sizes
        pvd_data = self._generate_pvd(volume_size_in_blocks)
        self.file_and_dir_data[pvd_lba] = pvd_data

        # Generate terminator
        terminator_data = self._generate_terminator()
        self.file_and_dir_data[pvd_lba + 1] = terminator_data

        # Place path tables
        self.file_and_dir_data[self.l_path_table_lba] = self.l_path_table_data
        self.file_and_dir_data[self.m_path_table_lba] = self.m_path_table_data

        # Assemble the final ISO bytearray
        iso_data = bytearray(volume_size_in_blocks * self.logical_block_size)
        for lba, data in self.file_and_dir_data.items():
            start_offset = lba * self.logical_block_size
            iso_data[start_offset : start_offset + len(data)] = data

        return iso_data

    def _layout_pass(self, node, parent_dir_num):
        """Recursively traverses the tree to assign LBAs and gather path table info."""
        dir_num = len(self.path_table_records) + 1
        node['dir_num'] = dir_num

        self.path_table_records.append({
            'node': node,
            'parent_dir_num': parent_dir_num
        })

        # First, recurse into subdirectories to handle them first
        for child in sorted(node['children'], key=lambda x: x['name']):
            if child['is_directory']:
                self._layout_pass(child, dir_num)

        # Then, lay out files in the current directory
        for child in sorted(node['children'], key=lambda x: x['name']):
            if not child['is_directory']:
                file_data = child.get('file_data', b'')
                num_blocks = math.ceil(child['size'] / self.logical_block_size)
                if num_blocks == 0: num_blocks = 1 # min 1 block even for 0-byte file

                child['extent_location'] = self.next_lba
                self.file_and_dir_data[self.next_lba] = file_data
                self.next_lba += num_blocks

        # Finally, calculate this directory's record size and assign its LBA
        dir_records_data = self._generate_directory_records_for_node(node)
        node['data_length'] = len(dir_records_data)

        num_blocks = math.ceil(node['data_length'] / self.logical_block_size)
        if num_blocks == 0: num_blocks = 1

        node['extent_location'] = self.next_lba
        self.next_lba += num_blocks

    def _generate_path_tables(self):
        """Generates both L-type and M-type path tables."""
        # Sort records for path table: root, then level 1 alphabetically, etc.
        self.path_table_records.sort(key=lambda r: self.get_node_path(r['node']))

        # Re-number directories after sorting and create a lookup
        dir_num_map = {self.get_node_path(r['node']): i + 1 for i, r in enumerate(self.path_table_records)}

        l_table = bytearray()
        m_table = bytearray()

        for record in self.path_table_records:
            node = record['node']
            path = self.get_node_path(node)
            parent_path = os.path.dirname(path).replace('\\', '/') if path != '/' else '/'
            parent_dir_num = dir_num_map.get(parent_path, 1)

            dir_id = b'\x00' if node['name'] == '/' else node['name'].encode('ascii')
            id_len = len(dir_id)

            # L-Path Table Record (Little Endian)
            l_rec = struct.pack('<BB<L<H', id_len, 0, node['extent_location'], parent_dir_num) + dir_id
            if id_len % 2 != 0:
                l_rec += b'\x00'
            l_table.extend(l_rec)

            # M-Path Table Record (Big Endian)
            m_rec = struct.pack('<BB>L>H', id_len, 0, node['extent_location'], parent_dir_num) + dir_id
            if id_len % 2 != 0:
                m_rec += b'\x00'
            m_table.extend(m_rec)

        self.l_path_table_data = bytes(l_table)
        self.m_path_table_data = bytes(m_table)

    def _generate_all_directory_records(self, node):
        """Traverses tree and stores final directory record data."""
        records_data = self._generate_directory_records_for_node(node)

        # Pad to full block size
        padded_data = bytearray(math.ceil(len(records_data) / self.logical_block_size) * self.logical_block_size)
        padded_data[:len(records_data)] = records_data

        self.file_and_dir_data[node['extent_location']] = bytes(padded_data)

        for child in node['children']:
            if child['is_directory']:
                self._generate_all_directory_records(child)

    def _generate_directory_records_for_node(self, node):
        """Generates the concatenated record data for all children of a node."""
        all_records = bytearray()

        # '.' entry (self)
        all_records.extend(self._create_dir_record(node, is_self=True))

        # '..' entry (parent)
        all_records.extend(self._create_dir_record(node.get('parent', node), is_parent=True))

        # Child entries
        for child in sorted(node['children'], key=lambda x: x['name']):
            all_records.extend(self._create_dir_record(child))

        return bytes(all_records)

    def _create_dir_record(self, node, is_self=False, is_parent=False):
        """Creates a single directory record."""
        file_flags = 0
        if node['is_directory']:
            file_flags |= 0x02
        if node.get('is_hidden', False):
            file_flags |= 0x01

        if is_self:
            file_id = b'\x00'
            data_len = node['data_length']
        elif is_parent:
            file_id = b'\x01'
            data_len = node['data_length']
        else:
            file_id_str = node['name']
            if not node['is_directory']:
                file_id_str += ';1'
            file_id = file_id_str.encode('ascii')
            data_len = node['size'] if not node['is_directory'] else node['data_length']

        file_id_len = len(file_id)

        try:
            record_date = datetime.strptime(node['date'], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            record_date = datetime.now()
        dir_date_bytes = _format_dir_date(record_date)

        record_len = 33 + file_id_len
        if record_len % 2 != 0:
            record_len += 1 # Records must have even length

        rec = bytearray(record_len)
        struct.pack_into('<B', rec, 0, record_len)
        struct.pack_into('<B', rec, 1, 0)  # Extended Attribute Record Length
        rec[2:10] = _pack_both_endian_32(node['extent_location'])
        rec[10:18] = _pack_both_endian_32(data_len)
        rec[18:25] = dir_date_bytes
        struct.pack_into('<B', rec, 25, file_flags)
        # Bytes 26, 27 are 0 for non-interleaved files
        rec[28:32] = _pack_both_endian_16(1)  # Volume Sequence Number
        struct.pack_into('<B', rec, 32, file_id_len)
        rec[33:33 + file_id_len] = file_id

        return bytes(rec)

    def _generate_pvd(self, volume_size_in_blocks):
        """Generates the Primary Volume Descriptor."""
        pvd = bytearray(self.logical_block_size)

        root_record_data = self._create_dir_record(self.root_node, is_self=True)

        pvd[0:1] = b'\x01'
        pvd[1:6] = b'CD001'
        pvd[6:7] = b'\x01'
        pvd[8:40] = _format_str_a("PYTHON TK ISO EDITOR", 32)
        pvd[40:72] = _format_str_d(self.volume_id, 32)
        pvd[80:88] = _pack_both_endian_32(volume_size_in_blocks)
        pvd[120:124] = _pack_both_endian_16(1)  # Volume Set Size
        pvd[124:128] = _pack_both_endian_16(1)  # Volume Sequence Number
        pvd[128:132] = _pack_both_endian_16(self.logical_block_size)
        pvd[132:140] = _pack_both_endian_32(len(self.l_path_table_data))
        pvd[140:144] = struct.pack('<L', self.l_path_table_lba)
        pvd[148:152] = struct.pack('>L', self.m_path_table_lba)
        pvd[156:190] = root_record_data[:34] # Root directory record (fixed size)
        pvd[190:318] = _format_str_d("ISO_SET", 128)
        pvd[318:446] = _format_str_a("JULES AI", 128)
        pvd[446:574] = _format_str_a("JULES AI", 128)
        pvd[574:702] = _format_str_a("ISO EDITOR", 128)

        now_date = _format_pvd_date()
        pvd[813:830] = now_date  # Volume Creation
        pvd[830:847] = now_date  # Volume Modification
        # Expiration and Effective dates are all '0's
        zero_date = b'0000000000000000\x00'
        pvd[847:864] = zero_date
        pvd[864:881] = zero_date

        pvd[881:882] = b'\x01'  # File Structure Version
        return pvd

    def _generate_terminator(self):
        """Generates the Volume Descriptor Set Terminator."""
        terminator = bytearray(self.logical_block_size)
        terminator[0:1] = b'\xff'
        terminator[1:6] = b'CD001'
        terminator[6:7] = b'\x01'
        return terminator

    def get_node_path(self, node):
        """Helper to get full, sortable path for a node."""
        if not node.get('parent'):
            return '/'
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
