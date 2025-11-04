import hashlib
import sys
import logging
import glob
import subprocess
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QStatusBar, QMenu,
    QFileDialog, QMessageBox, QInputDialog, QSplitter, QGroupBox,
    QDialog, QDialogButtonBox, QLineEdit, QFormLayout, QPushButton,
    QProgressDialog, QCheckBox, QComboBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QPoint, Signal, QThread
import os
import traceback
from iso_logic import ISOCore

logger = logging.getLogger(__name__)

IS_LINUX = sys.platform.startswith('linux')

class DroppableTreeWidget(QTreeWidget):
    """
    A QTreeWidget that supports drag and drop of files and folders.
    """
    filesDropped = Signal(list)

    def __init__(self, parent=None):
        """
        Initializes the DroppableTreeWidget.

        Args:
            parent (QWidget, optional): The parent widget.
        """
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """
        Handles the drag enter event. Accepts the event if it contains URLs.

        Args:
            event (QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """
        Handles the drag move event. Accepts the event if it contains URLs.

        Args:
            event (QDragMoveEvent): The drag move event.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """
        Handles the drop event. Emits a signal with the list of dropped file paths.

        Args:
            event (QDropEvent): The drop event.
        """
        if event.mimeData().hasUrls():
            urls = [url.toLocalFile() for url in event.mimeData().urls()]
            if urls:
                self.filesDropped.emit(urls)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class SaveAsDialog(QDialog):
    """
    A dialog for saving an ISO with options for UDF and Hybrid ISO.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save ISO As")
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.file_path_edit = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.file_path_edit)
        path_layout.addWidget(browse_button)

        form_layout.addRow("Save to:", path_layout)

        self.udf_checkbox = QCheckBox("Enable UDF Support")
        self.udf_checkbox.setChecked(True)
        form_layout.addRow(self.udf_checkbox)

        self.hybrid_checkbox = QCheckBox("Create Hybrid ISO")
        self.hybrid_checkbox.setChecked(False)
        form_layout.addRow(self.hybrid_checkbox)

        self.checksum_checkbox = QCheckBox("Verify checksums after saving")
        self.checksum_checkbox.setChecked(True)
        form_layout.addRow(self.checksum_checkbox)

        self.layout.addLayout(form_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def browse(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save ISO As", "", "ISO Files (*.iso)")
        if file_path:
            self.file_path_edit.setText(file_path)

    def accept(self):
        """Validate input before accepting the dialog."""
        file_path = self.file_path_edit.text().strip()

        if not file_path:
            QMessageBox.warning(self, "Invalid Input", "Please specify a file path.")
            return

        # Validate the directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            QMessageBox.warning(self, "Invalid Path", f"Directory does not exist:\n{directory}")
            return

        # Check if directory is writable
        if directory:
            test_dir = directory
        else:
            test_dir = os.getcwd()

        if not os.access(test_dir, os.W_OK):
            QMessageBox.warning(self, "Permission Denied", f"Cannot write to directory:\n{test_dir}")
            return

        # Ensure .iso extension
        if not file_path.lower().endswith('.iso'):
            file_path += '.iso'
            self.file_path_edit.setText(file_path)

        super().accept()

    def get_options(self):
        return {
            'file_path': self.file_path_edit.text().strip(),
            'use_udf': self.udf_checkbox.isChecked(),
            'make_hybrid': self.hybrid_checkbox.isChecked(),
            'calculate_checksums': self.checksum_checkbox.isChecked()
        }

class PropertiesDialog(QDialog):
    """
    A dialog for editing ISO properties, such as volume ID and boot options.
    """
    def __init__(self, parent, core):
        """
        Initializes the PropertiesDialog.
        Args:
            parent (QWidget): The parent widget.
            core (ISOCore): The ISOCore instance.
        """
        super().__init__(parent)
        self.setWindowTitle("ISO Properties")
        self.layout = QVBoxLayout(self)

        # Volume Properties
        volume_group = QGroupBox("Volume Properties")
        volume_layout = QFormLayout()
        self.volume_id_edit = QLineEdit(core.volume_descriptor.get('volume_id', ''))
        self.system_id_edit = QLineEdit(core.volume_descriptor.get('system_id', ''))
        volume_layout.addRow("Volume ID:", self.volume_id_edit)
        volume_layout.addRow("System ID:", self.system_id_edit)
        volume_group.setLayout(volume_layout)
        self.layout.addWidget(volume_group)

        # Detected Boot Info (Read-only)
        if core.extracted_boot_info:
            detected_boot_group = QGroupBox("Detected Boot Information")
            detected_boot_layout = QFormLayout()
            # Display info for the first boot entry found
            boot_info = core.extracted_boot_info[0]
            platform_map = {0: "x86", 1: "PowerPC", 2: "Mac", 0xef: "EFI"}
            platform_str = platform_map.get(boot_info.get('platform_id'), 'Unknown')

            detected_boot_layout.addRow(QLabel("Platform:"), QLabel(platform_str))
            detected_boot_layout.addRow(QLabel("Emulation:"), QLabel(boot_info.get('emulation_type', 'N/A')))
            detected_boot_layout.addRow(QLabel("Boot Image:"), QLabel(boot_info.get('boot_image_path', 'N/A')))
            detected_boot_group.setLayout(detected_boot_layout)
            self.layout.addWidget(detected_boot_group)

        # Boot Options (Editable)
        boot_group = QGroupBox("Boot Options")
        boot_form_layout = QFormLayout()

        # BIOS Boot Image
        self.boot_image_edit = QLineEdit(core.boot_image_path or '')
        bios_browse_button = QPushButton("Browse...")
        bios_browse_button.clicked.connect(lambda: self.browse_for_image(self.boot_image_edit, "Select BIOS Boot Image"))
        bios_boot_layout = QHBoxLayout()
        bios_boot_layout.addWidget(self.boot_image_edit)
        bios_boot_layout.addWidget(bios_browse_button)
        boot_form_layout.addRow("BIOS Boot Image:", bios_boot_layout)

        # Emulation Type
        self.emulation_combo = QComboBox()
        self.emulation_combo.addItems(['noemul', 'floppy', 'hdemul'])
        current_emulation = core.boot_emulation_type or 'noemul'
        self.emulation_combo.setCurrentText(current_emulation)
        boot_form_layout.addRow("Emulation Type:", self.emulation_combo)

        # EFI Boot Image
        self.efi_boot_image_edit = QLineEdit(core.efi_boot_image_path or '')
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

    def accept(self):
        """Validate input before accepting the dialog."""
        volume_id = self.volume_id_edit.text().strip()
        system_id = self.system_id_edit.text().strip()

        # Validate volume ID
        if not volume_id:
            QMessageBox.warning(self, "Invalid Input", "Volume ID cannot be empty.")
            return

        if len(volume_id) > 32:
            QMessageBox.warning(self, "Invalid Input", "Volume ID must be 32 characters or less.")
            return

        # Validate system ID
        if len(system_id) > 32:
            QMessageBox.warning(self, "Invalid Input", "System ID must be 32 characters or less.")
            return

        # Validate boot image paths if provided
        boot_path = self.boot_image_edit.text().strip()
        if boot_path and not os.path.exists(boot_path):
            reply = QMessageBox.question(
                self, "File Not Found",
                f"BIOS boot image file not found:\n{boot_path}\n\nContinue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        efi_path = self.efi_boot_image_edit.text().strip()
        if efi_path and not os.path.exists(efi_path):
            reply = QMessageBox.question(
                self, "File Not Found",
                f"EFI boot image file not found:\n{efi_path}\n\nContinue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        super().accept()

    def get_properties(self):
        return {
            'volume_id': self.volume_id_edit.text().strip(),
            'system_id': self.system_id_edit.text().strip(),
            'boot_image_path': self.boot_image_edit.text().strip(),
            'efi_boot_image_path': self.efi_boot_image_edit.text().strip(),
            'boot_emulation_type': self.emulation_combo.currentText()
        }


class RipDiscDialog(QDialog):
    """
    A dialog for setting up a disc ripping operation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create ISO from Disc")
        self.layout = QFormLayout(self)

        # Drive selection
        self.drive_combo = QComboBox()
        self.populate_drives()
        self.layout.addRow("Optical Drive:", self.drive_combo)

        # Output file
        self.output_path_edit = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_output)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(browse_button)
        self.layout.addRow("Output File:", output_layout)

        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.button(QDialogButtonBox.Ok).setText("Start Ripping")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def populate_drives(self):
        """
        Scans for optical drives and populates the combo box.
        """
        # A simple way to find drives on Linux
        drives = sorted(glob.glob('/dev/sr[0-9]*'))
        if drives:
            self.drive_combo.addItems(drives)
        else:
            self.drive_combo.addItem("No drives found")
            self.drive_combo.setEnabled(False)

    def browse_output(self):
        """
        Opens a file dialog to select the output ISO file.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save ISO As", "", "ISO Files (*.iso)")
        if file_path:
            self.output_path_edit.setText(file_path)

    def accept(self):
        """Validate input before accepting the dialog."""
        if not self.drive_combo.isEnabled():
            QMessageBox.warning(self, "No Drives", "No optical drives were found.")
            return

        drive = self.drive_combo.currentText()
        if not drive or "No drives found" in drive:
            QMessageBox.warning(self, "No Drive Selected", "Please select a valid optical drive.")
            return

        output_path = self.output_path_edit.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Invalid Input", "Please specify an output file path.")
            return

        # Validate the directory exists
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            QMessageBox.warning(self, "Invalid Path", f"Directory does not exist:\n{directory}")
            return

        # Check if directory is writable
        if directory:
            test_dir = directory
        else:
            test_dir = os.getcwd()

        if not os.access(test_dir, os.W_OK):
            QMessageBox.warning(self, "Permission Denied", f"Cannot write to directory:\n{test_dir}")
            return

        # Ensure .iso extension
        if not output_path.lower().endswith('.iso'):
            output_path += '.iso'
            self.output_path_edit.setText(output_path)

        # Check if drive is accessible
        if not os.path.exists(drive):
            reply = QMessageBox.question(
                self, "Drive Not Accessible",
                f"Cannot access drive:\n{drive}\n\nContinue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        super().accept()

    def get_rip_options(self):
        """
        Gets the selected options from the dialog.
        """
        if not self.drive_combo.isEnabled():
            return None
        return {
            'drive': self.drive_combo.currentText(),
            'output_path': self.output_path_edit.text().strip()
        }


class ISOEditor(QMainWindow):
    """
    The main window of the ISO Editor application.
    """
    def __init__(self):
        """Initializes the ISOEditor main window."""
        super().__init__()
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
        """Creates the main menu bar."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("&New ISO...", self)
        new_action.triggered.connect(self.new_iso)
        file_menu.addAction(new_action)

        open_action = QAction("&Open ISO...", self)
        open_action.triggered.connect(self.open_iso)
        file_menu.addAction(open_action)

        if IS_LINUX:
            rip_disc_action = QAction("Create ISO from &Disc...", self)
            rip_disc_action.triggered.connect(self.rip_disc)
            file_menu.addAction(rip_disc_action)

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
        """Creates the main user interface of the application."""
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

        self.tree = DroppableTreeWidget()
        self.tree.setHeaderLabels(['Name', 'Size', 'Date Modified', 'Type'])
        self.tree.filesDropped.connect(self.handle_drop)
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
        """Creates the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")

    def update_status(self, message):
        """
        Updates the message in the status bar.

        Args:
            message (str): The message to display.
        """
        modified_indicator = " [Modified]" if self.core.iso_modified else ""
        self.status_bar.showMessage(f"{message}{modified_indicator}")

    def open_iso(self):
        """Opens an ISO file and loads it into the editor."""
        logger.info("Open ISO action triggered.")
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Disc Images (*.iso *.cue);;All Files (*)")
        if not file_path:
            logger.info("Open ISO dialog cancelled.")
            return
        try:
            self.core.load_iso(file_path)
            self.refresh_view()
            self.update_status(f"Loaded ISO: {os.path.basename(file_path)}")
            logger.info(f"Successfully loaded ISO: {file_path}")
        except Exception as e:
            logger.exception(f"Failed to load ISO: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load ISO: {str(e)}")
            self.update_status("Error loading ISO")

    def new_iso(self):
        """Creates a new, empty ISO."""
        logger.info("New ISO action triggered.")
        if self.core.iso_modified:
            reply = QMessageBox.question(self, "Unsaved Changes",
                                           "Save changes before creating a new ISO?",
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                self.save_iso()
                if self.core.iso_modified: # If save was cancelled
                    return
        self.core.init_new_iso()
        self.refresh_view()
        self.update_status("Created new empty ISO.")
        logger.info("New empty ISO created.")

    def save_iso(self):
        """Saves the current ISO to its existing path."""
        logger.info("Save ISO action triggered.")
        if not self.core.current_iso_path:
            self.save_iso_as()
        else:
            # When re-saving, we don't show the options dialog, so we use default values.
            self._perform_save(self.core.current_iso_path, use_udf=True, make_hybrid=False, calculate_checksums=False)

    def save_iso_as(self):
        """Saves the current ISO to a new path."""
        logger.info("Save ISO As action triggered.")
        dialog = SaveAsDialog(self)
        if dialog.exec():
            options = dialog.get_options()
            if options['file_path']:
                self._perform_save(
                    options['file_path'],
                    options['use_udf'],
                    options['make_hybrid'],
                    options['calculate_checksums']
                )
            else:
                logger.info("Save As dialog cancelled.")
        else:
            logger.info("Save As dialog cancelled.")

    def _perform_save(self, file_path, use_udf, make_hybrid, calculate_checksums=False):
        """
        Performs the save operation, including filename validation.
        """
        logger.info(f"Attempting to save ISO to {file_path}")
        self.should_calculate_checksums = calculate_checksums

        # Validate filenames before saving
        non_compliant_files = self.core.find_non_compliant_filenames()
        if non_compliant_files:
            message = (
                "The following filenames are not compliant with the strict ISO9660 standard:\n\n"
                f"{', '.join(non_compliant_files[:5])}{'...' if len(non_compliant_files) > 5 else ''}\n\n"
                "These names will be automatically adjusted for maximum compatibility. "
                "This is usually safe.\n\n"
                "Do you want to continue?"
            )
            reply = QMessageBox.warning(self, "Filename Warning", message,
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Cancel:
                logger.info("User cancelled save due to non-compliant filenames.")
                self.update_status("Save cancelled by user.")
                return

        self.progress_dialog = QProgressDialog("Building ISO...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.canceled.connect(self.cancel_save)

        self.save_thread = SaveWorker(self.core, file_path, use_udf, make_hybrid)
        self.save_thread.progress.connect(self.update_progress)
        self.save_thread.finished.connect(self.save_finished)
        self.save_thread.error.connect(self.save_error)

        self.save_thread.start()
        self.progress_dialog.exec()

    def update_progress(self, value):
        self.progress_dialog.setValue(value)

    def cancel_save(self):
        if self.save_thread.isRunning():
            self.save_thread.cancel()
            self.update_status("Cancelling save operation...")

    def save_finished(self, file_path):
        self.progress_dialog.setValue(100)
        self.refresh_view()
        self.update_status(f"Successfully saved to {os.path.basename(file_path)}")
        logger.info(f"ISO saved successfully to {file_path}")

        if self.should_calculate_checksums:
            self.update_status(f"Saved. Now calculating checksums for {os.path.basename(file_path)}...")
            self.checksum_thread = ChecksumWorker(file_path)
            self.checksum_thread.finished.connect(self.checksum_finished)
            self.checksum_thread.start()
        else:
            QMessageBox.information(self, "Success", "ISO file has been saved successfully.")

    def checksum_finished(self, hashes, error_string):
        if error_string:
            QMessageBox.critical(self, "Error", error_string)
            self.update_status("Error calculating checksums.")
            return

        checksum_text = (f"Checksums for {os.path.basename(self.core.current_iso_path)}:\n\n"
                         f"MD5:    {hashes['md5']}\n"
                         f"SHA-1:  {hashes['sha1']}\n"
                         f"SHA-256: {hashes['sha256']}")

        QMessageBox.information(self, "Checksums", checksum_text)
        self.update_status("Checksum calculation complete.")

    def save_error(self, error_message):
        self.progress_dialog.close()
        logger.exception(f"An error occurred while saving the ISO: {error_message}")
        QMessageBox.critical(self, "Error Saving ISO", f"An error occurred: {error_message}")
        self.update_status("Error saving ISO.")

    def rip_disc(self):
        """
        Shows the dialog for ripping a disc to an ISO file and starts the process.
        """
        logger.info("Rip Disc action triggered.")
        dialog = RipDiscDialog(self)
        if dialog.exec():
            options = dialog.get_rip_options()
            if not options or not options.get('drive') or not options.get('output_path'):
                QMessageBox.warning(self, "Invalid Options", "Please select a valid drive and an output path.")
                return

            logger.info(f"Starting disc rip with options: {options}")

            self.rip_progress_dialog = QProgressDialog("Ripping disc...", "Cancel", 0, 100, self)
            self.rip_progress_dialog.setWindowModality(Qt.WindowModal)
            self.rip_progress_dialog.setAutoClose(True)

            self.rip_thread = RipDiscWorker(options['drive'], options['output_path'])
            self.rip_thread.progress.connect(self.update_rip_progress)
            self.rip_thread.finished.connect(self.rip_finished)
            self.rip_progress_dialog.canceled.connect(self.rip_thread.stop) # Connect cancel button

            self.rip_thread.start()
            self.rip_progress_dialog.exec()

    def update_rip_progress(self, value):
        self.rip_progress_dialog.setValue(value)

    def rip_finished(self, error_message):
        self.rip_progress_dialog.setValue(100)
        if error_message:
            QMessageBox.critical(self, "Ripping Failed", error_message)
            self.update_status("Disc ripping failed.")
        else:
            QMessageBox.information(self, "Success", "Disc has been successfully ripped to an ISO file.")
            self.update_status("Disc ripping complete.")

class SaveWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, core, file_path, use_udf, make_hybrid):
        super().__init__()
        self.core = core
        self.file_path = file_path
        self.use_udf = use_udf
        self.make_hybrid = make_hybrid
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the save operation."""
        self._cancelled = True

    def run(self):
        try:
            # The progress callback for pycdlib's write method
            def progress_cb(done, total, opaque):
                if self._cancelled:
                    raise InterruptedError("Save operation cancelled by user")
                percent = (done * 100) // total
                self.progress.emit(percent)

            self.core.save_iso(self.file_path, use_joliet=True, use_rock_ridge=True, progress_callback=progress_cb, use_udf=self.use_udf, make_hybrid=self.make_hybrid)
            if not self._cancelled:
                self.finished.emit(self.file_path)
        except InterruptedError as e:
            logger.info(f"Save operation cancelled: {e}")
            self.error.emit("Save cancelled by user")
        except Exception as e:
            logger.exception(f"Error during save operation: {e}")
            self.error.emit(str(e))


class ChecksumWorker(QThread):
    """
    A QThread worker for calculating file checksums in the background.
    """
    # Signal -> dict: e.g., {'md5': '...', 'sha1': '...', 'sha256': '...'}
    #           str:  Error message if something goes wrong.
    finished = Signal(dict, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the checksum calculation."""
        self._cancelled = True

    def run(self):
        """
        Calculates MD5, SHA1, and SHA256 hashes for the file.
        """
        try:
            hashes = {'md5': hashlib.md5(), 'sha1': hashlib.sha1(), 'sha256': hashlib.sha256()}
            with open(self.file_path, 'rb') as f:
                while chunk := f.read(8192):
                    if self._cancelled:
                        logger.info("Checksum calculation cancelled by user")
                        self.finished.emit({}, "Checksum calculation cancelled")
                        return
                    for h in hashes.values():
                        h.update(chunk)

            if not self._cancelled:
                results = {name: h.hexdigest() for name, h in hashes.items()}
                self.finished.emit(results, "")
        except Exception as e:
            logger.error(f"Checksum calculation failed for {self.file_path}: {e}")
            self.finished.emit({}, f"Failed to calculate checksums: {e}")


class RipDiscWorker(QThread):
    """
    A QThread worker for ripping a disc in the background using dd.
    """
    progress = Signal(int) # Percentage
    finished = Signal(str) # Error message (if any)

    def __init__(self, source_drive, dest_path):
        super().__init__()
        self.source_drive = source_drive
        self.dest_path = dest_path
        self._is_running = True

    def run(self):
        """
        Executes the dd command to rip the disc.
        """
        command = [
            'dd',
            f'if={self.source_drive}',
            f'of={self.dest_path}',
            'bs=2048',
            'status=progress'
        ]

        try:
            process = subprocess.Popen(command, stderr=subprocess.PIPE, text=True, encoding='utf-8')

            # This is a simplification. A better implementation would get the disc size first.
            DVD_SIZE_BYTES = 4.7 * 1024 * 1024 * 1024

            while self._is_running and process.poll() is None:
                line = process.stderr.readline()
                if line:
                    match = re.search(r'(\d+)\s+bytes', line)
                    if match:
                        bytes_copied = int(match.group(1))
                        percent = int((bytes_copied / DVD_SIZE_BYTES) * 100)
                        self.progress.emit(min(percent, 100))

            if not self._is_running:
                logger.info("Rip disc operation cancelled, terminating dd process")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("dd process did not terminate gracefully, killing it")
                    process.kill()
                    process.wait()

                # Clean up partial output file
                if os.path.exists(self.dest_path):
                    try:
                        os.remove(self.dest_path)
                        logger.info(f"Removed partial output file: {self.dest_path}")
                    except OSError as e:
                        logger.error(f"Failed to remove partial output file: {e}")

                self.finished.emit("Ripping cancelled by user.")
                return

            retcode = process.wait()
            if retcode == 0:
                self.progress.emit(100)
                self.finished.emit("") # Success
            else:
                self.finished.emit(f"dd command failed with exit code {retcode}")

        except FileNotFoundError:
            self.finished.emit("Error: 'dd' command not found. Is it installed and in your PATH?")
        except Exception as e:
            logger.error(f"Disc ripping failed: {e}")
            self.finished.emit(f"An unexpected error occurred: {e}")

    def stop(self):
        self._is_running = False


    def get_selected_node(self):
        """
        Gets the currently selected node in the tree view.

        Returns:
            dict or None: The selected node, or None if no node is selected.
        """
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None
        return self.tree_item_map.get(id(selected_items[0]))

    def add_file(self):
        """Adds a file to the ISO."""
        logger.info("Add File action triggered.")
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']:
            target_node = target_node['parent']

        file_paths, _ = QFileDialog.getOpenFileNames(self, "Add Files")
        if not file_paths:
            logger.info("Add Files dialog cancelled.")
            return

        for fp in file_paths:
            try:
                if any(c['name'].lower() == os.path.basename(fp).lower() for c in target_node['children']):
                    reply = QMessageBox.question(self, "File Exists", f"File '{os.path.basename(fp)}' already exists. Replace it?",
                                                   QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        continue
                self.core.add_file_to_directory(fp, target_node)
            except Exception as e:
                logger.exception(f"Failed to add file {fp}: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add file {os.path.basename(fp)}: {e}")

        self.refresh_view()
        self.update_status(f"Added {len(file_paths)} file(s)")

    def add_folder(self):
        """Adds a folder to the ISO."""
        logger.info("Add Folder action triggered.")
        try:
            target_node = self.get_selected_node() or self.core.directory_tree
            if not target_node.get('is_directory'):
                target_node = target_node.get('parent')

            folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
            if not ok or not folder_name:
                logger.info("Add Folder dialog cancelled.")
                return

            if any(c['name'].lower() == folder_name.lower() for c in target_node.get('children', [])):
                logger.warning(f"Attempted to create a folder with an existing name: {folder_name}")
                QMessageBox.warning(self, "Folder Exists", f"A folder with the name '{folder_name}' already exists.")
                return

            self.core.add_folder_to_directory(folder_name, target_node)
            self.refresh_view()
            self.update_status(f"Added folder: {folder_name}")
        except Exception as e:
            logger.exception(f"Failed to add folder: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while adding the folder: {e}")

    def remove_selected(self):
        """Removes the selected file or folder from the ISO."""
        logger.info("Remove Selected action triggered.")
        try:
            node = self.get_selected_node()
            if not node or node == self.core.directory_tree:
                logger.debug("Remove selected called with no valid node selected or root selected.")
                return

            node_name = node.get('name', 'the selected item')
            reply = QMessageBox.question(self, "Confirm Removal", f"Are you sure you want to remove '{node_name}'?",
                                           QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                logger.info(f"User confirmed removal of node: {node_name}")
                self.core.remove_node(node)
                self.refresh_view()
                self.update_status(f"Removed '{node_name}'")
            else:
                logger.info(f"User cancelled removal of node: {node_name}")
        except Exception as e:
            logger.exception(f"Failed to remove selected item: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while removing the item: {e}")

    def import_directory(self):
        """Imports a directory from the local filesystem into the ISO."""
        logger.info("Import Directory action triggered.")
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']:
            target_node = target_node['parent']

        source_dir = QFileDialog.getExistingDirectory(self, "Select Directory to Import")
        if not source_dir:
            logger.info("Import Directory dialog cancelled.")
            return

        try:
            self._import_directory_recursive(source_dir, target_node)
            self.refresh_view()
            self.update_status(f"Imported directory '{os.path.basename(source_dir)}'")
            logger.info(f"Successfully imported directory: {source_dir}")
        except Exception as e:
            logger.exception(f"Failed to import directory {source_dir}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to import directory: {e}")

    def extract_selected(self):
        """Extracts the selected file or folder from the ISO to the local filesystem."""
        logger.info("Extract Selected action triggered.")
        node = self.get_selected_node()
        if not node:
            logger.debug("Extract selected called with no valid node selected.")
            return

        if node['is_directory']:
            path = QFileDialog.getExistingDirectory(self, "Choose Extraction Location")
            if path:
                path = os.path.join(path, node['name'])
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Save File As", node['name'])

        if not path:
            logger.info("Extraction dialog cancelled.")
            return

        try:
            self._extract_node_recursive(node, path)
            self.update_status(f"Extracted {node['name']}")
            logger.info(f"Successfully extracted {node['name']} to {path}")
            QMessageBox.information(self, "Success", "Extraction complete.")
        except Exception as e:
            logger.exception(f"Failed to extract {node['name']}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to extract: {e}")

    def _extract_node_recursive(self, node, extract_path):
        """
        Recursively extracts a node and its children. Handles exceptions at each step.

        Args:
            node (dict): The node to extract.
            extract_path (str): The path to extract to.
        """
        node_name = node.get('name', 'Unnamed')
        try:
            if node.get('is_directory'):
                # Create the directory for the current node
                os.makedirs(extract_path, exist_ok=True)
                logger.info(f"Created directory: {extract_path}")

                # Recursively extract children
                for child in node.get('children', []):
                    child_path = os.path.join(extract_path, child.get('name', 'Unnamed_Child'))
                    self._extract_node_recursive(child, child_path) # This will handle its own exceptions
            else:
                # Get file data from the core logic
                file_data = self.core.get_file_data(node)
                if file_data is None:
                    # This can happen if get_file_data returns None on error
                    raise IOError(f"Failed to retrieve data for file '{node_name}' from ISO.")

                # Ensure parent directory exists before writing
                parent_dir = os.path.dirname(extract_path)
                os.makedirs(parent_dir, exist_ok=True)

                # Write the file data
                with open(extract_path, 'wb') as f:
                    f.write(file_data)
                logger.info(f"Extracted file: {extract_path}")

        except (IOError, OSError) as e:
            # Catch file system related errors (permissions, disk full, etc.)
            error_message = f"A file system error occurred while extracting '{node_name}': {e}"
            logger.exception(error_message)
            # We re-raise to let the top-level caller handle the UI notification
            raise IOError(error_message) from e
        except Exception as e:
            # Catch any other unexpected errors
            error_message = f"An unexpected error occurred during the extraction of '{node_name}': {e}"
            logger.exception(error_message)
            raise Exception(error_message) from e

    def handle_drop(self, urls):
        """
        Handles the drop event from the DroppableTreeWidget.

        Args:
            urls (list): A list of local file paths from the drop event.
        """
        logger.info(f"Drag and drop event received with {len(urls)} URLs.")
        target_node = self.get_selected_node() or self.core.directory_tree
        if not target_node['is_directory']:
            target_node = target_node['parent']

        for url in urls:
            try:
                if os.path.isfile(url):
                    self.core.add_file_to_directory(url, target_node)
                elif os.path.isdir(url):
                    self._import_directory_recursive(url, target_node)
            except Exception as e:
                logger.exception(f"Failed to process dropped item {url}: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add {os.path.basename(url)}: {e}")

        self.refresh_view()
        self.update_status(f"Added {len(urls)} items via drag and drop.")

    def _import_directory_recursive(self, source_dir, target_node):
        """
        Recursively imports a directory and its contents.

        Args:
            source_dir (str): The source directory to import.
            target_node (dict): The target node in the ISO to import into.
        """
        dir_name = os.path.basename(source_dir)
        # Avoid creating a folder if one with the same name already exists.
        existing_folder = next((c for c in target_node['children'] if c['name'].lower() == dir_name.lower() and c['is_directory']), None)
        if existing_folder:
            new_dir_node = existing_folder
        else:
            self.core.add_folder_to_directory(dir_name, target_node)
            new_dir_node = next(c for c in target_node['children'] if c['name'] == dir_name and c.get('is_new'))

        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if os.path.islink(item_path):
                logger.warning(f"Skipping symbolic link: {item_path}")
                continue
            if os.path.isfile(item_path):
                self.core.add_file_to_directory(item_path, new_dir_node)
            elif os.path.isdir(item_path):
                self._import_directory_recursive(item_path, new_dir_node)

    def show_context_menu(self, position: QPoint):
        """
        Shows the context menu for the tree view.

        Args:
            position (QPoint): The position to show the context menu at.
        """
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
        """Shows the ISO properties dialog."""
        logger.info("Show ISO Properties action triggered.")
        if not self.core.volume_descriptor:
            QMessageBox.warning(self, "No ISO", "No ISO file loaded.")
            return

        dialog = PropertiesDialog(self, self.core)
        if dialog.exec():
            new_props = dialog.get_properties()
            logger.info(f"ISO properties updated: {new_props}")

            # Check if anything has changed to set the modified flag
            if (self.core.volume_descriptor.get('volume_id') != new_props['volume_id'] or
                self.core.volume_descriptor.get('system_id') != new_props['system_id'] or
                self.core.boot_image_path != new_props['boot_image_path'] or
                self.core.efi_boot_image_path != new_props['efi_boot_image_path'] or
                self.core.boot_emulation_type != new_props['boot_emulation_type']):

                self.core.volume_descriptor['volume_id'] = new_props['volume_id']
                self.core.volume_descriptor['system_id'] = new_props['system_id']
                self.core.boot_image_path = new_props['boot_image_path']
                self.core.efi_boot_image_path = new_props['efi_boot_image_path']
                self.core.boot_emulation_type = new_props['boot_emulation_type']
                self.core.iso_modified = True
                self.refresh_view()

    def refresh_view(self):
        """Refreshes the tree view to show the current state of the ISO."""
        logger.debug("Refreshing tree view.")
        self.tree.clear()
        self.tree_item_map = {}
        if self.core.directory_tree:
            root_item = QTreeWidgetItem(self.tree, ['/', '', self.core.directory_tree.get('date', ''), 'Directory'])
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
        """
        Recursively populates the tree view with nodes.

        Args:
            parent_item (QTreeWidgetItem): The parent tree item.
            parent_node (dict): The parent node in the directory tree.
        """
        # Sort children: directories first, then files, both alphabetically
        sorted_children = sorted(parent_node.get('children', []), key=lambda x: (not x.get('is_directory', False), x.get('name', '').lower()))

        for child in sorted_children:
            if child.get('is_hidden') and not self.show_hidden:
                continue

            size_text = self.format_file_size(child.get('size', 0)) if not child.get('is_directory') else ''
            file_type = 'Directory' if child.get('is_directory') else 'File'
            display_name = child.get('name', '')
            if child.get('is_new'):
                display_name += " [NEW]"

            child_item = QTreeWidgetItem(parent_item, [display_name, size_text, child.get('date', ''), file_type])
            self.tree_item_map[id(child_item)] = child

            if child.get('children'):
                self.populate_tree_node(child_item, child)

    def update_iso_info(self):
        """Updates the ISO information display."""
        if not self.core.volume_descriptor:
            self.iso_info.setText("No ISO loaded.")
            self.volume_name_label.setText("Volume Name: -")
            return

        vd = self.core.volume_descriptor
        info_text = (f"System ID: {vd.get('system_id', 'N/A')}\n"
                     f"Volume Size: {vd.get('volume_size', 0)} blocks\n"
                     f"Block Size: {vd.get('logical_block_size', 0)} bytes")
        self.iso_info.setText(info_text)
        self.volume_name_label.setText(f"Volume Name: {vd.get('volume_id', 'N/A')}")

    def format_file_size(self, size):
        """
        Formats a file size in bytes into a human-readable string.

        Args:
            size (int): The file size in bytes.

        Returns:
            str: The formatted file size string.
        """
        if size == 0: return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0: return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

def main():
    """The main entry point of the application."""
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        filename='iso_editor.log',
                        filemode='w')
    logger.info("Application starting...")
    app = QApplication(sys.argv)
    editor = ISOEditor()
    editor.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
