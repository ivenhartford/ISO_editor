# Building on Windows (Recommended Method)

This guide explains how to build the ISO Editor application on a native Windows environment. **This is the recommended method for building on Windows.**

The easiest way to set up a build environment is to use MSYS2, which provides a Unix-like shell and a package manager (`pacman`) to install the required dependencies.

## 1. Install MSYS2

Download and install MSYS2 from the official website: [https://www.msys2.org/](https://www.msys2.org/)

Follow the installation instructions on the website. After installation, open the **MSYS2 MINGW64** terminal for all the following steps.

## 2. Install Dependencies

From the MSYS2 MINGW64 terminal, update the package database and install the required dependencies by running the following command:

```bash
pacman -Syu --noconfirm
pacman -S --noconfirm \
    mingw-w64-x86_64-toolchain \
    mingw-w64-x86_64-cmake \
    mingw-w64-x86_64-qt6 \
    mingw-w64-x86_64-libcdio
```

This will install the C++ compiler (as part of the `toolchain`), CMake, Qt6, and the required C++ libraries.


## 3. Build the Application

Once the dependencies are installed, you can build the application.

1.  Clone the repository to your local machine.
2.  Open the MSYS2 MINGW64 terminal and navigate to the root of the repository.
3.  Run the following commands to build the application:

```bash
./build.sh
```

The executable, `iso_editor.exe`, will be located in the `iso_editor_cpp/build` directory.
