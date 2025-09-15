#!/bin/bash
set -e

# This script detects the Linux distribution and installs the required dependencies.

if [ -f /etc/debian_version ]; then
    echo "Debian-based system detected. Installing dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        cmake \
        pkg-config \
        qt6-base-dev \
        libcdio++-dev \
        libiso9660-dev
    echo "Dependencies installed successfully."
elif [ -f /etc/redhat-release ]; then
    echo "RHEL-based system detected."
    ./install_deps-rhel.sh
else
    echo "Unsupported Linux distribution."
    exit 1
fi
