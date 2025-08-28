import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import traceback
from iso_logic import ISOCore

class ISOEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ISO Editor")
        self.root.geometry("800x600")
        self.core = ISOCore()
        self.tree_item_map = {}
        self.show_hidden = False
        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()
        self.refresh_view()

    def create_menu(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open ISO...", command=self.open_iso)
        file_menu.add_command(label="New ISO...", command=self.new_iso)
        file_menu.add_separator()
        file_menu.add_command(label="Save ISO", command=self.save_iso)
        file_menu.add_command(label="Save ISO As...", command=self.save_iso_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add File...", command=self.add_file)
        edit_menu.add_command(label="Add Folder...", command=self.add_folder)
        edit_menu.add_command(label="Import Directory...", command=self.import_directory)
        edit_menu.add_separator()
        edit_menu.add_command(label="Remove Selected", command=self.remove_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="ISO Properties...", command=self.show_iso_properties)
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_view)

    def create_main_interface(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_frame = ttk.LabelFrame(main_frame, text="ISO Properties", width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)
        self.iso_info = tk.Text(left_frame, width=30, height=15, wrap=tk.WORD)
        self.iso_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(left_frame, text="Volume Name:").pack(anchor=tk.W, padx=5)
        self.volume_name_var = tk.StringVar()
        self.volume_name_entry = ttk.Entry(left_frame, textvariable=self.volume_name_var)
        self.volume_name_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        self.volume_name_entry.bind('<Return>', self.update_volume_name)
        right_frame = ttk.LabelFrame(main_frame, text="ISO Contents")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree = ttk.Treeview(tree_frame, columns=('Size', 'Date', 'Type'), show='tree headings')
        self.tree.heading('#0', text='Name'); self.tree.column('#0', width=300)
        self.tree.heading('Size', text='Size'); self.tree.column('Size', width=100)
        self.tree.heading('Date', text='Date Modified'); self.tree.column('Date', width=150)
        self.tree.heading('Type', text='Type'); self.tree.column('Type', width=100)
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        modified_indicator = " [Modified]" if self.core.iso_modified else ""
        self.status_bar.config(text=f"{message}{modified_indicator}")
        self.root.update_idletasks()

    def open_iso(self):
        file_path = filedialog.askopenfilename(filetypes=[("ISO files", "*.iso"), ("All files", "*.*")])
        if not file_path: return
        try:
            self.core.load_iso(file_path)
            self.refresh_view()
            self.update_status(f"Loaded ISO: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ISO: {str(e)}")
            self.update_status("Error loading ISO")

    def new_iso(self):
        if self.core.iso_modified:
            if not messagebox.askyesno("Unsaved Changes", "Save changes before creating a new ISO?"):
                return
            self.save_iso()
            if self.core.iso_modified: return
        self.core.init_new_iso()
        self.refresh_view()
        self.update_status("Created new empty ISO.")

    def save_iso(self):
        if not self.core.current_iso_path:
            self.save_iso_as()
        else:
            self._perform_save(self.core.current_iso_path)

    def save_iso_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".iso", filetypes=[("ISO files", "*.iso")])
        if file_path:
            self._perform_save(file_path)

    def _perform_save(self, file_path):
        try:
            self.update_status("Building ISO...")
            self.core.save_iso(file_path, use_joliet=True, use_rock_ridge=True)
            self.refresh_view()
            self.update_status(f"Successfully saved to {os.path.basename(file_path)}")
            messagebox.showinfo("Success", "ISO file has been saved successfully.")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error Saving ISO", f"An error occurred: {str(e)}")
            self.update_status("Error saving ISO.")

    def add_file(self):
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']: target_node = target_node['parent']
        file_paths = filedialog.askopenfilenames()
        if not file_paths: return
        for fp in file_paths:
            if any(c['name'].lower() == os.path.basename(fp).lower() for c in target_node['children']):
                if not messagebox.askyesno("File Exists", f"File '{os.path.basename(fp)}' already exists. Replace it?"):
                    continue
            self.core.add_file_to_directory(fp, target_node)
        self.refresh_view()
        self.update_status(f"Added {len(file_paths)} file(s)")

    def add_folder(self):
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']: target_node = target_node['parent']
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if not folder_name: return
        if any(c['name'].lower() == folder_name.lower() for c in target_node['children']):
            return messagebox.showerror("Folder Exists", f"Folder '{folder_name}' already exists.")
        self.core.add_folder_to_directory(folder_name, target_node)
        self.refresh_view()

    def remove_selected(self):
        node = self.get_selected_node()
        if not node or node == self.core.directory_tree: return
        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{node['name']}'?"):
            self.core.remove_node(node)
            self.refresh_view()

    def refresh_view(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_item_map = {}
        if self.core.directory_tree:
            root_item = self.tree.insert('', 'end', text='/', values=('Directory', '', ''))
            self.tree_item_map[root_item] = self.core.directory_tree
            self.populate_tree_node(root_item, self.core.directory_tree)
            self.tree.item(root_item, open=True)
        self.update_iso_info()
        title = "ISO Editor"
        if self.core.current_iso_path:
            title += f" - {os.path.basename(self.core.current_iso_path)}"
        if self.core.iso_modified:
            title += " [Modified]"
        self.root.title(title)

    def populate_tree_node(self, tree_item, node):
        for child in sorted(node['children'], key=lambda x: x['name']):
            if child.get('is_hidden') and not self.show_hidden: continue
            size_text = self.format_file_size(child['size']) if not child['is_directory'] else ''
            file_type = 'Directory' if child['is_directory'] else 'File'
            display_name = child['name']
            if child.get('is_new'): display_name += " [NEW]"
            child_item = self.tree.insert(tree_item, 'end', text=display_name, values=(size_text, child['date'], file_type))
            self.tree_item_map[child_item] = child
            if child['is_directory'] and child['children']:
                self.populate_tree_node(child_item, child)

    def get_selected_node(self):
        selection = self.tree.selection()
        return self.tree_item_map.get(selection[0]) if selection else None

    def update_iso_info(self):
        if not self.core.volume_descriptor: return
        vd = self.core.volume_descriptor
        info_text = (f"System ID: {vd['system_id']}\n"
                     f"Volume ID: {vd['volume_id']}\n"
                     f"Volume Size: {vd['volume_size']} blocks\n"
                     f"Block Size: {vd['logical_block_size']} bytes")
        self.iso_info.delete(1.0, tk.END)
        self.iso_info.insert(1.0, info_text)
        self.volume_name_var.set(vd['volume_id'])

    def update_volume_name(self, event=None):
        if self.core.volume_descriptor:
            self.core.volume_descriptor['volume_id'] = self.volume_name_var.get()
            self.core.iso_modified = True
            self.refresh_view()

    def import_directory(self):
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']: target_node = target_node['parent']
        source_dir = filedialog.askdirectory(title="Select directory to import")
        if not source_dir: return

        def import_recursive(source, target):
            dir_name = os.path.basename(source)
            self.core.add_folder_to_directory(dir_name, target)
            new_dir_node = next(c for c in target['children'] if c['name'] == dir_name)
            for item in os.listdir(source):
                item_path = os.path.join(source, item)
                if os.path.isfile(item_path):
                    self.core.add_file_to_directory(item_path, new_dir_node)
                elif os.path.isdir(item_path):
                    import_recursive(item_path, new_dir_node)

        import_recursive(source_dir, target_node)
        self.refresh_view()
        self.update_status(f"Imported directory '{os.path.basename(source_dir)}'")

    def extract_selected(self):
        node = self.get_selected_node()
        if not node: return

        if node['is_directory']:
            path = filedialog.askdirectory(title="Choose extraction location")
            if path: path = os.path.join(path, node['name'])
        else:
            path = filedialog.asksaveasfilename(initialname=node['name'])

        if not path: return

        try:
            self._extract_node_recursive(node, path)
            self.update_status(f"Extracted {node['name']}")
            messagebox.showinfo("Success", "Extraction complete.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract: {e}")

    def _extract_node_recursive(self, node, extract_path):
        if node['is_directory']:
            os.makedirs(extract_path, exist_ok=True)
            for child in node['children']:
                child_path = os.path.join(extract_path, child['name'])
                self._extract_node_recursive(child, child_path)
        else:
            file_data = self.core.get_file_data(node)
            os.makedirs(os.path.dirname(extract_path), exist_ok=True)
            with open(extract_path, 'wb') as f:
                f.write(file_data)

    def show_iso_properties(self):
        if not self.core.volume_descriptor:
            return messagebox.showwarning("No ISO", "No ISO file loaded")

        props_window = tk.Toplevel(self.root)
        props_window.title("ISO Properties")
        props_window.geometry("400x200")
        props_window.grab_set()

        ttk.Label(props_window, text="Volume Properties", font=('Arial', 12, 'bold')).pack(pady=10)

        frame = ttk.Frame(props_window); frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frame, text="Volume ID:").pack(side=tk.LEFT)
        vol_id_var = tk.StringVar(value=self.core.volume_descriptor['volume_id'])
        ttk.Entry(frame, textvariable=vol_id_var).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        frame = ttk.Frame(props_window); frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(frame, text="System ID:").pack(side=tk.LEFT)
        sys_id_var = tk.StringVar(value=self.core.volume_descriptor['system_id'])
        ttk.Entry(frame, textvariable=sys_id_var).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        button_frame = ttk.Frame(props_window); button_frame.pack(fill=tk.X, padx=20, pady=20)

        def apply_changes():
            self.core.volume_descriptor['volume_id'] = vol_id_var.get()
            self.core.volume_descriptor['system_id'] = sys_id_var.get()
            self.core.iso_modified = True
            self.refresh_view()
            props_window.destroy()

        ttk.Button(button_frame, text="Apply", command=apply_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=props_window.destroy).pack(side=tk.RIGHT)

    def toggle_hidden_files(self):
        self.show_hidden = not self.show_hidden
        self.refresh_view()
        self.update_status(f"Hidden files {'shown' if self.show_hidden else 'hidden'}")

    def on_tree_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        self.tree.item(item_id, open=not self.tree.item(item_id, 'open'))

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id: self.tree.selection_set(item_id)
        node = self.get_selected_node()
        context_menu = tk.Menu(self.root, tearoff=0)
        if node:
            context_menu.add_command(label="Extract...", command=self.extract_selected)
            context_menu.add_command(label="Remove", command=self.remove_selected)
        context_menu.tk_popup(event.x_root, event.y_root)
    def format_file_size(self, size):
        if size == 0: return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0: return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

def main():
    root = tk.Tk()
    app = ISOEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
