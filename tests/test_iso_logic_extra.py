import pytest
from iso_logic import ISOCore
import os
import re

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
    # Use a different name for creation, then rename to ensure it's a different file
    new_path.write_bytes(new_content)
    os.rename(new_path, tmp_path / file_name)

    iso_core.add_file_to_directory(str(tmp_path / file_name), root_node)

    # The list of children should still be 1, as the file is replaced.
    assert len(root_node['children']) == 1
    # The size should be updated to the new file's size.
    assert root_node['children'][0]['size'] == len(new_content)
    # The file data should be the new content.
    assert root_node['children'][0]['file_data'] == new_content

def test_add_file_to_file_node(iso_core, tmp_path):
    """Test that adding a file to a node that is a file adds it to the parent directory."""
    root_node = iso_core.directory_tree
    # Add a file to the root
    file1_path = tmp_path / "file1.txt"
    file1_path.write_bytes(b"file1 content")
    iso_core.add_file_to_directory(str(file1_path), root_node)

    file_node = root_node['children'][0]
    assert file_node['is_directory'] is False

    # Create a second file to add
    another_file_path = tmp_path / "another.txt"
    another_file_path.write_bytes(b"another file")

    # Attempt to add the second file, targeting the first file node
    iso_core.add_file_to_directory(str(another_file_path), file_node)

    # The file should have been added to the *parent* of the target node (the root)
    assert len(root_node['children']) == 2
    assert root_node['children'][0]['name'] == 'file1.txt'
    assert root_node['children'][1]['name'] == 'another.txt'

def test_add_duplicate_folder_is_ignored(iso_core):
    """Test that adding a folder with a name that already exists is ignored."""
    root_node = iso_core.directory_tree
    folder_name = "DUPLICATE"
    iso_core.add_folder_to_directory(folder_name, root_node)
    assert len(root_node['children']) == 1

    # Attempt to add the same folder again
    iso_core.add_folder_to_directory(folder_name, root_node)

    # The number of children should remain 1
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

def test_get_node_path(iso_core):
    """Test the get_node_path utility function."""
    root = iso_core.directory_tree
    assert iso_core.get_node_path(root) == '/'

    iso_core.add_folder_to_directory("DIR1", root)
    dir1_node = root['children'][0]
    assert iso_core.get_node_path(dir1_node) == '/DIR1'

    iso_core.add_folder_to_directory("DIR2", dir1_node)
    dir2_node = dir1_node['children'][0]
    assert iso_core.get_node_path(dir2_node) == '/DIR1/DIR2'

    # Create a fake file node to test file paths
    file_node = {'name': 'file.txt', 'parent': dir2_node}
    assert iso_core.get_node_path(file_node) == '/DIR1/DIR2/file.txt'

def sanitize_for_iso9660(name):
    # A simplified sanitizer for testing purposes.
    # Replace invalid characters with underscores.
    return re.sub(r'[^A-Z0-9_]', '_', name.upper())

def test_complex_load_iso_after_save(iso_core, tmp_path):
    """
    Test a more complex save/load cycle to better verify the parser and builder.
    """
    # 1. Build a complex structure
    root_node = iso_core.directory_tree
    # Use names that are valid for Joliet/RR but need sanitizing for base ISO9660
    dir1_name = "dIR1"
    long_dir_name = "long_directory_name" # Changed to be valid
    long_file_name = "long file name with spaces.txt"

    iso_core.add_folder_to_directory(dir1_name, root_node)
    iso_core.add_folder_to_directory(long_dir_name, root_node)

    dir1_node = next(c for c in root_node['children'] if c['name'] == dir1_name)
    long_dir_node = next(c for c in root_node['children'] if c['name'] == long_dir_name)

    # Add a file with a long name and spaces
    long_file_content = b"long file content"
    long_file_path = tmp_path / long_file_name
    long_file_path.write_bytes(long_file_content)
    iso_core.add_file_to_directory(str(long_file_path), root_node)

    # Add a nested file
    nested_content = b"nested"
    nested_path = tmp_path / "nested.dat"
    nested_path.write_bytes(nested_content)
    iso_core.add_file_to_directory(str(nested_path), dir1_node)

    # Add a file to the other directory
    other_content = b"other"
    other_path = tmp_path / "other.bin"
    other_path.write_bytes(other_content)
    iso_core.add_file_to_directory(str(other_path), long_dir_node)

    # 2. Save the ISO (Joliet and Rock Ridge are important here)
    output_iso_path = tmp_path / "test_complex.iso"
    iso_core.save_iso(str(output_iso_path), use_joliet=True, use_rock_ridge=True)

    # 3. Load the ISO into a new ISOCore instance
    new_iso_core = ISOCore()
    new_iso_core.load_iso(str(output_iso_path))

    # 4. Assert the structure and content are identical
    new_root = new_iso_core.directory_tree
    # The root should contain the two directories and one file
    assert len(new_root['children']) == 3

    # Find nodes (names should be preserved by Rock Ridge/Joliet)
    new_dir1 = next((c for c in new_root['children'] if c['name'] == dir1_name), None)
    new_long_dir = next((c for c in new_root['children'] if c['name'] == long_dir_name), None)
    new_long_file = next((c for c in new_root['children'] if c['name'] == long_file_name), None)

    assert new_dir1 is not None and new_dir1['is_directory']
    assert new_long_dir is not None and new_long_dir['is_directory']
    assert new_long_file is not None and not new_long_file['is_directory']

    assert new_long_file['size'] == len(long_file_content)
    assert new_iso_core.get_file_data(new_long_file) == long_file_content

    assert len(new_dir1['children']) == 1
    nested_file_node = new_dir1['children'][0]
    assert nested_file_node['name'] == 'nested.dat'
    assert nested_file_node['size'] == len(nested_content)
    assert new_iso_core.get_file_data(nested_file_node) == nested_content

    assert len(new_long_dir['children']) == 1
    other_file_node = new_long_dir['children'][0]
    assert other_file_node['name'] == 'other.bin'
    assert other_file_node['size'] == len(other_content)
    assert new_iso_core.get_file_data(other_file_node) == other_content

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

def test_close_iso_no_file(iso_core):
    """Test that calling close_iso when no file is open does not error."""
    try:
        iso_core.close_iso()
    except Exception as e:
        pytest.fail(f"close_iso() raised an exception when no file was open: {e}")
