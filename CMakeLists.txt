cmake_minimum_required(VERSION 3.16)
project(iso-editor VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable automatic handling of Qt features
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Find Qt6 packages
find_package(Qt6 REQUIRED COMPONENTS
    Core
    Gui
    Widgets
)

# Find ISO libraries
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBISOFS REQUIRED libisofs-1)
pkg_check_modules(LIBISOBURN REQUIRED libisoburn-1)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${LIBISOFS_INCLUDE_DIRS}
    ${LIBISOBURN_INCLUDE_DIRS}
)

# Source files
set(SOURCES
    src/main.cpp
    src/MainWindow.cpp
    src/ISOCore.cpp
    src/PropertiesDialog.cpp
    src/SaveAsDialog.cpp
    src/DroppableTreeWidget.cpp
    src/CommandHistory.cpp
    src/Constants.cpp
)

# Header files
set(HEADERS
    include/MainWindow.h
    include/core/ISOCore.h
    include/dialogs/PropertiesDialog.h
    include/dialogs/SaveAsDialog.h
    include/widgets/DroppableTreeWidget.h
    include/commands/CommandHistory.h
    include/commands/Command.h
    include/Constants.h
)

# Create executable
add_executable(iso-editor ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(iso-editor
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    ${LIBISOFS_LIBRARIES}
    ${LIBISOBURN_LIBRARIES}
)

# Set compile options
target_compile_options(iso-editor PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    $<$<CONFIG:Debug>:-g -O0>
    $<$<CONFIG:Release>:-O3>
)

# Installation rules
install(TARGETS iso-editor
    RUNTIME DESTINATION bin
)

# Option for static linking
option(BUILD_STATIC "Build with static Qt libraries" OFF)
if(BUILD_STATIC)
    set_target_properties(iso-editor PROPERTIES
        LINK_FLAGS "-static-libgcc -static-libstdc++"
    )
endif()

# CPack configuration for packaging
set(CPACK_PACKAGE_NAME "iso-editor")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_VENDOR "ISO Editor Team")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Professional ISO Editor with Qt6")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")

include(CPack)
