#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shape-related commands for Undo/Redo system
"""

from typing import Dict, Any, List, Tuple, Optional
import logging
import copy
from PyQt5.QtCore import QPointF
from ..command import Command
from .composite_command import CompositeCommand

logger = logging.getLogger(__name__)


class AddShapeCommand(Command):
    """Command to add a shape to the canvas"""
    
    def __init__(self, frame_path: str, shape_data: Dict[str, Any]):
        """
        Initialize AddShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_data: Dictionary containing shape information
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_data = copy.deepcopy(shape_data)
        self.shape_index = None
        self.shape_id = None
        self.added_shape = None
    
    def execute(self, app: Any) -> bool:
        """
        Add shape to the canvas
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Import Shape class
            from libs.shape import Shape
            
            # Create shape
            shape = Shape()
            shape.label = self.shape_data.get('label', '')
            
            # Convert points to QPointF
            points = self.shape_data.get('points', [])
            shape.points = [QPointF(x, y) for x, y in points]
            shape.close()
            
            # Set additional properties
            if 'line_color' in self.shape_data:
                shape.line_color = self.shape_data['line_color']
            if 'fill_color' in self.shape_data:
                shape.fill_color = self.shape_data['fill_color']
            if 'difficult' in self.shape_data:
                shape.difficult = self.shape_data['difficult']
            
            # Add to canvas
            app.canvas.shapes.append(shape)
            app.add_label(shape)
            
            # Store reference for undo
            self.shape_index = len(app.canvas.shapes) - 1
            self.shape_id = id(shape)
            self.added_shape = shape
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing AddShapeCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Remove the added shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Remove shape from canvas
            if self.shape_index is not None and self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                app.canvas.shapes.remove(shape)
                
                # Remove from label list
                if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                    item = app.shapes_to_items[shape]
                    if hasattr(app, 'label_list'):
                        row = app.label_list.row(item)
                        app.label_list.takeItem(row)
                    del app.shapes_to_items[shape]
                    if hasattr(app, 'items_to_shapes') and item in app.items_to_shapes:
                        del app.items_to_shapes[item]
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing AddShapeCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        label = self.shape_data.get('label', 'unknown')
        return f"Add shape '{label}'"
    
    def can_merge_with(self, other: Command) -> bool:
        """AddShapeCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("AddShapeCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Adding a shape affects save state"""
        return True


class DeleteShapeCommand(Command):
    """Command to delete a shape from the canvas"""
    
    def __init__(self, frame_path: str, shape_index: int, shape: Any):
        """
        Initialize DeleteShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the shapes list
            shape: The shape object to delete
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_index = shape_index
        
        # Store shape data for restoration
        self.shape_data = {
            'label': shape.label if hasattr(shape, 'label') else '',
            'points': [(p.x(), p.y()) for p in shape.points] if hasattr(shape, 'points') else [],
            'difficult': shape.difficult if hasattr(shape, 'difficult') else False
        }
        
        # Store additional properties if they exist
        if hasattr(shape, 'line_color'):
            self.shape_data['line_color'] = shape.line_color
        if hasattr(shape, 'fill_color'):
            self.shape_data['fill_color'] = shape.fill_color
    
    def execute(self, app: Any) -> bool:
        """
        Delete the shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Remove shape from canvas
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                app.canvas.shapes.remove(shape)
                
                # Remove from label list
                if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                    item = app.shapes_to_items[shape]
                    if hasattr(app, 'label_list'):
                        row = app.label_list.row(item)
                        app.label_list.takeItem(row)
                    del app.shapes_to_items[shape]
                    if hasattr(app, 'items_to_shapes') and item in app.items_to_shapes:
                        del app.items_to_shapes[item]
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing DeleteShapeCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore the deleted shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Import Shape class
            from libs.shape import Shape
            
            # Recreate shape
            shape = Shape()
            shape.label = self.shape_data.get('label', '')
            
            # Convert points to QPointF
            points = self.shape_data.get('points', [])
            shape.points = [QPointF(x, y) for x, y in points]
            shape.close()
            
            # Restore additional properties
            if 'line_color' in self.shape_data:
                shape.line_color = self.shape_data['line_color']
            if 'fill_color' in self.shape_data:
                shape.fill_color = self.shape_data['fill_color']
            if 'difficult' in self.shape_data:
                shape.difficult = self.shape_data['difficult']
            
            # Insert at original position
            app.canvas.shapes.insert(self.shape_index, shape)
            app.add_label(shape)
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing DeleteShapeCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        label = self.shape_data.get('label', 'unknown')
        return f"Delete shape '{label}'"
    
    def can_merge_with(self, other: Command) -> bool:
        """DeleteShapeCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("DeleteShapeCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Deleting a shape affects save state"""
        return True


class MoveShapeCommand(Command):
    """Command to move a shape"""
    
    def __init__(self, frame_path: str, shape_index: int, 
                 old_points: List[Tuple[float, float]], 
                 new_points: List[Tuple[float, float]]):
        """
        Initialize MoveShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the shapes list
            old_points: Original points before move
            new_points: New points after move
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_points = copy.deepcopy(old_points)
        self.new_points = copy.deepcopy(new_points)
    
    def execute(self, app: Any) -> bool:
        """
        Move shape to new position
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Update shape points
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.points = [QPointF(x, y) for x, y in self.new_points]
                
                # Refresh canvas
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
            
        except Exception as e:
            logger.error(f"Error executing MoveShapeCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Move shape back to original position
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original points
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.points = [QPointF(x, y) for x, y in self.old_points]
                
                # Refresh canvas
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
            
        except Exception as e:
            logger.error(f"Error undoing MoveShapeCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Move shape"
    
    def can_merge_with(self, other: Command) -> bool:
        """Check if can merge with another move command"""
        if not isinstance(other, MoveShapeCommand):
            return False
        
        # Can merge if same frame and same shape
        return (self.frame_path == other.frame_path and 
                self.shape_index == other.shape_index)
    
    def merge(self, other: 'MoveShapeCommand') -> 'MoveShapeCommand':
        """Merge with another move command"""
        # Keep original starting position and final ending position
        return MoveShapeCommand(
            self.frame_path,
            self.shape_index,
            self.old_points,  # Keep original starting position
            other.new_points  # Use final ending position
        )
    
    @property
    def affects_save_state(self) -> bool:
        """Moving a shape affects save state"""
        return True


class ResizeShapeCommand(Command):
    """Command to resize a shape"""
    
    def __init__(self, frame_path: str, shape_index: int, 
                 old_rect: Tuple[float, float, float, float],
                 new_rect: Tuple[float, float, float, float]):
        """
        Initialize ResizeShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the shapes list
            old_rect: Original rectangle (x, y, width, height)
            new_rect: New rectangle (x, y, width, height)
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_rect = old_rect
        self.new_rect = new_rect
    
    def execute(self, app: Any) -> bool:
        """
        Resize shape to new size
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Update shape size
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                x, y, width, height = self.new_rect
                
                # Create new rectangle points
                shape.points = [
                    QPointF(x, y),
                    QPointF(x + width, y),
                    QPointF(x + width, y + height),
                    QPointF(x, y + height)
                ]
                
                # Refresh canvas
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
            
        except Exception as e:
            logger.error(f"Error executing ResizeShapeCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Resize shape back to original size
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original size
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                x, y, width, height = self.old_rect
                
                # Restore original rectangle points
                shape.points = [
                    QPointF(x, y),
                    QPointF(x + width, y),
                    QPointF(x + width, y + height),
                    QPointF(x, y + height)
                ]
                
                # Refresh canvas
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
            
        except Exception as e:
            logger.error(f"Error undoing ResizeShapeCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Resize shape"
    
    def can_merge_with(self, other: Command) -> bool:
        """Check if can merge with another resize command"""
        if not isinstance(other, ResizeShapeCommand):
            return False
        
        # Can merge if same frame and same shape
        return (self.frame_path == other.frame_path and 
                self.shape_index == other.shape_index)
    
    def merge(self, other: 'ResizeShapeCommand') -> 'ResizeShapeCommand':
        """Merge with another resize command"""
        # Keep original starting size and final ending size
        return ResizeShapeCommand(
            self.frame_path,
            self.shape_index,
            self.old_rect,  # Keep original size
            other.new_rect  # Use final size
        )
    
    @property
    def affects_save_state(self) -> bool:
        """Resizing a shape affects save state"""
        return True


class DuplicateShapeCommand(Command):
    """Command to duplicate a shape within the same frame"""
    
    def __init__(self, frame_path: str, source_shape: Any):
        """
        Initialize DuplicateShapeCommand
        
        Args:
            frame_path: Path to the frame/image file
            source_shape: The shape to duplicate
        """
        super().__init__()
        self.frame_path = frame_path
        
        # Store source shape data
        self.shape_data = {
            'label': source_shape.label if hasattr(source_shape, 'label') else '',
            'points': [(p.x(), p.y()) for p in source_shape.points] if hasattr(source_shape, 'points') else [],
            'difficult': source_shape.difficult if hasattr(source_shape, 'difficult') else False
        }
        
        # Store additional properties if they exist
        if hasattr(source_shape, 'line_color'):
            self.shape_data['line_color'] = source_shape.line_color
        if hasattr(source_shape, 'fill_color'):
            self.shape_data['fill_color'] = source_shape.fill_color
        
        self.duplicated_shape_index = None
    
    def execute(self, app: Any) -> bool:
        """
        Duplicate the shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Import Shape class
            from libs.shape import Shape
            
            # Create duplicate shape
            shape = Shape()
            shape.label = self.shape_data.get('label', '')
            
            # Convert points to QPointF (slightly offset for visibility)
            points = self.shape_data.get('points', [])
            shape.points = [QPointF(x + 10, y + 10) for x, y in points]  # Offset by 10 pixels
            shape.close()
            
            # Set additional properties
            if 'line_color' in self.shape_data:
                shape.line_color = self.shape_data['line_color']
            if 'fill_color' in self.shape_data:
                shape.fill_color = self.shape_data['fill_color']
            if 'difficult' in self.shape_data:
                shape.difficult = self.shape_data['difficult']
            
            # Add to canvas
            app.canvas.shapes.append(shape)
            app.add_label(shape)
            
            # Store index for undo
            self.duplicated_shape_index = len(app.canvas.shapes) - 1
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing DuplicateShapeCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Remove the duplicated shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Remove duplicated shape
            if self.duplicated_shape_index is not None and self.duplicated_shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.duplicated_shape_index]
                app.canvas.shapes.remove(shape)
                
                # Remove from label list
                if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                    item = app.shapes_to_items[shape]
                    if hasattr(app, 'label_list'):
                        row = app.label_list.row(item)
                        app.label_list.takeItem(row)
                    del app.shapes_to_items[shape]
                    if hasattr(app, 'items_to_shapes') and item in app.items_to_shapes:
                        del app.items_to_shapes[item]
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing DuplicateShapeCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        label = self.shape_data.get('label', 'unknown')
        return f"Duplicate shape '{label}'"
    
    def can_merge_with(self, other: Command) -> bool:
        """DuplicateShapeCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("DuplicateShapeCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Duplicating a shape affects save state"""
        return True


class MultiFrameDuplicateCommand(CompositeCommand):
    """Command to duplicate a shape to multiple frames"""
    
    def __init__(self, source_shape: Any, target_frames: List[str]):
        """
        Initialize MultiFrameDuplicateCommand
        
        Args:
            source_shape: The shape to duplicate
            target_frames: List of frame paths to duplicate to
        """
        # Create AddShapeCommand for each target frame
        shape_data = {
            'label': source_shape.label if hasattr(source_shape, 'label') else '',
            'points': [(p.x(), p.y()) for p in source_shape.points] if hasattr(source_shape, 'points') else [],
            'difficult': source_shape.difficult if hasattr(source_shape, 'difficult') else False
        }
        
        # Store additional properties if they exist
        if hasattr(source_shape, 'line_color'):
            shape_data['line_color'] = source_shape.line_color
        if hasattr(source_shape, 'fill_color'):
            shape_data['fill_color'] = source_shape.fill_color
        
        # Create commands for each frame
        commands = []
        for frame_path in target_frames:
            cmd = AddShapeCommand(frame_path, shape_data)
            commands.append(cmd)
        
        # Initialize composite command
        description = f"Duplicate shape to {len(target_frames)} frames"
        super().__init__(commands, description)