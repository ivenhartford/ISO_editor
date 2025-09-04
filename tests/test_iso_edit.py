import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from ISO_edit import ISOEditor

# The QApplication instance is managed automatically by pytest-qt
# The qtbot fixture is also provided automatically.

def test_app_initialization(qtbot):
    """Test that the main window can be created."""
    editor = ISOEditor()
    qtbot.addWidget(editor)  # Add the widget to the qtbot to manage its lifecycle

    # On initialization, the ISO is new but not yet modified by the user
    assert editor.windowTitle() == "ISO Editor"
    assert editor.status_bar.currentMessage() == "View refreshed"

def test_initial_tree_view_state(qtbot):
    """Test that the tree view is populated with the root node on startup."""
    editor = ISOEditor()
    qtbot.addWidget(editor)

    # The refresh_view() is called in __init__
    tree = editor.tree
    assert tree.topLevelItemCount() == 1

    root_item = tree.topLevelItem(0)
    assert root_item.text(0) == '/' # Column 0 is the name
    assert root_item.text(3) == 'Directory' # Column 3 is the type

def test_new_iso_action(qtbot, monkeypatch):
    """Test the 'New ISO' action, mocking the message box."""
    editor = ISOEditor()
    qtbot.addWidget(editor)

    # Mock the QMessageBox.question to always return 'Yes' to avoid blocking
    # This is a bit advanced, but shows how UI testing can be done.
    # For this test, we'll just test the state before and after.

    # Let's add a folder to make the ISO "dirty"
    editor.core.add_folder_to_directory("TEST_DIR", editor.core.directory_tree)
    editor.refresh_view()

    assert len(editor.core.directory_tree['children']) == 1
    assert editor.core.iso_modified is True

    # Mock the save_iso method to simulate a successful save
    def mock_save_iso():
        editor.core.iso_modified = False

    monkeypatch.setattr(editor, 'save_iso', mock_save_iso)
    # Mock the message box to prevent it from blocking the test run
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.question', lambda *args, **kwargs: QMessageBox.Yes)

    # Trigger the new_iso method
    editor.new_iso()

    # Check that the ISO is now clean and empty
    assert len(editor.core.directory_tree['children']) == 0
    assert editor.core.iso_modified is False

    tree = editor.tree
    assert tree.topLevelItemCount() == 1
    assert tree.topLevelItem(0).childCount() == 0
