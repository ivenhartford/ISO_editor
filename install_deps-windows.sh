#!/bin/bash
set -e

# This script installs the required dependencies for building on Windows using MSYS2.

echo "Updating package database..."
pacman -Syu --noconfirm

echo "Installing dependencies..."
pacman -S --noconfirm \
    mingw-w64-x86_64-toolchain \
    mingw-w64-x86_64-cmake \
    mingw-w64-x86_64-qt6 \
    mingw-w64-x86_64-libcdio

echo "Dependencies installed successfully."
