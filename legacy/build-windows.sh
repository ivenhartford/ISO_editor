#!/bin/bash
set -e

# This script is a template for cross-compiling the application for Windows from Linux.
# It requires a cross-compiled version of Qt6, which is not available in the default
# repositories and would need to be built from source.
#
# For a more reliable way to build on Windows, please see README.windows.md.

echo "NOTE: This script is a template and requires a cross-compiled Qt6."
echo "Please see README.windows.md for instructions on building natively on Windows."
exit 1

# Create build directory for Windows build
mkdir -p iso_editor_cpp/build_windows
cd iso_editor_cpp/build_windows

# Configure and build using the MinGW-w64 toolchain
# You would need to point CMake to your cross-compiled Qt6 installation, e.g.:
#   -DCMAKE_PREFIX_PATH=/path/to/cross/compiled/qt6
cmake -DCMAKE_TOOLCHAIN_FILE=../../mingw-w64-toolchain.cmake ..
make -j$(nproc)

echo "Windows build complete. The executable is in iso_editor_cpp/build_windows/iso_editor.exe"
