#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UndoManager for managing command history
"""

from typing import List, Optional, Any
import time
import logging
from .command import Command

logger = logging.getLogger(__name__)


class UndoManager:
    """Manages undo/redo history"""
    
    def __init__(self, app: Any, max_history: int = 100):
        """
        Initialize UndoManager
        
        Args:
            app: MainWindow instance
            max_history: Maximum number of commands to keep in history
        """
        self.app = app
        self.history: List[Command] = []
        self.current_index = -1
        self.max_history = max_history
        self.merge_timeout = 500  # milliseconds
        self.last_merge_time = 0
    
    def execute_command(self, command: Command) -> bool:
        """
        Execute a command and add it to history
        
        Args:
            command: Command to execute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if we can merge with the last command
            if self.can_merge_last(command):
                merged = self.merge_with_last(command)
                if merged:
                    # The merge already updated history, just update time
                    self.last_merge_time = time.time() * 1000
                    return True
            
            # Truncate history after current position
            self.history = self.history[:self.current_index + 1]
            
            # Execute the command
            if not command.execute(self.app):
                return False
            
            # Add to history
            command.timestamp = time.time()
            self.history.append(command)
            self.current_index += 1
            self.last_merge_time = time.time() * 1000
            
            # Limit history size
            if len(self.history) > self.max_history:
                self.history.pop(0)
                self.current_index -= 1
            
            # Update UI
            self.update_ui()
            
            logger.debug(f"Executed command: {command.description}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return False
    
    def undo(self) -> bool:
        """
        Undo the last command
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.can_undo():
            return False
        
        try:
            command = self.history[self.current_index]
            if command.undo(self.app):
                self.current_index -= 1
                self.update_ui()
                logger.debug(f"Undid command: {command.description}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error undoing command: {e}")
            return False
    
    def redo(self) -> bool:
        """
        Redo the next command
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.can_redo():
            return False
        
        try:
            self.current_index += 1
            command = self.history[self.current_index]
            if command.execute(self.app):
                self.update_ui()
                logger.debug(f"Redid command: {command.description}")
                return True
            
            # If redo failed, restore index
            self.current_index -= 1
            return False
            
        except Exception as e:
            logger.error(f"Error redoing command: {e}")
            self.current_index -= 1
            return False
    
    def can_undo(self) -> bool:
        """
        Check if undo is possible
        
        Returns:
            bool: True if can undo, False otherwise
        """
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """
        Check if redo is possible
        
        Returns:
            bool: True if can redo, False otherwise
        """
        return self.current_index < len(self.history) - 1
    
    def can_merge_last(self, command: Command) -> bool:
        """
        Check if the last command can be merged with the given command
        
        Args:
            command: Command to check for merging
            
        Returns:
            bool: True if can merge, False otherwise
        """
        if self.current_index < 0:
            return False
        
        # Check time since last command
        current_time = time.time() * 1000
        if current_time - self.last_merge_time > self.merge_timeout:
            return False
        
        last_command = self.history[self.current_index]
        return last_command.can_merge_with(command)
    
    def merge_with_last(self, command: Command) -> Optional[Command]:
        """
        Merge the given command with the last command in history
        
        Args:
            command: Command to merge
            
        Returns:
            Command: Merged command or None if merge failed
        """
        if self.current_index < 0:
            return None
        
        try:
            last_command = self.history[self.current_index]
            merged = last_command.merge(command)
            
            # Replace the last command with the merged one
            self.history[self.current_index] = merged
            self.last_merge_time = time.time() * 1000
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging commands: {e}")
            return None
    
    def update_ui(self):
        """Update UI elements based on current state"""
        if hasattr(self.app, 'actions'):
            if hasattr(self.app.actions, 'undo') and self.app.actions.undo:
                self.app.actions.undo.setEnabled(self.can_undo())
            if hasattr(self.app.actions, 'redo') and self.app.actions.redo:
                self.app.actions.redo.setEnabled(self.can_redo())
    
    def clear(self):
        """Clear all history"""
        self.history.clear()
        self.current_index = -1
        self.update_ui()
        logger.debug("Cleared undo history")
    
    def get_history_info(self) -> List[str]:
        """
        Get information about the history for debugging
        
        Returns:
            List[str]: List of command descriptions with current position marked
        """
        info = []
        for i, cmd in enumerate(self.history):
            marker = " <-- current" if i == self.current_index else ""
            info.append(f"{i}: {cmd.description}{marker}")
        return info
    
    def __str__(self):
        """String representation"""
        return f"UndoManager(history={len(self.history)}, current={self.current_index})"
    
    def __repr__(self):
        """Detailed representation"""
        return f"UndoManager(history={len(self.history)}, current={self.current_index}, can_undo={self.can_undo()}, can_redo={self.can_redo()})"