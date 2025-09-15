#!/bin/bash
set -e

# This script installs the required dependencies for building on RHEL-based systems.
# Note: The package names are best-effort guesses and may need to be adjusted.

echo "Installing dependencies for RHEL-based systems..."

# Install Development Tools group
sudo dnf groupinstall -y "Development Tools"

# Install other dependencies
sudo dnf install -y \
    cmake \
    pkgconfig \
    qt6-qtbase-devel \
    libcdio-devel \
    libiso9660-devel

echo "Dependencies installed successfully."
