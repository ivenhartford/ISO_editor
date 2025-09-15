cmake_minimum_required(VERSION 3.16)
project(ISO_Editor CXX)

# --- C++ Standard ---
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Qt Setup ---
set(CMAKE_AUTOMOC ON)
find_package(Qt6 REQUIRED COMPONENTS Widgets) # For the main app

# --- libcdio Setup ---
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBCDIO REQUIRED libcdio++)
pkg_check_modules(LIBISO9660 REQUIRED libiso9660++)


# --- GUI Application Target ---
add_executable(iso_editor
    src/main.cpp
    src/iso_editor.cpp
    src/save_as_dialog.cpp
    src/properties_dialog.cpp
    src/iso_core.cpp
    src/droppable_tree_widget.cpp
)

target_link_libraries(iso_editor PRIVATE
    Qt6::Widgets
    ${LIBCDIO_LIBRARIES}
    ${LIBISO9660_LIBRARIES}
)

target_include_directories(iso_editor PRIVATE
    ${LIBCDIO_INCLUDE_DIRS}
    ${LIBISO9660_INCLUDE_DIRS}
)


# --- Test Runner Target ---
add_executable(test_runner
    src/test_runner.cpp
    src/iso_core.cpp # Also needs the core logic
)

target_link_libraries(test_runner PRIVATE
    Qt6::Core # For QString, etc.
    ${LIBCDIO_LIBRARIES}
    ${LIBISO9660_LIBRARIES}
)

target_include_directories(test_runner PRIVATE
    ${LIBCDIO_INCLUDE_DIRS}
    ${LIBISO9660_INCLUDE_DIRS}
)
