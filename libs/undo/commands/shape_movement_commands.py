#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shape movement and resize commands for Undo/Redo system
"""

from typing import Any, Optional, List
import logging
import copy
from ..command import Command

logger = logging.getLogger(__name__)


class MoveShapeCommand(Command):
    """Command to move a shape"""
    
    def __init__(self, frame_path: str, shape_index: int, old_points: list, new_points: list):
        """
        Initialize MoveShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the shapes list
            old_points: Original points of the shape
            new_points: New points after moving
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_points = copy.deepcopy(old_points)
        self.new_points = copy.deepcopy(new_points)
    
    def execute(self, app: Any) -> bool:
        """Move the shape to new position"""
        try:
            from PyQt5.QtCore import QPointF
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Update shape points
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.points = [QPointF(x, y) for x, y in self.new_points]
                
                # Update canvas
                if hasattr(app.canvas, 'load_shapes'):
                    app.canvas.load_shapes(app.canvas.shapes)
                elif hasattr(app.canvas, 'update'):
                    app.canvas.update()
                
                # Mark as dirty
                app.set_dirty()
                
                # Auto-save if enabled
                if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                    app.save_file()
                
                self.executed = True
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error moving shape: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """Restore original position"""
        try:
            from PyQt5.QtCore import QPointF
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original points
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.points = [QPointF(x, y) for x, y in self.old_points]
                
                # Update canvas
                if hasattr(app.canvas, 'load_shapes'):
                    app.canvas.load_shapes(app.canvas.shapes)
                elif hasattr(app.canvas, 'update'):
                    app.canvas.update()
                
                # Mark as dirty
                app.set_dirty()
                
                # Auto-save if enabled
                if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                    app.save_file()
                
                self.executed = False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error undoing shape move: {e}")
            return False
    
    @property
    def description(self) -> str:
        return f"Move shape"
    
    def can_merge_with(self, other: Command) -> bool:
        """Can merge with another move command for the same shape"""
        if not isinstance(other, MoveShapeCommand):
            return False
        return (self.frame_path == other.frame_path and
                self.shape_index == other.shape_index)
    
    def merge(self, other: Command) -> Command:
        """Merge with another move command"""
        if not self.can_merge_with(other):
            raise ValueError("Cannot merge with this command")
        
        # Keep old_points from self, take new_points from other
        merged = MoveShapeCommand(
            self.frame_path,
            self.shape_index,
            self.old_points,
            other.new_points
        )
        merged.executed = self.executed
        return merged


class ResizeShapeCommand(Command):
    """Command to resize a shape"""
    
    def __init__(self, frame_path: str, shape_index: int, old_points: list, new_points: list):
        """
        Initialize ResizeShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the shapes list
            old_points: Original points of all vertices
            new_points: New points of all vertices after resize
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_points = copy.deepcopy(old_points)
        self.new_points = copy.deepcopy(new_points)
    
    def execute(self, app: Any) -> bool:
        """Resize the shape"""
        try:
            from PyQt5.QtCore import QPointF
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Update all vertex positions
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.points = [QPointF(x, y) for x, y in self.new_points]
                
                # Update canvas
                if hasattr(app.canvas, 'load_shapes'):
                    app.canvas.load_shapes(app.canvas.shapes)
                elif hasattr(app.canvas, 'update'):
                    app.canvas.update()
                
                # Mark as dirty
                app.set_dirty()
                
                # Auto-save if enabled
                if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                    app.save_file()
                
                self.executed = True
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resizing shape: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """Restore original size"""
        try:
            from PyQt5.QtCore import QPointF
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original vertex positions
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.points = [QPointF(x, y) for x, y in self.old_points]
                
                # Update canvas
                if hasattr(app.canvas, 'load_shapes'):
                    app.canvas.load_shapes(app.canvas.shapes)
                elif hasattr(app.canvas, 'update'):
                    app.canvas.update()
                
                # Mark as dirty
                app.set_dirty()
                
                # Auto-save if enabled
                if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                    app.save_file()
                
                self.executed = False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error undoing shape resize: {e}")
            return False
    
    @property
    def description(self) -> str:
        return f"Resize shape"
    
    def can_merge_with(self, other: Command) -> bool:
        """Can merge with another resize command for the same shape"""
        if not isinstance(other, ResizeShapeCommand):
            return False
        return (self.frame_path == other.frame_path and
                self.shape_index == other.shape_index)
    
    def merge(self, other: Command) -> Command:
        """Merge with another resize command"""
        if not self.can_merge_with(other):
            raise ValueError("Cannot merge with this command")
        
        # Keep old_points from self, take new_points from other
        merged = ResizeShapeCommand(
            self.frame_path,
            self.shape_index,
            self.old_points,
            other.new_points
        )
        merged.executed = self.executed
        return merged