# Building ISO Editor (Qt/C++)

This document provides detailed instructions for building the ISO Editor from source on Linux, Windows, and macOS.

## Prerequisites

### All Platforms

- **CMake** 3.16 or newer
- **Qt6** 6.5 or newer (Widgets module)
- **C++17 compatible compiler**

### Linux

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    qt6-base-dev \
    qt6-tools-dev \
    libisofs-dev \
    libisoburn-dev \
    git
```

#### Fedora/RHEL

```bash
sudo dnf install -y \
    gcc-c++ \
    cmake \
    qt6-qtbase-devel \
    qt6-qttools-devel \
    libisofs-devel \
    libisoburn-devel \
    git
```

#### Arch Linux

```bash
sudo pacman -S --needed \
    base-devel \
    cmake \
    qt6-base \
    qt6-tools \
    libisofs \
    libisoburn \
    git
```

### Windows

1. **Install Visual Studio 2019 or newer** (Community Edition is fine)
   - Include "Desktop development with C++" workload
   - Download from: https://visualstudio.microsoft.com/

2. **Install CMake**
   - Download from: https://cmake.org/download/
   - Add to PATH during installation

3. **Install Qt6**
   - Download Qt Online Installer: https://www.qt.io/download-qt-installer
   - Install Qt 6.5+ with MSVC 2019 64-bit component
   - Note the installation path (e.g., `C:\Qt\6.5.3\msvc2019_64`)

4. **Build libisofs and libisoburn** (or use pre-built binaries)
   - Option 1: Use vcpkg
     ```bash
     git clone https://github.com/Microsoft/vcpkg.git
     cd vcpkg
     .\bootstrap-vcpkg.bat
     .\vcpkg install libisofs:x64-windows libisoburn:x64-windows
     ```
   - Option 2: Download pre-built binaries from libburnia project

### macOS

1. **Install Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **Install Homebrew** (if not already installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Install dependencies**
   ```bash
   brew install cmake qt6 libisofs libisoburn
   ```

---

## Building

### Linux

```bash
# Clone the repository
git clone https://github.com/ivenhartford/ISO_editor.git
cd ISO_editor

# Create build directory
mkdir build
cd build

# Configure with CMake
cmake -DCMAKE_BUILD_TYPE=Release ..

# Build (use all CPU cores)
make -j$(nproc)

# Optional: Run tests
ctest --output-on-failure

# Optional: Install system-wide
sudo make install
```

The binary will be located at: `build/iso-editor`

### Linux (Static Build)

For a portable binary with Qt statically linked:

```bash
# Download and build Qt6 statically (one-time setup)
# This is a complex process - see Qt documentation

# Then build ISO Editor with static Qt
mkdir build-static
cd build-static
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_PREFIX_PATH=/path/to/static/qt6 \
      -DBUILD_STATIC=ON \
      ..
make -j$(nproc)
```

Result: Single ~20MB binary with no external dependencies (except libc).

### Windows (Visual Studio)

```bash
# Clone the repository
git clone https://github.com/ivenhartford/ISO_editor.git
cd ISO_editor

# Create build directory
mkdir build
cd build

# Configure with CMake (adjust Qt path)
cmake -G "Visual Studio 16 2019" -A x64 ^
      -DCMAKE_PREFIX_PATH=C:\Qt\6.5.3\msvc2019_64 ^
      -DCMAKE_BUILD_TYPE=Release ^
      ..

# Build
cmake --build . --config Release

# Optional: Run tests
ctest -C Release --output-on-failure
```

The executable will be at: `build\Release\iso-editor.exe`

**Note**: You'll need to copy Qt DLLs to run the executable. Use `windeployqt`:

```bash
cd build\Release
C:\Qt\6.5.3\msvc2019_64\bin\windeployqt.exe iso-editor.exe
```

### Windows (MinGW)

```bash
# Install MinGW and add to PATH
# Install Qt6 for MinGW

# Create build directory
mkdir build
cd build

# Configure
cmake -G "MinGW Makefiles" ^
      -DCMAKE_PREFIX_PATH=C:\Qt\6.5.3\mingw_64 ^
      -DCMAKE_BUILD_TYPE=Release ^
      ..

# Build
mingw32-make -j4
```

### macOS

```bash
# Clone the repository
git clone https://github.com/ivenhartford/ISO_editor.git
cd ISO_editor

# Create build directory
mkdir build
cd build

# Configure
cmake -DCMAKE_BUILD_TYPE=Release ..

# Build
make -j$(sysctl -n hw.ncpu)

# Optional: Create .app bundle
# (Additional steps needed - see Packaging section)
```

The binary will be at: `build/iso-editor`

---

## Running

### Linux

```bash
./build/iso-editor
```

Or if installed system-wide:
```bash
iso-editor
```

### Windows

```bash
.\build\Release\iso-editor.exe
```

Make sure Qt DLLs are in the same directory or in PATH.

### macOS

```bash
./build/iso-editor
```

---

## Packaging

### Linux - DEB Package

```bash
cd build
cpack -G DEB
```

Result: `iso-editor-1.0.0-Linux.deb`

Install with:
```bash
sudo dpkg -i iso-editor-1.0.0-Linux.deb
```

### Linux - RPM Package

```bash
cd build
cpack -G RPM
```

Result: `iso-editor-1.0.0-Linux.rpm`

Install with:
```bash
sudo rpm -i iso-editor-1.0.0-Linux.rpm
```

### Linux - AppImage

```bash
# Install linuxdeploy
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage

# Install Qt plugin
wget https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage
chmod +x linuxdeploy-plugin-qt-x86_64.AppImage

# Create AppImage
./linuxdeploy-x86_64.AppImage \
    --executable=build/iso-editor \
    --appdir=AppDir \
    --plugin qt \
    --output appimage
```

Result: `iso-editor-x86_64.AppImage`

### Windows - Installer

```bash
cd build
cpack -G NSIS
```

Result: `iso-editor-1.0.0-win64.exe`

**Requires**: NSIS (Nullsoft Scriptable Install System) installed

### macOS - DMG

```bash
# Build the application
cd build
make

# Create .app bundle
macdeployqt iso-editor.app -dmg
```

Result: `iso-editor.dmg`

---

## CMake Options

| Option | Default | Description |
|--------|---------|-------------|
| `CMAKE_BUILD_TYPE` | `Release` | Build type (Debug, Release, RelWithDebInfo) |
| `BUILD_STATIC` | `OFF` | Build with static Qt libraries |
| `CMAKE_PREFIX_PATH` | (auto) | Path to Qt installation |
| `CMAKE_INSTALL_PREFIX` | `/usr/local` | Installation prefix |

### Example: Debug Build

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

### Example: Custom Qt Location

```bash
cmake -DCMAKE_PREFIX_PATH=/opt/Qt/6.5.3/gcc_64 ..
make
```

### Example: Custom Install Location

```bash
cmake -DCMAKE_INSTALL_PREFIX=/opt/iso-editor ..
make
sudo make install
```

---

## Troubleshooting

### Qt6 not found

**Error**: `Could not find Qt6`

**Solution**:
- Ensure Qt6 is installed
- Set `CMAKE_PREFIX_PATH` to Qt installation directory:
  ```bash
  cmake -DCMAKE_PREFIX_PATH=/path/to/qt6 ..
  ```

### libisofs not found

**Error**: `Could not find libisofs-1`

**Solution**:
- Install libisofs development package:
  - Ubuntu/Debian: `sudo apt-get install libisofs-dev`
  - Fedora: `sudo dnf install libisofs-devel`
  - macOS: `brew install libisofs`
  - Windows: Use vcpkg or build from source

### Missing DLLs on Windows

**Error**: `The code execution cannot proceed because Qt6Core.dll was not found`

**Solution**:
- Run `windeployqt` on the executable:
  ```bash
  C:\Qt\6.5.3\msvc2019_64\bin\windeployqt.exe iso-editor.exe
  ```
- Or copy Qt DLLs manually to the executable directory

### MOC errors

**Error**: `error: undefined reference to 'vtable for ...'`

**Solution**:
- Clean and rebuild:
  ```bash
  rm -rf build
  mkdir build
  cd build
  cmake ..
  make
  ```
- Ensure `CMAKE_AUTOMOC` is `ON` in CMakeLists.txt

---

## Development Build

For active development with faster incremental builds:

```bash
mkdir build-dev
cd build-dev

# Configure for development (Debug + verbose)
cmake -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      ..

# Build with verbose output
make VERBOSE=1

# Run with debugging
gdb ./iso-editor
```

The `compile_commands.json` file enables IDE features like code completion and navigation.

---

## IDE Integration

### Qt Creator

1. Open Qt Creator
2. **File → Open File or Project**
3. Select `CMakeLists.txt`
4. Configure kit (Desktop Qt 6.x.x)
5. Build and run

### Visual Studio Code

1. Install extensions:
   - C/C++
   - CMake Tools
   - Qt tools
2. Open project folder
3. Configure CMake kit
4. Build with CMake Tools

### CLion

1. Open project folder
2. CLion auto-detects CMake project
3. Configure toolchain and Qt paths in **Settings → Build, Execution, Deployment → CMake**
4. Build and run

---

## Binary Size Comparison

| Build Type | Linux | Windows | macOS |
|------------|-------|---------|-------|
| **Dynamic** (shared Qt) | ~5 MB | ~8 MB | ~6 MB |
| **Static** (bundled Qt) | ~20 MB | ~25 MB | ~22 MB |
| **Python (reference)** | ~200 MB | ~220 MB | ~200 MB |

*Static builds include all dependencies except system libraries (libc, OpenGL, etc.)*

---

## Need Help?

- **Documentation**: See [README.md](README.md) and [ROADMAP.md](ROADMAP.md)
- **Issues**: https://github.com/ivenhartford/ISO_editor/issues
- **Qt Documentation**: https://doc.qt.io/qt-6/
- **CMake Documentation**: https://cmake.org/documentation/

---

**Last Updated**: 2025-11-06
**Version**: 1.0.0
