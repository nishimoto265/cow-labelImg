#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Label-related commands for Undo/Redo system
"""

from typing import Any, List, Optional, Dict
import logging
import copy
from ..command import Command
from .composite_command import CompositeCommand

logger = logging.getLogger(__name__)


class ChangeLabelCommand(Command):
    """Command to change a shape's label"""
    
    def __init__(self, frame_path: str, shape_index: int, old_label: str, new_label: str):
        """
        Initialize ChangeLabelCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_index: Index of the shape in the shapes list
            old_label: Original label
            new_label: New label to apply
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_label = old_label
        self.new_label = new_label
    
    def execute(self, app: Any) -> bool:
        """
        Change the shape's label
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Change label
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.label = self.new_label
                
                # Update list item if exists
                if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                    item = app.shapes_to_items[shape]
                    item.setText(self.new_label)
                    
                    # Update background color based on label
                    try:
                        from libs.utils import generate_color_by_text
                        item.setBackground(generate_color_by_text(self.new_label))
                        shape.line_color = generate_color_by_text(self.new_label)
                        shape.fill_color = generate_color_by_text(self.new_label)
                    except ImportError:
                        pass
            
            # Update combo box
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Update canvas
            if hasattr(app.canvas, 'update'):
                app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing ChangeLabelCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore the original label
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original label
            if self.shape_index < len(app.canvas.shapes):
                shape = app.canvas.shapes[self.shape_index]
                shape.label = self.old_label
                
                # Update list item if exists
                if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                    item = app.shapes_to_items[shape]
                    item.setText(self.old_label)
                    
                    # Update background color based on label
                    try:
                        from libs.utils import generate_color_by_text
                        item.setBackground(generate_color_by_text(self.old_label))
                        shape.line_color = generate_color_by_text(self.old_label)
                        shape.fill_color = generate_color_by_text(self.old_label)
                    except ImportError:
                        pass
            
            # Update combo box
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Update canvas
            if hasattr(app.canvas, 'update'):
                app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing ChangeLabelCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Change label '{self.old_label}' to '{self.new_label}'"
    
    def can_merge_with(self, other: Command) -> bool:
        """ChangeLabelCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("ChangeLabelCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Changing a label affects save state"""
        return True


class ApplyQuickIDCommand(Command):
    """Command to apply a Quick ID to a shape"""
    
    def __init__(self, frame_path: str, shape: Any, quick_id: str):
        """
        Initialize ApplyQuickIDCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape: The shape to apply Quick ID to
            quick_id: The Quick ID to apply
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape = shape
        self.quick_id = quick_id
        self.old_label = shape.label if hasattr(shape, 'label') else ''
    
    def execute(self, app: Any) -> bool:
        """
        Apply Quick ID to the shape
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Get the actual label for this Quick ID
            new_label = self.quick_id
            if hasattr(app, 'get_class_name_for_quick_id'):
                new_label = app.get_class_name_for_quick_id(self.quick_id)
            
            # Apply new label
            self.shape.label = new_label
            
            # Update list item if exists
            if hasattr(app, 'shapes_to_items') and self.shape in app.shapes_to_items:
                item = app.shapes_to_items[self.shape]
                item.setText(new_label)
                
                # Update background color
                if hasattr(app, 'generate_color_by_text'):
                    from libs.utils import generate_color_by_text
                    item.setBackground(generate_color_by_text(new_label))
                    self.shape.line_color = generate_color_by_text(new_label)
            
            # Update combo box
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Update canvas
            if hasattr(app.canvas, 'update'):
                app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing ApplyQuickIDCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore the original label
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original label
            self.shape.label = self.old_label
            
            # Update list item if exists
            if hasattr(app, 'shapes_to_items') and self.shape in app.shapes_to_items:
                item = app.shapes_to_items[self.shape]
                item.setText(self.old_label)
                
                # Update background color
                if hasattr(app, 'generate_color_by_text'):
                    from libs.utils import generate_color_by_text
                    item.setBackground(generate_color_by_text(self.old_label))
                    self.shape.line_color = generate_color_by_text(self.old_label)
            
            # Update combo box
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Update canvas
            if hasattr(app.canvas, 'update'):
                app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing ApplyQuickIDCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Apply Quick ID '{self.quick_id}'"
    
    def can_merge_with(self, other: Command) -> bool:
        """ApplyQuickIDCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("ApplyQuickIDCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Applying Quick ID affects save state"""
        return True


class PropagateLabelCommand(Command):
    """Command to propagate a label change to subsequent frames"""
    
    def __init__(self, source_shape: Any, new_label: str, affected_frames: List[str]):
        """
        Initialize PropagateLabelCommand
        
        Args:
            source_shape: The source shape with the label to propagate
            new_label: The new label to propagate
            affected_frames: List of frame paths that will be affected
        """
        super().__init__()
        self.source_shape = source_shape
        self.new_label = new_label
        self.affected_frames = affected_frames
        self.original_states = {}  # Will store original states of affected frames
    
    def execute(self, app: Any) -> bool:
        """
        Propagate label to subsequent frames
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store current frame
            original_frame = app.file_path
            
            # Process each affected frame
            for frame_path in self.affected_frames:
                # Load frame
                app.load_file(frame_path, preserve_zoom=True)
                
                # Store original state
                self.original_states[frame_path] = []
                
                # Find matching shapes and update labels
                for shape in app.canvas.shapes:
                    # Check if shape matches (simplified - you might want to use IOU)
                    if self._shapes_match(self.source_shape, shape):
                        # Store original label
                        self.original_states[frame_path].append({
                            'shape': shape,
                            'old_label': shape.label
                        })
                        
                        # Apply new label
                        shape.label = self.new_label
                        
                        # Update list item if exists
                        if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                            item = app.shapes_to_items[shape]
                            item.setText(self.new_label)
                
                # Save if auto-saving enabled
                if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                    app.save_file()
            
            # Return to original frame
            if app.file_path != original_frame:
                app.load_file(original_frame, preserve_zoom=True)
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing PropagateLabelCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore original labels in all affected frames
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store current frame
            original_frame = app.file_path
            
            # Restore each affected frame
            for frame_path, shape_states in self.original_states.items():
                # Load frame
                app.load_file(frame_path, preserve_zoom=True)
                
                # Restore original labels
                for state in shape_states:
                    shape = state['shape']
                    shape.label = state['old_label']
                    
                    # Update list item if exists
                    if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                        item = app.shapes_to_items[shape]
                        item.setText(state['old_label'])
                
                # Save if auto-saving enabled
                if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                    app.save_file()
            
            # Return to original frame
            if app.file_path != original_frame:
                app.load_file(original_frame, preserve_zoom=True)
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing PropagateLabelCommand: {e}")
            return False
    
    def _shapes_match(self, shape1: Any, shape2: Any) -> bool:
        """
        Check if two shapes match (simplified version)
        
        Args:
            shape1: First shape
            shape2: Second shape
            
        Returns:
            bool: True if shapes match, False otherwise
        """
        # Simplified matching - you might want to use IOU or other criteria
        if not hasattr(shape1, 'points') or not hasattr(shape2, 'points'):
            return False
        
        if len(shape1.points) != len(shape2.points):
            return False
        
        # Check if points are similar (within threshold)
        threshold = 50  # pixels
        for p1, p2 in zip(shape1.points, shape2.points):
            if abs(p1.x() - p2.x()) > threshold or abs(p1.y() - p2.y()) > threshold:
                return False
        
        return True
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Propagate label '{self.new_label}' to {len(self.affected_frames)} frames"
    
    def can_merge_with(self, other: Command) -> bool:
        """PropagateLabelCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("PropagateLabelCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Propagating labels affects save state"""
        return True


class PropagateQuickIDCommand(PropagateLabelCommand):
    """Command to propagate a Quick ID to subsequent frames"""
    
    def __init__(self, source_shape: Any, quick_id: str, affected_frames: List[str]):
        """
        Initialize PropagateQuickIDCommand
        
        Args:
            source_shape: The source shape with the Quick ID to propagate
            quick_id: The Quick ID to propagate
            affected_frames: List of frame paths that will be affected
        """
        self.quick_id = quick_id
        super().__init__(source_shape, quick_id, affected_frames)
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Propagate Quick ID '{self.quick_id}' to {len(self.affected_frames)} frames"


class BatchChangeLabelCommand(Command):
    """Command to change labels of multiple shapes at once"""
    
    def __init__(self, frame_path: str, shape_indices: List[int], 
                 old_labels: Any, new_label: str):
        """
        Initialize BatchChangeLabelCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_indices: Indices of shapes to change
            old_labels: Original labels (can be list or single value)
            new_label: New label to apply to all shapes
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape_indices = shape_indices
        
        # Handle old_labels as either list or single value
        if isinstance(old_labels, list):
            self.old_labels = old_labels
        else:
            self.old_labels = [old_labels] * len(shape_indices)
        
        self.new_label = new_label
    
    def execute(self, app: Any) -> bool:
        """
        Change labels of multiple shapes
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Change labels
            for idx in self.shape_indices:
                if idx < len(app.canvas.shapes):
                    shape = app.canvas.shapes[idx]
                    shape.label = self.new_label
                    
                    # Update list item if exists
                    if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                        item = app.shapes_to_items[shape]
                        item.setText(self.new_label)
                        
                        # Update color
                        if hasattr(app, 'generate_color_by_text'):
                            from libs.utils import generate_color_by_text
                            item.setBackground(generate_color_by_text(self.new_label))
                            shape.line_color = generate_color_by_text(self.new_label)
            
            # Update combo box
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Update canvas
            if hasattr(app.canvas, 'update'):
                app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing BatchChangeLabelCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore original labels
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original labels
            for idx, old_label in zip(self.shape_indices, self.old_labels):
                if idx < len(app.canvas.shapes):
                    shape = app.canvas.shapes[idx]
                    shape.label = old_label
                    
                    # Update list item if exists
                    if hasattr(app, 'shapes_to_items') and shape in app.shapes_to_items:
                        item = app.shapes_to_items[shape]
                        item.setText(old_label)
                        
                        # Update color
                        if hasattr(app, 'generate_color_by_text'):
                            from libs.utils import generate_color_by_text
                            item.setBackground(generate_color_by_text(old_label))
                            shape.line_color = generate_color_by_text(old_label)
            
            # Update combo box
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Update canvas
            if hasattr(app.canvas, 'update'):
                app.canvas.update()
            
            # Mark as dirty
            app.set_dirty()
            
            # Auto-save if enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing BatchChangeLabelCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        return f"Change {len(self.shape_indices)} labels to '{self.new_label}'"
    
    def can_merge_with(self, other: Command) -> bool:
        """BatchChangeLabelCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("BatchChangeLabelCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Changing labels affects save state"""
        return True


class ClickChangeLabelCommand(Command):
    """Command for click-to-change label functionality"""
    
    def __init__(self, frame_path: str, shape: Any, item: Any, 
                 old_label: str, new_label: str, 
                 propagate: bool = False, affected_frames: List[str] = None):
        """
        Initialize ClickChangeLabelCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape: The shape to change
            item: The list item associated with the shape
            old_label: Original label
            new_label: New label to apply
            propagate: Whether to propagate to subsequent frames
            affected_frames: List of affected frames if propagating
        """
        super().__init__()
        self.frame_path = frame_path
        self.shape = shape
        self.item = item
        self.old_label = old_label
        self.new_label = new_label
        self.propagate = propagate
        self.affected_frames = affected_frames or []
        self.propagate_command = None
    
    def execute(self, app: Any) -> bool:
        """
        Change label via click
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Change label
            self.shape.label = self.new_label
            self.item.setText(self.new_label)
            
            # Update color
            if hasattr(app, 'generate_color_by_text'):
                from libs.utils import generate_color_by_text
                self.item.setBackground(generate_color_by_text(self.new_label))
                self.shape.line_color = generate_color_by_text(self.new_label)
            
            # Update UI
            app.set_dirty()
            if hasattr(app, 'canvas'):
                app.canvas.load_shapes(app.canvas.shapes)
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Save if auto-saving enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            # Propagate if requested
            if self.propagate and self.affected_frames:
                self.propagate_command = PropagateLabelCommand(
                    self.shape, self.new_label, self.affected_frames
                )
                self.propagate_command.execute(app)
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing ClickChangeLabelCommand: {e}")
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore original label
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Undo propagation first if it was done
            if self.propagate_command:
                self.propagate_command.undo(app)
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore original label
            self.shape.label = self.old_label
            self.item.setText(self.old_label)
            
            # Update color
            if hasattr(app, 'generate_color_by_text'):
                from libs.utils import generate_color_by_text
                self.item.setBackground(generate_color_by_text(self.old_label))
                self.shape.line_color = generate_color_by_text(self.old_label)
            
            # Update UI
            app.set_dirty()
            if hasattr(app, 'canvas'):
                app.canvas.load_shapes(app.canvas.shapes)
            if hasattr(app, 'update_combo_box'):
                app.update_combo_box()
            
            # Save if auto-saving enabled
            if hasattr(app, 'auto_saving') and app.auto_saving.isChecked():
                app.save_file()
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing ClickChangeLabelCommand: {e}")
            return False
    
    @property
    def description(self) -> str:
        """Get command description"""
        desc = f"Click-change label '{self.old_label}' to '{self.new_label}'"
        if self.propagate:
            desc += f" (propagated to {len(self.affected_frames)} frames)"
        return desc
    
    def can_merge_with(self, other: Command) -> bool:
        """ClickChangeLabelCommand doesn't merge"""
        return False
    
    def merge(self, other: Command) -> Command:
        """Merge is not supported"""
        raise NotImplementedError("ClickChangeLabelCommand does not support merging")
    
    @property
    def affects_save_state(self) -> bool:
        """Changing label affects save state"""
        return True