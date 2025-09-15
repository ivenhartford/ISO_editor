# Add the executable for the tests
add_executable(core_tests
    test_iso_core.cpp
)

# Link against our core library and Google Test
target_link_libraries(core_tests PRIVATE
    iso_core
    GTest::gtest_main
    Qt6::Core
)

# Include Google Test and add the tests to CTest
include(GoogleTest)
gtest_discover_tests(core_tests)
