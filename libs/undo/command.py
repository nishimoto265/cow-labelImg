#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command base class for Undo/Redo system
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import time


class Command(ABC):
    """Abstract base class for all commands"""
    
    def __init__(self):
        """Initialize command"""
        self.executed = False
        self.timestamp = None
        self.command_id = None
    
    @abstractmethod
    def execute(self, app: Any) -> bool:
        """
        Execute the command
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def undo(self, app: Any) -> bool:
        """
        Undo the command
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get command description for UI/debugging
        
        Returns:
            str: Description of the command
        """
        pass
    
    @abstractmethod
    def can_merge_with(self, other: 'Command') -> bool:
        """
        Check if this command can be merged with another
        
        Args:
            other: Another command
            
        Returns:
            bool: True if can merge, False otherwise
        """
        pass
    
    @abstractmethod
    def merge(self, other: 'Command') -> 'Command':
        """
        Merge this command with another
        
        Args:
            other: Another command to merge with
            
        Returns:
            Command: A new merged command
        """
        pass
    
    @property
    @abstractmethod
    def affects_save_state(self) -> bool:
        """
        Check if this command affects the save state
        
        Returns:
            bool: True if affects save state, False otherwise
        """
        pass
    
    def __str__(self):
        """String representation"""
        return self.description
    
    def __repr__(self):
        """Detailed representation"""
        return f"{self.__class__.__name__}(description='{self.description}', executed={self.executed})"