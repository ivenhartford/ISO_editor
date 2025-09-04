import pytest
from iso_logic import ISOCore
import os

@pytest.fixture
def iso_core():
    """Provides a fresh ISOCore instance for each test."""
    return ISOCore()

def test_initialization(iso_core):
    """Test that ISOCore initializes with an empty root directory."""
    assert iso_core.directory_tree is not None
    assert iso_core.directory_tree['name'] == '/'
    assert iso_core.directory_tree['is_directory'] is True
    assert len(iso_core.directory_tree['children']) == 0
    assert iso_core.iso_modified is False

def test_add_folder(iso_core):
    """Test adding a new folder to the root directory."""
    root_node = iso_core.directory_tree
    folder_name = "NEW_FOLDER"

    assert len(root_node['children']) == 0

    iso_core.add_folder_to_directory(folder_name, root_node)

    assert len(root_node['children']) == 1
    new_folder_node = root_node['children'][0]

    assert new_folder_node['name'] == folder_name
    assert new_folder_node['is_directory'] is True
    assert new_folder_node['parent'] == root_node
    assert iso_core.iso_modified is True

def test_remove_node(iso_core):
    """Test removing a node from the directory tree."""
    root_node = iso_core.directory_tree
    folder_name = "FOLDER_TO_DELETE"

    # Add a folder first
    iso_core.add_folder_to_directory(folder_name, root_node)
    assert len(root_node['children']) == 1
    node_to_remove = root_node['children'][0]

    # Reset modified flag to test the remove operation
    iso_core.iso_modified = False

    # Remove the folder
    iso_core.remove_node(node_to_remove)

    assert len(root_node['children']) == 0
    assert iso_core.iso_modified is True

def test_remove_nonexistent_child(iso_core):
    """Test that removing a node that isn't a child doesn't error and does nothing."""
    root_node = iso_core.directory_tree
    iso_core.add_folder_to_directory("FOLDER1", root_node)

    # Create a standalone node that is not in the tree
    fake_node = {
        'name': 'FAKE',
        'is_directory': True,
        'parent': root_node,
        'children': []
    }

    iso_core.remove_node(fake_node)

    assert len(root_node['children']) == 1
    assert root_node['children'][0]['name'] == "FOLDER1"
