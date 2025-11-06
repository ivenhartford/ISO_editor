"""
Command pattern implementation for undo/redo functionality.

This module provides command classes for undoable operations in the ISO Editor.
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Command(ABC):
    """
    Abstract base class for all undoable commands.

    Each command must implement execute() to perform the action
    and undo() to reverse the action.
    """

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the command.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def undo(self) -> bool:
        """
        Undo the command.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def description(self) -> str:
        """
        Get a human-readable description of this command.

        Returns:
            str: Description of the command
        """
        pass


class AddFileCommand(Command):
    """Command for adding a file to the ISO."""

    def __init__(self, core, file_path: str, target_node: Dict[str, Any]):
        """
        Initialize the AddFileCommand.

        Args:
            core: The ISOCore instance
            file_path: Path to the file to add
            target_node: The target directory node
        """
        self.core = core
        self.file_path = file_path
        self.target_node = target_node
        self.added_node: Optional[Dict[str, Any]] = None

    def execute(self) -> bool:
        """Add the file to the ISO."""
        try:
            self.core.add_file_to_directory(self.file_path, self.target_node)
            # Find the newly added node (it's the last child with this filename)
            import os
            filename = os.path.basename(self.file_path)
            for node in reversed(self.target_node['children']):
                if node['name'] == filename:
                    self.added_node = node
                    break
            logger.info(f"Executed: Add file '{self.file_path}'")
            return True
        except Exception as e:
            logger.error(f"Failed to execute AddFileCommand: {e}")
            return False

    def undo(self) -> bool:
        """Remove the file from the ISO."""
        try:
            if self.added_node:
                self.core.remove_node(self.added_node)
                logger.info(f"Undone: Add file '{self.file_path}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to undo AddFileCommand: {e}")
            return False

    def description(self) -> str:
        """Get description of this command."""
        import os
        return f"Add file '{os.path.basename(self.file_path)}'"


class RemoveNodeCommand(Command):
    """Command for removing a file or folder from the ISO."""

    def __init__(self, core, node: Dict[str, Any]):
        """
        Initialize the RemoveNodeCommand.

        Args:
            core: The ISOCore instance
            node: The node to remove
        """
        self.core = core
        self.node = node
        self.parent = node.get('parent')
        self.index: Optional[int] = None

    def execute(self) -> bool:
        """Remove the node from the ISO."""
        try:
            # Remember the index so we can restore to the same position
            if self.parent and 'children' in self.parent:
                try:
                    self.index = self.parent['children'].index(self.node)
                except ValueError:
                    self.index = None

            self.core.remove_node(self.node)
            logger.info(f"Executed: Remove '{self.node.get('name')}'")
            return True
        except Exception as e:
            logger.error(f"Failed to execute RemoveNodeCommand: {e}")
            return False

    def undo(self) -> bool:
        """Re-add the node to the ISO."""
        try:
            if self.parent and 'children' in self.parent:
                # Restore to the same position if we know the index
                if self.index is not None and self.index <= len(self.parent['children']):
                    self.parent['children'].insert(self.index, self.node)
                else:
                    self.parent['children'].append(self.node)
                self.core.iso_modified = True
                logger.info(f"Undone: Remove '{self.node.get('name')}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to undo RemoveNodeCommand: {e}")
            return False

    def description(self) -> str:
        """Get description of this command."""
        node_type = "folder" if self.node.get('is_directory') else "file"
        return f"Remove {node_type} '{self.node.get('name')}'"


class AddFolderCommand(Command):
    """Command for adding a folder to the ISO."""

    def __init__(self, core, folder_name: str, target_node: Dict[str, Any]):
        """
        Initialize the AddFolderCommand.

        Args:
            core: The ISOCore instance
            folder_name: Name of the folder to create
            target_node: The target directory node
        """
        self.core = core
        self.folder_name = folder_name
        self.target_node = target_node
        self.added_node: Optional[Dict[str, Any]] = None

    def execute(self) -> bool:
        """Add the folder to the ISO."""
        try:
            self.core.add_folder_to_directory(self.folder_name, self.target_node)
            # Find the newly added folder
            for node in reversed(self.target_node['children']):
                if node['name'] == self.folder_name and node.get('is_directory'):
                    self.added_node = node
                    break
            logger.info(f"Executed: Add folder '{self.folder_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to execute AddFolderCommand: {e}")
            return False

    def undo(self) -> bool:
        """Remove the folder from the ISO."""
        try:
            if self.added_node:
                self.core.remove_node(self.added_node)
                logger.info(f"Undone: Add folder '{self.folder_name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to undo AddFolderCommand: {e}")
            return False

    def description(self) -> str:
        """Get description of this command."""
        return f"Add folder '{self.folder_name}'"


class RenameNodeCommand(Command):
    """Command for renaming a file or folder in the ISO."""

    def __init__(self, node: Dict[str, Any], old_name: str, new_name: str):
        """
        Initialize the RenameNodeCommand.

        Args:
            node: The node to rename
            old_name: The current name
            new_name: The new name
        """
        self.node = node
        self.old_name = old_name
        self.new_name = new_name

    def execute(self) -> bool:
        """Rename the node."""
        try:
            self.node['name'] = self.new_name
            logger.info(f"Executed: Rename '{self.old_name}' to '{self.new_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to execute RenameNodeCommand: {e}")
            return False

    def undo(self) -> bool:
        """Restore the original name."""
        try:
            self.node['name'] = self.old_name
            logger.info(f"Undone: Rename '{self.new_name}' back to '{self.old_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to undo RenameNodeCommand: {e}")
            return False

    def description(self) -> str:
        """Get description of this command."""
        return f"Rename '{self.old_name}' to '{self.new_name}'"


class CommandHistory:
    """
    Manages the undo/redo history using command pattern.
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize the command history.

        Args:
            max_history: Maximum number of commands to keep in history
        """
        self.max_history = max_history
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def execute(self, command: Command) -> bool:
        """
        Execute a command and add it to the history.

        Args:
            command: The command to execute

        Returns:
            bool: True if successful, False otherwise
        """
        if command.execute():
            self.undo_stack.append(command)
            # Clear redo stack when a new command is executed
            self.redo_stack.clear()
            # Limit history size
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
            logger.debug(f"Command executed: {command.description()}")
            return True
        return False

    def undo(self) -> Optional[str]:
        """
        Undo the last command.

        Returns:
            str: Description of the undone command, or None if nothing to undo
        """
        if not self.can_undo():
            return None

        command = self.undo_stack.pop()
        if command.undo():
            self.redo_stack.append(command)
            desc = command.description()
            logger.debug(f"Command undone: {desc}")
            return desc
        else:
            # If undo fails, put the command back
            self.undo_stack.append(command)
            return None

    def redo(self) -> Optional[str]:
        """
        Redo the last undone command.

        Returns:
            str: Description of the redone command, or None if nothing to redo
        """
        if not self.can_redo():
            return None

        command = self.redo_stack.pop()
        if command.execute():
            self.undo_stack.append(command)
            desc = command.description()
            logger.debug(f"Command redone: {desc}")
            return desc
        else:
            # If redo fails, put the command back
            self.redo_stack.append(command)
            return None

    def can_undo(self) -> bool:
        """Check if there are commands to undo."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if there are commands to redo."""
        return len(self.redo_stack) > 0

    def clear(self) -> None:
        """Clear all command history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger.debug("Command history cleared")

    def get_undo_description(self) -> Optional[str]:
        """Get description of the next command that would be undone."""
        if self.can_undo():
            return self.undo_stack[-1].description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """Get description of the next command that would be redone."""
        if self.can_redo():
            return self.redo_stack[-1].description()
        return None
