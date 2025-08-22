#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dual label commands for Undo/Redo system
"""

from typing import Any, Optional
import logging
from ..command import Command

logger = logging.getLogger(__name__)


class ChangeDualLabelCommand(Command):
    """Command to change both label1 and label2 of a shape"""
    
    def __init__(self, frame_path: str, shape_index: int,
                 old_label1: str, new_label1: str,
                 old_label2: str, new_label2: str,
                 change_label1: bool = True,
                 change_label2: bool = True):
        """
        Initialize ChangeDualLabelCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the canvas
            old_label1: Previous label1 value
            new_label1: New label1 value
            old_label2: Previous label2 value
            new_label2: New label2 value
            change_label1: Whether to change label1
            change_label2: Whether to change label2
        """
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_label1 = old_label1
        self.new_label1 = new_label1
        self.old_label2 = old_label2
        self.new_label2 = new_label2
        self.change_label1 = change_label1
        self.change_label2 = change_label2
        self.executed = False
    
    def execute(self, app: Any) -> bool:
        """
        Change the dual labels of a shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Get the shape
            if self.shape_index >= len(app.canvas.shapes):
                logger.error(f"Shape index {self.shape_index} out of range")
                return False
            
            shape = app.canvas.shapes[self.shape_index]
            
            # Change labels based on flags
            if self.change_label1:
                shape.label1 = self.new_label1
                shape.label = self.new_label1  # For backward compatibility
            
            if self.change_label2:
                shape.label2 = self.new_label2
            
            # Update the item in the label list
            item = app.shapes_to_items.get(shape)
            if item:
                # Update item text to show both labels
                text_parts = []
                if hasattr(shape, 'label1') and shape.label1:
                    text_parts.append(shape.label1)
                if hasattr(shape, 'label2') and shape.label2:
                    text_parts.append(shape.label2)
                text = " | ".join(text_parts) if len(text_parts) > 1 else " ".join(text_parts)
                item.setText(text)
            
            # Update canvas
            app.canvas.load_shapes(app.canvas.shapes)
            app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            logger.debug(f"Changed dual labels for shape {self.shape_index}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing dual labels: {e}")
            return False
    
    def redo(self, app: Any) -> bool:
        """Redo the dual label change"""
        return self.execute(app)
    
    def undo(self, app: Any) -> bool:
        """
        Undo the dual label change
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Get the shape
            if self.shape_index >= len(app.canvas.shapes):
                logger.error(f"Shape index {self.shape_index} out of range")
                return False
            
            shape = app.canvas.shapes[self.shape_index]
            
            # Restore original labels based on flags
            if self.change_label1:
                shape.label1 = self.old_label1
                shape.label = self.old_label1  # For backward compatibility
            
            if self.change_label2:
                shape.label2 = self.old_label2
            
            # Update the item in the label list
            item = app.shapes_to_items.get(shape)
            if item:
                # Update item text to show both labels
                text_parts = []
                if hasattr(shape, 'label1') and shape.label1:
                    text_parts.append(shape.label1)
                if hasattr(shape, 'label2') and shape.label2:
                    text_parts.append(shape.label2)
                text = " | ".join(text_parts) if len(text_parts) > 1 else " ".join(text_parts)
                item.setText(text)
            
            # Update canvas
            app.canvas.load_shapes(app.canvas.shapes)
            app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            logger.debug(f"Undid dual label change for shape {self.shape_index}")
            return True
            
        except Exception as e:
            logger.error(f"Error undoing dual label change: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        changes = []
        if self.change_label1:
            changes.append(f"Label1: '{self.old_label1}' -> '{self.new_label1}'")
        if self.change_label2:
            changes.append(f"Label2: '{self.old_label2}' -> '{self.new_label2}'")
        return f"Change {', '.join(changes)}"
    
    def affects_save_state(self) -> bool:
        """Whether this command affects the save state"""
        return True
    
    def can_merge_with(self, other: 'Command') -> bool:
        """Check if this command can be merged with another"""
        return False
    
    def merge(self, other: 'Command') -> 'Command':
        """Merge this command with another"""
        return self