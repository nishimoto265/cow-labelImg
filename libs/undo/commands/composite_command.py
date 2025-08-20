#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CompositeCommand for handling multiple commands as a single unit
"""

from typing import List, Any
import logging
from ..command import Command

logger = logging.getLogger(__name__)


class CompositeCommand(Command):
    """Composite command that executes multiple commands as a single unit"""
    
    def __init__(self, commands: List[Command], description: str = None):
        """
        Initialize CompositeCommand
        
        Args:
            commands: List of commands to execute
            description: Optional description for the composite operation
        """
        super().__init__()
        self.commands = commands
        self._description = description or "Composite operation"
    
    def execute(self, app: Any) -> bool:
        """
        Execute all commands in order
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if all commands executed successfully, False otherwise
        """
        executed_commands = []
        
        try:
            for cmd in self.commands:
                if not cmd.execute(app):
                    # If a command fails, rollback all executed commands
                    logger.warning(f"Command failed: {cmd.description}")
                    for executed_cmd in reversed(executed_commands):
                        try:
                            executed_cmd.undo(app)
                        except Exception as rollback_error:
                            logger.error(f"Error during rollback: {rollback_error}")
                    return False
                executed_commands.append(cmd)
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing composite command: {e}")
            # Rollback on exception
            for executed_cmd in reversed(executed_commands):
                try:
                    executed_cmd.undo(app)
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Undo all commands in reverse order
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if all commands undone successfully, False otherwise
        """
        try:
            # Undo in reverse order
            for cmd in reversed(self.commands):
                if not cmd.undo(app):
                    logger.warning(f"Failed to undo command: {cmd.description}")
                    return False
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing composite command: {e}")
            return False
    
    @property
    def description(self) -> str:
        """
        Get command description
        
        Returns:
            str: Description of the composite operation
        """
        return self._description
    
    def can_merge_with(self, other: Command) -> bool:
        """
        Composite commands generally don't merge
        
        Args:
            other: Another command
            
        Returns:
            bool: Always False for composite commands
        """
        return False
    
    def merge(self, other: Command) -> Command:
        """
        Merge is not supported for composite commands
        
        Args:
            other: Another command
            
        Raises:
            NotImplementedError: Always raised
        """
        raise NotImplementedError("CompositeCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """
        Check if any contained command affects save state
        
        Returns:
            bool: True if any command affects save state, False otherwise
        """
        return any(cmd.affects_save_state for cmd in self.commands)
    
    def __len__(self):
        """Get number of commands"""
        return len(self.commands)
    
    def __repr__(self):
        """Detailed representation"""
        return f"CompositeCommand(commands={len(self.commands)}, description='{self.description}')"