# ISO Editor

A comprehensive and user-friendly ISO image editor with support for multiple formats and bootable disc creation.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

## Features

### Core Functionality
- **Create, Open, and Edit ISO Images** - Full support for creating new ISOs and modifying existing ones
- **Multiple Format Support** - ISO 9660, Joliet, Rock Ridge, and UDF (Universal Disk Format)
- **CUE/BIN Support** - Open and edit disc images in CUE sheet format
- **Drag & Drop Interface** - Simply drag files and folders into the ISO
- **Bootable ISO Creation** - El Torito support for both BIOS and UEFI boot
- **Hybrid ISOs** - Create ISOs that boot from both CD/DVD and USB drives
- **Disc Ripping** (Linux) - Create ISO images directly from optical discs
- **Checksum Verification** - Calculate MD5, SHA-1, and SHA-256 checksums

### User Interface
- **Modern Qt-based GUI** - Clean, intuitive interface built with PySide6
- **Keyboard Shortcuts** - Full keyboard navigation support
- **Recent Files** - Quick access to recently opened ISOs
- **Context Menus** - Right-click for quick actions
- **Status Bar** - Real-time feedback on operations
- **Progress Dialogs** - Visual feedback for long operations
- **Unsaved Changes Protection** - Warns before closing with unsaved work

### Advanced Features
- **Directory Tree View** - Hierarchical view of ISO contents
- **File Metadata Preservation** - Maintains timestamps and attributes
- **Multi-Selection** - Select multiple files/folders for batch operations
- **Extract Files** - Extract individual files or entire directories from ISOs
- **Import Directories** - Recursively import entire folder structures
- **ISO Properties Editor** - Modify volume labels, boot options, and more

## Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Linux, Windows, or macOS
- **RAM**: 512 MB minimum (2 GB recommended for large ISOs)
- **Disk Space**: 100 MB for application + space for ISO files

### Python Dependencies
- `PySide6` - Qt6 bindings for Python (GUI framework)
- `pycdlib` - Pure Python library for reading and writing ISOs
- `CueParser` - CUE sheet parsing library

## Installation

### Quick Install (Linux/macOS)

```bash
# Clone the repository
git clone https://github.com/ivenhartford/ISO_editor.git
cd ISO_editor

# Run the setup script (creates virtual environment and installs dependencies)
./setup_venv.sh

# Activate the virtual environment
source venv/bin/activate

# Run the application
python3 ISO_edit.py
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/ivenhartford/ISO_editor.git
cd ISO_editor

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 ISO_edit.py
```

### Windows Installation

For Windows-specific build instructions (C++ version), see [README.windows.md](README.windows.md).

For the Python version on Windows:

```powershell
# Install Python 3.8+ from python.org
# Clone the repository
git clone https://github.com/ivenhartford/ISO_editor.git
cd ISO_editor

# Install dependencies
pip install -r requirements.txt

# Run the application
python ISO_edit.py
```

### Linux Package Dependencies

On some Linux distributions, you may need to install additional system packages:

**Ubuntu/Debian:**
```bash
sudo apt install python3-pip python3-venv
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-pip python3-virtualenv
# Or use the provided script
./install_deps-rhel.sh
```

## Usage

### Basic Operations

#### Creating a New ISO
1. Go to **File → New ISO** (or press `Ctrl+N`)
2. Add files using **Edit → Add File** (or press `Ctrl+F`)
3. Add folders using **Edit → Add Folder** (or press `Ctrl+Shift+F`)
4. Save the ISO using **File → Save ISO As** (or press `Ctrl+Shift+S`)

#### Opening an Existing ISO
1. Go to **File → Open ISO** (or press `Ctrl+O`)
2. Select your ISO or CUE file
3. Browse and edit the contents
4. Save changes with **File → Save ISO** (or press `Ctrl+S`)

#### Drag and Drop
- Simply drag files or folders from your file manager into the ISO tree view
- Files will be added to the currently selected directory (or root if none selected)

### Advanced Operations

#### Creating a Bootable ISO

1. Open or create an ISO
2. Go to **Edit → ISO Properties** (or press `Alt+Return`)
3. In the Boot Options section:
   - **BIOS Boot Image**: Select a boot image file (e.g., `boot.img`)
   - **Emulation Type**: Choose the appropriate mode:
     - `noemul`: No emulation (recommended for modern systems)
     - `floppy`: Floppy disk emulation
     - `hdemul`: Hard disk emulation
   - **EFI Boot Image**: Select an EFI boot image for UEFI systems (optional)
4. When saving, optionally check "Create Hybrid ISO" for USB boot support

#### Ripping a Disc to ISO (Linux Only)

1. Insert a disc into your optical drive
2. Go to **File → Create ISO from Disc** (or press `Ctrl+D`)
3. Select your drive from the dropdown
4. Choose the output location
5. Click "Start Ripping"

#### Extracting Files from an ISO

1. Open an ISO file
2. Right-click on a file or folder in the tree view
3. Select **Extract...**
4. Choose the destination folder

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New ISO |
| `Ctrl+O` | Open ISO |
| `Ctrl+S` | Save ISO |
| `Ctrl+Shift+S` | Save ISO As |
| `Ctrl+D` | Create ISO from Disc (Linux) |
| `Ctrl+F` | Add File |
| `Ctrl+Shift+F` | Add Folder |
| `Ctrl+I` | Import Directory |
| `Delete` | Remove Selected |
| `Alt+Return` | ISO Properties |
| `F5` | Refresh View |
| `Ctrl+Q` | Exit |

## Configuration

### Recent Files

Recent files are stored in `~/.config/iso-editor/recent_files.json`. The application remembers the last 10 opened files.

### Logging

Logs are written to `iso_editor.log` in the current directory. Log level can be configured (see [Configurable Logging](#configurable-logging) section).

## Technical Details

### Supported ISO Standards
- **ISO 9660** - Basic ISO standard (Level 1, 2, and 3)
- **Joliet** - Microsoft extension for long filenames (Unicode support)
- **Rock Ridge** - POSIX extension for Unix file attributes
- **UDF** - Universal Disk Format for better compatibility with modern systems
- **El Torito** - Bootable CD/DVD specification

### File System Limitations

| Standard | Max Filename Length | Max Path Depth | Notes |
|----------|-------------------|----------------|-------|
| ISO 9660 Level 1 | 8.3 (DOS format) | 8 levels | Most compatible |
| ISO 9660 Level 2 | 31 characters | 8 levels | Better compatibility |
| Joliet | 64 characters | Unlimited | Windows-friendly |
| Rock Ridge | 255 characters | Unlimited | Unix-friendly |
| UDF | 255 characters | Unlimited | Modern standard |

### Architecture

```
ISO_editor/
├── ISO_edit.py         # Main GUI application
├── iso_logic.py        # Core ISO manipulation logic
├── requirements.txt    # Python dependencies
├── tests/             # Unit tests
│   ├── test_iso_logic.py
│   ├── test_iso_edit.py
│   └── ...
└── scripts/           # Build and setup scripts
    ├── setup_venv.sh
    ├── install_deps.sh
    └── ...
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-qt pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_iso_logic.py -v
```

### Code Style

This project follows:
- PEP 8 style guidelines
- Type hints where appropriate
- Comprehensive docstrings
- Descriptive variable and function names

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Common Issues

#### "No module named 'PySide6'"
**Solution:** Install dependencies with `pip install -r requirements.txt`

#### "Permission denied" when accessing optical drive (Linux)
**Solution:** Add your user to the `cdrom` group:
```bash
sudo usermod -a -G cdrom $USER
# Log out and back in for changes to take effect
```

#### "dd: command not found" when ripping discs
**Solution:** Install `coreutils`:
- **Ubuntu/Debian:** `sudo apt install coreutils`
- **Fedora/RHEL:** `sudo dnf install coreutils`

#### ISO won't boot
**Solutions:**
- Ensure boot image file is valid and bootable
- Try different emulation types (noemul, floppy, hdemul)
- For USB booting, enable "Create Hybrid ISO" option
- Verify the boot image is in the correct format for your target system

#### "Filename not compliant with ISO9660"
**Explanation:** The application will automatically adjust filenames to be compatible with the strict ISO 9660 standard.

**Solutions:**
- Use Joliet or Rock Ridge extensions (enabled by default)
- Keep filenames short and simple for maximum compatibility
- Avoid special characters in filenames

### Debug Mode

For verbose logging, edit `ISO_edit.py` and change:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **pycdlib** - Excellent pure-Python ISO library
- **PySide6** - Python bindings for Qt6
- **CueParser** - CUE sheet parsing library

## Related Projects

- [genisoimage](https://linux.die.net/man/1/genisoimage) - Command-line ISO creation tool
- [ISO Master](http://littlesvr.ca/isomaster/) - Another GUI ISO editor
- [AcetoneISO](http://www.acetoneiso.com/) - ISO management suite

## Support

- **Issues**: [GitHub Issues](https://github.com/ivenhartford/ISO_editor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ivenhartford/ISO_editor/discussions)

## Changelog

### Version 1.0.0 (2024)
- Initial release
- Full ISO 9660, Joliet, Rock Ridge, and UDF support
- El Torito bootable ISO support (BIOS and EFI)
- Hybrid ISO creation
- CUE/BIN format support
- Disc ripping (Linux)
- Modern Qt-based GUI
- Comprehensive keyboard shortcuts
- Recent files menu
- Drag & drop support
- Checksum verification
- Extensive test coverage

---

**Made with ❤️ by the ISO Editor Team**
