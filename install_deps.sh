#!/bin/bash
set -e

# Update package lists
sudo apt-get update

# Install dependencies, including the C++ compiler, CMake, and Qt.

sudo apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    qt6-base-dev \
    libcdio++-dev \
    libiso9660++-dev

echo "Dependencies installed successfully."
