import pytest
from iso_logic import ISOCore
import os

@pytest.fixture
def iso_core():
    """Provides a fresh ISOCore instance for each test."""
    return ISOCore()

def test_add_file(iso_core, tmp_path):
    """Test adding a file to the root directory."""
    root_node = iso_core.directory_tree
    file_name = "test.txt"
    file_content = b"hello world"
    file_path = tmp_path / file_name
    file_path.write_bytes(file_content)

    assert len(root_node['children']) == 0

    iso_core.add_file_to_directory(str(file_path), root_node)

    assert len(root_node['children']) == 1
    new_file_node = root_node['children'][0]

    assert new_file_node['name'] == file_name
    assert new_file_node['is_directory'] is False
    assert new_file_node['parent'] == root_node
    assert new_file_node['size'] == len(file_content)
    assert iso_core.iso_modified is True

def test_remove_file(iso_core, tmp_path):
    """Test removing a file from the root directory."""
    root_node = iso_core.directory_tree
    file_name = "test.txt"
    file_content = b"hello world"
    file_path = tmp_path / file_name
    file_path.write_bytes(file_content)

    iso_core.add_file_to_directory(str(file_path), root_node)
    assert len(root_node['children']) == 1
    node_to_remove = root_node['children'][0]

    iso_core.iso_modified = False
    iso_core.remove_node(node_to_remove)

    assert len(root_node['children']) == 0
    assert iso_core.iso_modified is True

def test_add_folder_to_subdir(iso_core):
    """Test adding a folder to a sub-directory."""
    root_node = iso_core.directory_tree
    iso_core.add_folder_to_directory("SUBDIR", root_node)
    subdir_node = root_node['children'][0]

    iso_core.add_folder_to_directory("NESTED_FOLDER", subdir_node)

    assert len(subdir_node['children']) == 1
    nested_folder_node = subdir_node['children'][0]
    assert nested_folder_node['name'] == "NESTED_FOLDER"
    assert nested_folder_node['is_directory'] is True
    assert nested_folder_node['parent'] == subdir_node

def test_add_file_to_subdir(iso_core, tmp_path):
    """Test adding a file to a sub-directory."""
    root_node = iso_core.directory_tree
    iso_core.add_folder_to_directory("SUBDIR", root_node)
    subdir_node = root_node['children'][0]

    file_name = "nested.txt"
    file_content = b"nested content"
    file_path = tmp_path / file_name
    file_path.write_bytes(file_content)

    iso_core.add_file_to_directory(str(file_path), subdir_node)

    assert len(subdir_node['children']) == 1
    nested_file_node = subdir_node['children'][0]
    assert nested_file_node['name'] == file_name
    assert nested_file_node['is_directory'] is False
    assert nested_file_node['parent'] == subdir_node
    assert nested_file_node['size'] == len(file_content)

def test_add_duplicate_file_overwrites(iso_core, tmp_path):
    """Test that adding a file with the same name overwrites the original."""
    root_node = iso_core.directory_tree
    file_name = "test.txt"

    # Add the first file
    original_content = b"original"
    original_path = tmp_path / file_name
    original_path.write_bytes(original_content)
    iso_core.add_file_to_directory(str(original_path), root_node)

    assert len(root_node['children']) == 1
    assert root_node['children'][0]['size'] == len(original_content)

    # Add the second file with the same name
    new_content = b"new content is longer"
    new_path = tmp_path / "new_test.txt"
    new_path.write_bytes(new_content)
    os.rename(new_path, tmp_path / file_name) # Ensure it has the same name

    iso_core.add_file_to_directory(str(tmp_path / file_name), root_node)

    assert len(root_node['children']) == 1
    assert root_node['children'][0]['size'] == len(new_content)

def test_add_file_to_file_node(iso_core, tmp_path):
    """Test that adding a file to a node that is a file fails gracefully."""
    root_node = iso_core.directory_tree
    file_name = "test.txt"
    file_content = b"hello world"
    file_path = tmp_path / file_name
    file_path.write_bytes(file_content)

    iso_core.add_file_to_directory(str(file_path), root_node)
    file_node = root_node['children'][0]

    another_file_name = "another.txt"
    another_file_path = tmp_path / another_file_name
    another_file_path.write_bytes(b"another file")

    # This should not raise an exception, but it also should not add the file.
    # The logic in ISOCore will traverse up to the parent, which is root.
    iso_core.add_file_to_directory(str(another_file_path), file_node)

    assert len(root_node['children']) == 2

def test_add_duplicate_folder(iso_core):
    """Test that adding a folder with a name that already exists is handled."""
    root_node = iso_core.directory_tree
    folder_name = "DUPLICATE"
    iso_core.add_folder_to_directory(folder_name, root_node)

    # In a correct implementation, this should probably raise an error
    # or be ignored. For now, we'll test the current behavior, which
    # is to add a second folder with the same name.
    iso_core.add_folder_to_directory(folder_name, root_node)

    # The new implementation should not add a duplicate folder.
    assert len(root_node['children']) == 1

def test_calculate_next_extent_location(iso_core):
    """Test that the next extent location is calculated correctly."""
    # Initially, it should be 10, as the root directory is at 0.
    iso_core.calculate_next_extent_location()
    assert iso_core.next_extent_location == 10

    # Add a file, which will have an extent location of 0 since it's new,
    # but the next extent should be recalculated.
    root_node = iso_core.directory_tree
    root_node['children'].append({
        'name': 'file1.txt', 'is_directory': False, 'size': 100,
        'extent_location': 20, 'children': [], 'parent': root_node
    })
    root_node['children'].append({
        'name': 'file2.txt', 'is_directory': False, 'size': 100,
        'extent_location': 30, 'children': [], 'parent': root_node
    })

    iso_core.calculate_next_extent_location()
    assert iso_core.next_extent_location == 40

def test_get_file_data_for_new_file(iso_core):
    """Test getting the data for a newly added file."""
    root_node = iso_core.directory_tree
    file_data_content = b"new file data"
    new_node = {
        'name': 'new_file.txt', 'is_directory': False, 'is_hidden': False,
        'size': len(file_data_content), 'date': '2025-01-01', 'extent_location': 0,
        'children': [], 'parent': root_node, 'file_data': file_data_content, 'is_new': True
    }
    root_node['children'].append(new_node)

    retrieved_data = iso_core.get_file_data(new_node)
    assert retrieved_data == file_data_content

def test_get_file_data_for_nonexistent_file(iso_core):
    """Test getting data for a file that is not new and has no open ISO."""
    node = {'name': 'no_file.txt', 'is_directory': False, 'size': 100, 'extent_location': 100}
    data = iso_core.get_file_data(node)
    assert data == b''

def test_remove_node_with_no_parent(iso_core):
    """Test that removing a node with no parent does not error."""
    node = {'name': 'no_parent.txt'}
    # This should not raise an exception
    iso_core.remove_node(node)

def test_load_iso_after_save(iso_core, tmp_path):
    """
    Test that loading an ISO after saving it results in the same structure.
    This is an integration test for the parser and builder.
    """
    # 1. Build a known structure
    root_node = iso_core.directory_tree
    iso_core.add_folder_to_directory("DIR1", root_node)

    file1_content = b"file1"
    file1_path = tmp_path / "file1.txt"
    file1_path.write_bytes(file1_content)
    iso_core.add_file_to_directory(str(file1_path), root_node.get('children')[0])

    file2_content = b"file2"
    file2_path = tmp_path / "file2.txt"
    file2_path.write_bytes(file2_content)
    iso_core.add_file_to_directory(str(file2_path), root_node)

    # 2. Save the ISO
    output_iso_path = tmp_path / "test.iso"
    iso_core.save_iso(str(output_iso_path), use_joliet=True, use_rock_ridge=True)

    # 3. Load the ISO into a new ISOCore instance
    new_iso_core = ISOCore()
    new_iso_core.load_iso(str(output_iso_path))

    # 4. Assert the structure is the same
    new_root = new_iso_core.directory_tree
    assert len(new_root['children']) == 2

    dir1 = next((c for c in new_root['children'] if c['name'] == 'DIR1'), None)
    assert dir1 is not None
    assert dir1['is_directory'] is True

    file2 = next((c for c in new_root['children'] if c['name'] == 'file2.txt'), None)
    assert file2 is not None
    assert file2['is_directory'] is False
    assert file2['size'] == len(file2_content)

    assert len(dir1['children']) == 1
    file1 = dir1['children'][0]
    assert file1['name'] == 'file1.txt'
    assert file1['is_directory'] is False
    assert file1['size'] == len(file1_content)

    # Also test get_file_data on the loaded ISO
    assert new_iso_core.get_file_data(file1) == file1_content
    assert new_iso_core.get_file_data(file2) == file2_content

def test_load_nonexistent_iso(iso_core):
    """Test that loading a non-existent ISO raises an error."""
    with pytest.raises(IOError):
        iso_core.load_iso("nonexistent.iso")

def test_load_invalid_iso(iso_core, tmp_path):
    """Test that loading an invalid ISO file raises an error."""
    invalid_iso_path = tmp_path / "invalid.iso"
    invalid_iso_path.write_bytes(b"this is not an iso file")
    with pytest.raises(Exception):
        iso_core.load_iso(str(invalid_iso_path))

def test_close_iso(iso_core, tmp_path):
    """Test that the close_iso method closes the file handle."""
    # First, create and load a valid ISO to have an open file handle
    iso_path = tmp_path / "test.iso"
    iso_core.save_iso(str(iso_path), use_joliet=False, use_rock_ridge=False)

    # Load it to open the handle
    loaded_core = ISOCore()
    loaded_core.load_iso(str(iso_path))
    assert loaded_core.iso_file_handle is not None
    assert not loaded_core.iso_file_handle.closed

    # Close it
    loaded_core.close_iso()
    assert loaded_core.iso_file_handle is None
