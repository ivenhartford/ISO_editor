#!/bin/bash
set -e

# Create build directory
mkdir -p iso_editor_cpp/build
cd iso_editor_cpp/build

# Configure and build
cmake ..
make -j$(nproc)

echo "Build complete. The executable is in iso_editor_cpp/build/iso_editor"
