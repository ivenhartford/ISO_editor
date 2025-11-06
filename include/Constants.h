#ifndef CONSTANTS_H
#define CONSTANTS_H

#include <QString>
#include <cstdint>

namespace Constants {

// Version Information
constexpr const char* VERSION = "1.0.0";
constexpr const char* APP_NAME = "ISO Editor";
constexpr const char* APP_AUTHOR = "ISO Editor Team";
constexpr const char* COPYRIGHT_YEAR = "2025";

// File System Constants
constexpr int ISO_BLOCK_SIZE = 2048;
constexpr int CD_FRAME_SIZE = 2352;
constexpr int CD_FRAMES_PER_SECOND = 75;

// ISO Standard Limits
constexpr int ISO9660_MAX_FILENAME_LENGTH = 31;
constexpr int JOLIET_MAX_FILENAME_LENGTH = 64;
constexpr int MAX_VOLUME_ID_LENGTH = 32;
constexpr int MAX_SYSTEM_ID_LENGTH = 32;
constexpr int ISO9660_MAX_PATH_DEPTH = 8;

// Buffer Sizes
constexpr int FILE_READ_BUFFER_SIZE = 8192;
constexpr int CHECKSUM_BUFFER_SIZE = 8192;

// Disc Sizes (in bytes)
constexpr uint64_t CD_SIZE_BYTES = 700ULL * 1024 * 1024;
constexpr uint64_t DVD_SIZE_BYTES = 4700ULL * 1024 * 1024;
constexpr uint64_t DVD_DL_SIZE_BYTES = 8500ULL * 1024 * 1024;
constexpr uint64_t BD_SIZE_BYTES = 25ULL * 1024 * 1024 * 1024;

// UI Constants
constexpr int DEFAULT_WINDOW_WIDTH = 800;
constexpr int DEFAULT_WINDOW_HEIGHT = 600;
constexpr int DEFAULT_LEFT_PANE_WIDTH = 250;
constexpr int DEFAULT_RIGHT_PANE_WIDTH = 550;
constexpr int TREE_COLUMN_NAME_WIDTH = 300;
constexpr int TREE_COLUMN_SIZE_WIDTH = 100;
constexpr int TREE_COLUMN_DATE_WIDTH = 150;
constexpr int TREE_COLUMN_TYPE_WIDTH = 100;

// Recent Files
constexpr int MAX_RECENT_FILES = 10;

// Timeout Constants
constexpr int DEFAULT_COMMAND_TIMEOUT_MS = 120000;
constexpr int MAX_COMMAND_TIMEOUT_MS = 600000;
constexpr int PROCESS_TERMINATE_TIMEOUT_SEC = 5;

// Drag and Drop Visual Feedback
constexpr const char* DRAG_BORDER_COLOR = "#4A90E2";
constexpr const char* DRAG_BACKGROUND_COLOR = "#E8F4FF";

// El Torito Boot Platform IDs
constexpr uint8_t BOOT_PLATFORM_X86 = 0;
constexpr uint8_t BOOT_PLATFORM_POWERPC = 1;
constexpr uint8_t BOOT_PLATFORM_MAC = 2;
constexpr uint8_t BOOT_PLATFORM_EFI = 0xEF;

// El Torito Boot Media Types
constexpr uint8_t BOOT_MEDIA_NOEMUL = 0;
constexpr uint8_t BOOT_MEDIA_FLOPPY_1_2MB = 1;
constexpr uint8_t BOOT_MEDIA_FLOPPY_1_44MB = 2;
constexpr uint8_t BOOT_MEDIA_FLOPPY_2_88MB = 3;
constexpr uint8_t BOOT_MEDIA_HARDDISK = 4;

// Boot Emulation Type Names
constexpr const char* BOOT_EMULATION_NOEMUL = "noemul";
constexpr const char* BOOT_EMULATION_FLOPPY = "floppy";
constexpr const char* BOOT_EMULATION_HDEMUL = "hdemul";

// Configuration Paths
constexpr const char* CONFIG_DIR_NAME = ".config";
constexpr const char* CONFIG_SUBDIR_NAME = "iso-editor";
constexpr const char* RECENT_FILES_FILENAME = "recent_files.json";
constexpr const char* SETTINGS_FILENAME = "settings.json";
constexpr const char* LOG_FILENAME = "iso_editor.log";

// File Filters for Dialogs
constexpr const char* ISO_FILE_FILTER = "Disc Images (*.iso *.cue);;ISO Files (*.iso);;CUE Files (*.cue);;All Files (*)";
constexpr const char* ISO_SAVE_FILTER = "ISO Files (*.iso)";
constexpr const char* BOOT_IMAGE_FILTER = "Boot Images (*.img *.bin);;All Files (*)";

// Status Messages
constexpr const char* STATUS_READY = "Ready";
constexpr const char* STATUS_LOADING = "Loading...";
constexpr const char* STATUS_SAVING = "Saving...";
constexpr const char* STATUS_MODIFIED_SUFFIX = " [Modified]";

// Error Messages
constexpr const char* ERROR_NO_ISO_LOADED = "No ISO file loaded.";
constexpr const char* ERROR_FILE_NOT_FOUND = "File not found";
constexpr const char* ERROR_PERMISSION_DENIED = "Permission denied";
constexpr const char* ERROR_INVALID_INPUT = "Invalid input";
constexpr const char* ERROR_OPERATION_CANCELLED = "Operation cancelled by user";

// Success Messages
constexpr const char* SUCCESS_ISO_SAVED = "ISO file has been saved successfully.";
constexpr const char* SUCCESS_FILE_ADDED = "File added successfully";
constexpr const char* SUCCESS_FOLDER_CREATED = "Folder created successfully";
constexpr const char* SUCCESS_EXTRACTION_COMPLETE = "Extraction complete.";

// Dialog Titles
constexpr const char* DIALOG_OPEN_IMAGE = "Open Image";
constexpr const char* DIALOG_SAVE_ISO_AS = "Save ISO As";
constexpr const char* DIALOG_SELECT_BIOS_BOOT_IMAGE = "Select BIOS Boot Image";
constexpr const char* DIALOG_SELECT_EFI_BOOT_IMAGE = "Select EFI Boot Image";
constexpr const char* DIALOG_UNSAVED_CHANGES = "Unsaved Changes";

// Tree Widget Item Types
constexpr const char* ITEM_TYPE_FILE = "File";
constexpr const char* ITEM_TYPE_DIRECTORY = "Directory";

} // namespace Constants

#endif // CONSTANTS_H
