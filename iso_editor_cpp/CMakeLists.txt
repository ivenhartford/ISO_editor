cmake_minimum_required(VERSION 3.16)
project(ISO_Editor CXX)

# --- C++ Standard ---
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

# --- Find Packages ---
find_package(Qt6 REQUIRED COMPONENTS Widgets)
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBCDIO REQUIRED libcdio++)
pkg_check_modules(LIBISO9660 REQUIRED libiso9660++)

# --- Dependencies via FetchContent ---
include(FetchContent)

# Google Test
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)
enable_testing()

# CUE Parser (non-CMake project)
FetchContent_Declare(
  cueparser
  GIT_REPOSITORY https://github.com/rabbitholecomputing/CUEParser.git
  GIT_TAG        main
)
FetchContent_GetProperties(cueparser)
if(NOT cueparser_POPULATED)
  FetchContent_Populate(cueparser)
endif()


# --- Project Libraries ---

# Core logic library
add_library(iso_core
    src/iso_core.cpp
    ${cueparser_SOURCE_DIR}/src/CUEParser.cpp
)
target_link_libraries(iso_core PRIVATE
    Qt6::Core
    ${LIBCDIO_LIBRARIES}
    ${LIBISO9660_LIBRARIES}
)
target_include_directories(iso_core PUBLIC
    src
    ${LIBCDIO_INCLUDE_DIRS}
    ${LIBISO9660_INCLUDE_DIRS}
    ${cueparser_SOURCE_DIR}/src # Add CUEParser includes
)

# --- GUI Application Target ---
add_executable(iso_editor
    src/main.cpp
    src/iso_editor.cpp
    src/save_as_dialog.cpp
    src/properties_dialog.cpp
    src/droppable_tree_widget.cpp
)
target_link_libraries(iso_editor PRIVATE
    Qt6::Widgets
    iso_core
)

# --- Add Tests Subdirectory ---
add_subdirectory(tests)
