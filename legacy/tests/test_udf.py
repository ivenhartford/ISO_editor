import pytest
from iso_logic import ISOCore
import os

@pytest.fixture
def iso_core():
    """Provides a fresh ISOCore instance for each test."""
    return ISOCore()

def test_create_and_load_udf_iso(iso_core, tmp_path):
    """Test that an ISO with UDF support can be created and loaded."""
    # 1. Build a simple structure
    root_node = iso_core.directory_tree
    file_name = "test_udf.txt"
    file_content = b"This is a UDF test file."

    file_path = tmp_path / file_name
    file_path.write_bytes(file_content)

    iso_core.add_file_to_directory(str(file_path), root_node)

    # 2. Save the ISO with UDF enabled
    output_iso_path = tmp_path / "test_udf.iso"
    # The UDF support is now enabled by default in the builder
    iso_core.save_iso(str(output_iso_path), use_joliet=True, use_rock_ridge=True)

    # 3. Load the ISO into a new ISOCore instance
    new_iso_core = ISOCore()
    new_iso_core.load_iso(str(output_iso_path))

    # 4. Assert that the ISO has UDF support
    assert new_iso_core._pycdlib_instance.has_udf() is True

    # 5. Assert the structure and content are correct
    new_root = new_iso_core.directory_tree
    assert len(new_root['children']) == 1

    file_node = new_root['children'][0]
    assert file_node['name'] == file_name
    assert file_node['size'] == len(file_content)

    retrieved_data = new_iso_core.get_file_data(file_node)
    assert retrieved_data == file_content
