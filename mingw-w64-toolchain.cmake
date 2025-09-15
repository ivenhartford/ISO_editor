# Toolchain file for MinGW-w64 cross-compilation
set(CMAKE_SYSTEM_NAME Windows)

# Specify the cross-compilers
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)

# Specify the resource compiler
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)

# Where to look for target environment headers and libraries
set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)

# Adjust the default find behavior to search for programs in the
# host environment and libraries/headers in the target environment.
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
