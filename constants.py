"""
Constants and configuration values for ISO Editor.

This module centralizes all magic numbers, limits, and configuration
values used throughout the application.
"""

# Version Information
VERSION = "1.0.0"
APP_NAME = "ISO Editor"
APP_AUTHOR = "ISO Editor Team"
COPYRIGHT_YEAR = "2024"

# File System Constants
ISO_BLOCK_SIZE = 2048  # Standard ISO 9660 block size in bytes
CD_FRAME_SIZE = 2352   # CD-DA frame size in bytes
CD_FRAMES_PER_SECOND = 75  # CD frames per second
CD_SECONDS_PER_MINUTE = 60  # Seconds per minute

# ISO Standard Limits
ISO9660_MAX_FILENAME_LENGTH = 31  # ISO 9660 Level 2 max filename
JOLIET_MAX_FILENAME_LENGTH = 64   # Joliet max filename length
MAX_VOLUME_ID_LENGTH = 32         # Max length for volume identifier
MAX_SYSTEM_ID_LENGTH = 32         # Max length for system identifier
ISO9660_MAX_PATH_DEPTH = 8        # ISO 9660 max directory depth

# ISO 9660 Level 1 (DOS 8.3 format)
ISO9660_L1_MAX_NAME_LENGTH = 8    # Base filename
ISO9660_L1_MAX_EXT_LENGTH = 3     # Extension length

# Buffer Sizes
FILE_READ_BUFFER_SIZE = 8192      # Buffer for file reading (8 KB)
CHECKSUM_BUFFER_SIZE = 8192       # Buffer for checksum calculation

# Disc Sizes (in bytes)
CD_SIZE_BYTES = 700 * 1024 * 1024           # 700 MB CD
DVD_SIZE_BYTES = int(4.7 * 1024 * 1024 * 1024)  # 4.7 GB DVD
DVD_DL_SIZE_BYTES = int(8.5 * 1024 * 1024 * 1024)  # 8.5 GB Dual Layer DVD
BD_SIZE_BYTES = 25 * 1024 * 1024 * 1024    # 25 GB Blu-ray

# UI Constants
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600
DEFAULT_LEFT_PANE_WIDTH = 250
DEFAULT_RIGHT_PANE_WIDTH = 550
TREE_COLUMN_NAME_WIDTH = 300
TREE_COLUMN_SIZE_WIDTH = 100
TREE_COLUMN_DATE_WIDTH = 150
TREE_COLUMN_TYPE_WIDTH = 100

# Recent Files
MAX_RECENT_FILES = 10

# Timeout Constants
DEFAULT_COMMAND_TIMEOUT_MS = 120000  # 2 minutes
MAX_COMMAND_TIMEOUT_MS = 600000      # 10 minutes
PROCESS_TERMINATE_TIMEOUT_SEC = 5    # Timeout for graceful process termination

# Drag and Drop Visual Feedback
DRAG_BORDER_COLOR = "#4A90E2"  # Blue
DRAG_BACKGROUND_COLOR = "#E8F4FF"  # Light blue

# El Torito Boot Platform IDs
BOOT_PLATFORM_X86 = 0
BOOT_PLATFORM_POWERPC = 1
BOOT_PLATFORM_MAC = 2
BOOT_PLATFORM_EFI = 0xEF

# El Torito Boot Media Types
BOOT_MEDIA_NOEMUL = 0
BOOT_MEDIA_FLOPPY_1_2MB = 1
BOOT_MEDIA_FLOPPY_1_44MB = 2
BOOT_MEDIA_FLOPPY_2_88MB = 3
BOOT_MEDIA_HARDDISK = 4

# Boot Media Type Names
BOOT_EMULATION_NOEMUL = "noemul"
BOOT_EMULATION_FLOPPY = "floppy"
BOOT_EMULATION_HDEMUL = "hdemul"

# Configuration Paths
CONFIG_DIR_NAME = ".config"
CONFIG_SUBDIR_NAME = "iso-editor"
RECENT_FILES_FILENAME = "recent_files.json"
SETTINGS_FILENAME = "settings.json"
LOG_FILENAME = "iso_editor.log"

# Logging
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File Filters for Dialogs
ISO_FILE_FILTER = "Disc Images (*.iso *.cue);;ISO Files (*.iso);;CUE Files (*.cue);;All Files (*)"
ISO_SAVE_FILTER = "ISO Files (*.iso)"
BOOT_IMAGE_FILTER = "Boot Images (*.img *.bin);;All Files (*)"

# Progress Dialog Settings
PROGRESS_MIN_VALUE = 0
PROGRESS_MAX_VALUE = 100

# Status Messages
STATUS_READY = "Ready"
STATUS_LOADING = "Loading..."
STATUS_SAVING = "Saving..."
STATUS_MODIFIED_SUFFIX = " [Modified]"

# Platform Detection
PLATFORM_LINUX = "linux"
PLATFORM_WINDOWS = "win32"
PLATFORM_MACOS = "darwin"

# Default Values
DEFAULT_USE_JOLIET = True
DEFAULT_USE_ROCK_RIDGE = True
DEFAULT_USE_UDF = True
DEFAULT_MAKE_HYBRID = False
DEFAULT_CALCULATE_CHECKSUMS = True

# UDF Version
UDF_VERSION_2_60 = "2.60"

# Interchange Levels
ISO_INTERCHANGE_LEVEL_3 = 3

# Joliet Specification Level
JOLIET_SPEC_LEVEL = 3

# Rock Ridge Version
ROCK_RIDGE_VERSION = "1.09"

# Error Messages
ERROR_NO_ISO_LOADED = "No ISO file loaded."
ERROR_FILE_NOT_FOUND = "File not found"
ERROR_PERMISSION_DENIED = "Permission denied"
ERROR_INVALID_INPUT = "Invalid input"
ERROR_OPERATION_CANCELLED = "Operation cancelled by user"

# Success Messages
SUCCESS_ISO_SAVED = "ISO file has been saved successfully."
SUCCESS_FILE_ADDED = "File added successfully"
SUCCESS_FOLDER_CREATED = "Folder created successfully"
SUCCESS_EXTRACTION_COMPLETE = "Extraction complete."

# Dialog Titles
DIALOG_OPEN_IMAGE = "Open Image"
DIALOG_SAVE_ISO_AS = "Save ISO As"
DIALOG_SELECT_BIOS_BOOT_IMAGE = "Select BIOS Boot Image"
DIALOG_SELECT_EFI_BOOT_IMAGE = "Select EFI Boot Image"
DIALOG_SELECT_DIRECTORY = "Select Directory"
DIALOG_SAVE_FILE_AS = "Save File As"
DIALOG_UNSAVED_CHANGES = "Unsaved Changes"
DIALOG_CONFIRM_REMOVAL = "Confirm Removal"
DIALOG_ERROR = "Error"
DIALOG_WARNING = "Warning"
DIALOG_INFORMATION = "Information"
DIALOG_ABOUT = "About ISO Editor"

# Menu Item Names
MENU_FILE = "&File"
MENU_EDIT = "&Edit"
MENU_VIEW = "&View"
MENU_HELP = "&Help"

# Context Menu Actions
ACTION_EXTRACT = "Extract..."
ACTION_REMOVE = "Remove"

# Tree Widget Item Types
ITEM_TYPE_FILE = "File"
ITEM_TYPE_DIRECTORY = "Directory"

# Node Flags
NODE_FLAG_NEW = "is_new"
NODE_FLAG_HIDDEN = "is_hidden"
NODE_FLAG_DIRECTORY = "is_directory"
NODE_FLAG_CUE_TRACK = "is_cue_track"
