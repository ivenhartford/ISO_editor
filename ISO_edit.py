import sys
import logging
import logging.config
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QStatusBar, QMenu,
    QFileDialog, QMessageBox, QInputDialog, QSplitter, QGroupBox,
    QDialog, QDialogButtonBox, QLineEdit, QFormLayout, QPushButton
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QPoint
import os
import traceback
from iso_logic import ISOCore

class PropertiesDialog(QDialog):
    def __init__(self, parent, volume_descriptor, boot_image_path, efi_boot_image_path):
        super().__init__(parent)
        self.setWindowTitle("ISO Properties")

        self.layout = QFormLayout(self)

        # Volume Properties
        volume_group = QGroupBox("Volume Properties")
        volume_layout = QFormLayout()
        self.volume_id_edit = QLineEdit(volume_descriptor.get('volume_id', ''))
        self.system_id_edit = QLineEdit(volume_descriptor.get('system_id', ''))
        volume_layout.addRow("Volume ID:", self.volume_id_edit)
        volume_layout.addRow("System ID:", self.system_id_edit)
        volume_group.setLayout(volume_layout)
        self.layout.addWidget(volume_group)

        # Boot Properties
        boot_group = QGroupBox("Boot Options")
        boot_form_layout = QFormLayout()

        # BIOS Boot Image
        self.boot_image_edit = QLineEdit(boot_image_path or '')
        bios_browse_button = QPushButton("Browse...")
        bios_browse_button.clicked.connect(lambda: self.browse_for_image(self.boot_image_edit, "Select BIOS Boot Image"))
        bios_boot_layout = QHBoxLayout()
        bios_boot_layout.addWidget(self.boot_image_edit)
        bios_boot_layout.addWidget(bios_browse_button)
        boot_form_layout.addRow("BIOS Boot Image:", bios_boot_layout)

        # EFI Boot Image
        self.efi_boot_image_edit = QLineEdit(efi_boot_image_path or '')
        efi_browse_button = QPushButton("Browse...")
        efi_browse_button.clicked.connect(lambda: self.browse_for_image(self.efi_boot_image_edit, "Select EFI Boot Image"))
        efi_boot_layout = QHBoxLayout()
        efi_boot_layout.addWidget(self.efi_boot_image_edit)
        efi_boot_layout.addWidget(efi_browse_button)
        boot_form_layout.addRow("EFI Boot Image:", efi_boot_layout)

        boot_group.setLayout(boot_form_layout)
        self.layout.addWidget(boot_group)

        # Dialog Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def browse_for_image(self, line_edit, title):
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", "Boot Images (*.img *.bin);;All Files (*)")
        if file_path:
            line_edit.setText(file_path)

    def get_properties(self):
        return {
            'volume_id': self.volume_id_edit.text(),
            'system_id': self.system_id_edit.text(),
            'boot_image_path': self.boot_image_edit.text(),
            'efi_boot_image_path': self.efi_boot_image_edit.text()
        }

class ISOEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Application starting...")
        self.setWindowTitle("ISO Editor")
        self.setGeometry(100, 100, 800, 600)
        self.core = ISOCore()
        self.tree_item_map = {}
        self.show_hidden = False

        self.create_menu()
        self.create_main_interface()
        self.create_status_bar()
        self.refresh_view()

    def create_menu(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("&New ISO...", self)
        new_action.triggered.connect(self.new_iso)
        file_menu.addAction(new_action)

        open_action = QAction("&Open ISO...", self)
        open_action.triggered.connect(self.open_iso)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Save ISO", self)
        save_action.triggered.connect(self.save_iso)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save ISO &As...", self)
        save_as_action.triggered.connect(self.save_iso_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        add_file_action = QAction("Add &File...", self)
        add_file_action.triggered.connect(self.add_file)
        edit_menu.addAction(add_file_action)

        add_folder_action = QAction("Add F&older...", self)
        add_folder_action.triggered.connect(self.add_folder)
        edit_menu.addAction(add_folder_action)

        import_dir_action = QAction("&Import Directory...", self)
        import_dir_action.triggered.connect(self.import_directory)
        edit_menu.addAction(import_dir_action)

        edit_menu.addSeparator()

        remove_action = QAction("&Remove Selected", self)
        remove_action.triggered.connect(self.remove_selected)
        edit_menu.addAction(remove_action)

        edit_menu.addSeparator()

        properties_action = QAction("ISO &Properties...", self)
        properties_action.triggered.connect(self.show_iso_properties)
        edit_menu.addAction(properties_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")
        refresh_action = QAction("&Refresh", self)
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)

    def create_main_interface(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # Left pane
        left_pane = QGroupBox("ISO Properties")
        left_layout = QVBoxLayout(left_pane)

        self.iso_info = QLabel("No ISO loaded.")
        self.iso_info.setWordWrap(True)
        self.iso_info.setAlignment(Qt.AlignTop)
        left_layout.addWidget(self.iso_info)

        self.volume_name_label = QLabel("Volume Name:")
        left_layout.addWidget(self.volume_name_label)
        left_layout.addStretch()

        splitter.addWidget(left_pane)

        # Right pane
        right_pane = QGroupBox("ISO Contents")
        right_layout = QVBoxLayout(right_pane)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Name', 'Size', 'Date Modified', 'Type'])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 150)
        self.tree.setColumnWidth(3, 100)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        right_layout.addWidget(self.tree)

        splitter.addWidget(right_pane)

        splitter.setSizes([250, 550])
        main_layout.addWidget(splitter)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")

    def update_status(self, message):
        modified_indicator = " [Modified]" if self.core.iso_modified else ""
        self.status_bar.showMessage(f"{message}{modified_indicator}")

    def open_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open ISO", "", "ISO Files (*.iso);;All Files (*)")
        if not file_path:
            self.logger.info("Open ISO dialog cancelled.")
            return
        self.logger.info(f"Opening ISO file: {file_path}")
        try:
            self.core.load_iso(file_path)
            self.refresh_view()
            self.update_status(f"Loaded ISO: {os.path.basename(file_path)}")
            self.logger.info(f"Successfully loaded ISO: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to load ISO: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load ISO: {str(e)}")
            self.update_status("Error loading ISO")

    def new_iso(self):
        self.logger.info("Creating new ISO.")
        if self.core.iso_modified:
            reply = QMessageBox.question(self, "Unsaved Changes",
                                           "Save changes before creating a new ISO?",
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                self.logger.info("New ISO creation cancelled due to unsaved changes.")
                return
            if reply == QMessageBox.Yes:
                self.save_iso()
                if self.core.iso_modified: # If save was cancelled
                    self.logger.info("Save was cancelled, aborting new ISO creation.")
                    return
        self.core.init_new_iso()
        self.refresh_view()
        self.update_status("Created new empty ISO.")
        self.logger.info("New empty ISO created.")

    def save_iso(self):
        if not self.core.current_iso_path:
            self.save_iso_as()
        else:
            self._perform_save(self.core.current_iso_path)

    def save_iso_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save ISO As", "", "ISO Files (*.iso)")
        if file_path:
            self.logger.info(f"Saving ISO to new path: {file_path}")
            self._perform_save(file_path)
        else:
            self.logger.info("Save As dialog cancelled.")

    def _perform_save(self, file_path):
        self.update_status("Building ISO...")
        self.logger.info(f"Performing save to: {file_path}")
        try:
            self.core.save_iso(file_path, use_joliet=True, use_rock_ridge=True)
            self.refresh_view()
            self.update_status(f"Successfully saved to {os.path.basename(file_path)}")
            QMessageBox.information(self, "Success", "ISO file has been saved successfully.")
            self.logger.info(f"ISO saved successfully to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving ISO to {file_path}: {e}", exc_info=True)
            traceback.print_exc()
            QMessageBox.critical(self, "Error Saving ISO", f"An error occurred: {str(e)}")
            self.update_status("Error saving ISO.")

    def get_selected_node(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None
        return self.tree_item_map.get(id(selected_items[0]))

    def add_file(self):
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']:
            target_node = target_node['parent']

        file_paths, _ = QFileDialog.getOpenFileNames(self, "Add Files")
        if not file_paths:
            self.logger.info("Add files dialog cancelled.")
            return

        self.logger.info(f"Adding {len(file_paths)} files.")
        for fp in file_paths:
            if any(c['name'].lower() == os.path.basename(fp).lower() for c in target_node['children']):
                reply = QMessageBox.question(self, "File Exists", f"File '{os.path.basename(fp)}' already exists. Replace it?",
                                               QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    self.logger.info(f"Skipping existing file: {fp}")
                    continue
            self.core.add_file_to_directory(fp, target_node)
            self.logger.info(f"Added file: {fp}")

        self.refresh_view()
        self.update_status(f"Added {len(file_paths)} file(s)")

    def add_folder(self):
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']:
            target_node = target_node['parent']

        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if not ok or not folder_name:
            self.logger.info("Add folder dialog cancelled.")
            return

        if any(c['name'].lower() == folder_name.lower() for c in target_node['children']):
            self.logger.warning(f"Attempted to create a folder that already exists: {folder_name}")
            QMessageBox.critical(self, "Folder Exists", f"Folder '{folder_name}' already exists.")
            return

        self.logger.info(f"Adding new folder: {folder_name}")
        self.core.add_folder_to_directory(folder_name, target_node)
        self.refresh_view()

    def remove_selected(self):
        node = self.get_selected_node()
        if not node or node == self.core.directory_tree:
            self.logger.warning("Attempted to remove root or no node selected.")
            return

        reply = QMessageBox.question(self, "Confirm Removal", f"Are you sure you want to remove '{node['name']}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.logger.info(f"Removing node: {node['name']}")
            self.core.remove_node(node)
            self.refresh_view()
        else:
            self.logger.info(f"Removal of node cancelled: {node['name']}")

    def import_directory(self):
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']:
            target_node = target_node['parent']

        source_dir = QFileDialog.getExistingDirectory(self, "Select Directory to Import")
        if not source_dir:
            self.logger.info("Import directory dialog cancelled.")
            return

        self.logger.info(f"Importing directory '{source_dir}'")

        def import_recursive(source, target):
            dir_name = os.path.basename(source)
            self.core.add_folder_to_directory(dir_name, target)
            new_dir_node = next(c for c in target['children'] if c['name'] == dir_name and c.get('is_new'))
            for item in os.listdir(source):
                item_path = os.path.join(source, item)
                if os.path.isfile(item_path):
                    self.core.add_file_to_directory(item_path, new_dir_node)
                elif os.path.isdir(item_path):
                    import_recursive(item_path, new_dir_node)

        import_recursive(source_dir, target_node)
        self.refresh_view()
        self.update_status(f"Imported directory '{os.path.basename(source_dir)}'")
        self.logger.info(f"Successfully imported directory '{source_dir}'")

    def extract_selected(self):
        node = self.get_selected_node()
        if not node:
            self.logger.warning("Extract called with no node selected.")
            return

        if node['is_directory']:
            path = QFileDialog.getExistingDirectory(self, "Choose Extraction Location")
            if path:
                path = os.path.join(path, node['name'])
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Save File As", node['name'])

        if not path:
            self.logger.info("Extraction dialog cancelled.")
            return

        self.logger.info(f"Extracting node '{node['name']}' to '{path}'")
        try:
            self._extract_node_recursive(node, path)
            self.update_status(f"Extracted {node['name']}")
            QMessageBox.information(self, "Success", "Extraction complete.")
            self.logger.info(f"Successfully extracted node '{node['name']}'")
        except Exception as e:
            self.logger.error(f"Failed to extract node '{node['name']}': {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to extract: {e}")

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

    def show_context_menu(self, position: QPoint):
        item = self.tree.itemAt(position)
        if not item:
            return

        node = self.tree_item_map.get(id(item))
        if not node:
            return

        context_menu = QMenu(self)
        extract_action = context_menu.addAction("Extract...")
        remove_action = context_menu.addAction("Remove")

        action = context_menu.exec(self.tree.mapToGlobal(position))

        if action == extract_action:
            self.extract_selected()
        elif action == remove_action:
            self.remove_selected()

    def show_iso_properties(self):
        if not self.core.volume_descriptor:
            self.logger.warning("Attempted to show ISO properties with no ISO loaded.")
            QMessageBox.warning(self, "No ISO", "No ISO file loaded.")
            return

        self.logger.info("Showing ISO properties dialog.")
        dialog = PropertiesDialog(self, self.core.volume_descriptor, self.core.boot_image_path, self.core.efi_boot_image_path)
        if dialog.exec():
            self.logger.info("ISO properties dialog accepted.")
            new_props = dialog.get_properties()

            # Check if anything has changed to set the modified flag
            if (self.core.volume_descriptor.get('volume_id') != new_props['volume_id'] or
                self.core.volume_descriptor.get('system_id') != new_props['system_id'] or
                self.core.boot_image_path != new_props['boot_image_path'] or
                self.core.efi_boot_image_path != new_props['efi_boot_image_path']):

                self.logger.info("ISO properties changed.")
                self.core.volume_descriptor['volume_id'] = new_props['volume_id']
                self.core.volume_descriptor['system_id'] = new_props['system_id']
                self.core.boot_image_path = new_props['boot_image_path']
                self.core.efi_boot_image_path = new_props['efi_boot_image_path']
                self.core.iso_modified = True
                self.refresh_view()
        else:
            self.logger.info("ISO properties dialog cancelled.")

    def refresh_view(self):
        self.tree.clear()
        self.tree_item_map = {}
        if self.core.directory_tree:
            root_item = QTreeWidgetItem(self.tree, ['/', '', self.core.directory_tree['date'], 'Directory'])
            self.tree.addTopLevelItem(root_item)
            self.tree_item_map[id(root_item)] = self.core.directory_tree
            self.populate_tree_node(root_item, self.core.directory_tree)
            root_item.setExpanded(True)

        self.update_iso_info()

        title = "ISO Editor"
        if self.core.current_iso_path:
            title += f" - {os.path.basename(self.core.current_iso_path)}"
        if self.core.iso_modified:
            title += " [Modified]"
        self.setWindowTitle(title)
        self.update_status("View refreshed")

    def populate_tree_node(self, parent_item, parent_node):
        # Sort children: directories first, then files, both alphabetically
        sorted_children = sorted(parent_node['children'], key=lambda x: (not x['is_directory'], x['name'].lower()))

        for child in sorted_children:
            if child.get('is_hidden') and not self.show_hidden:
                continue

            size_text = self.format_file_size(child['size']) if not child['is_directory'] else ''
            file_type = 'Directory' if child['is_directory'] else 'File'
            display_name = child['name']
            if child.get('is_new'):
                display_name += " [NEW]"

            child_item = QTreeWidgetItem(parent_item, [display_name, size_text, child['date'], file_type])
            self.tree_item_map[id(child_item)] = child

            if child['is_directory'] and child['children']:
                self.populate_tree_node(child_item, child)

    def update_iso_info(self):
        if not self.core.volume_descriptor:
            self.iso_info.setText("No ISO loaded.")
            self.volume_name_label.setText("Volume Name: -")
            return

        vd = self.core.volume_descriptor
        info_text = (f"System ID: {vd['system_id']}\n"
                     f"Volume Size: {vd['volume_size']} blocks\n"
                     f"Block Size: {vd['logical_block_size']} bytes")
        self.iso_info.setText(info_text)
        self.volume_name_label.setText(f"Volume Name: {vd['volume_id']}")

    def format_file_size(self, size):
        if size == 0: return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0: return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

def main():
    if os.path.exists('logging.conf'):
        logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        logging.warning("logging.conf not found, using basic configuration.")

    app = QApplication(sys.argv)
    editor = ISOEditor()
    editor.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
