#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BB duplication commands with IOU checking for Undo/Redo system
"""

from typing import Any, List, Optional, Dict
import logging
import copy
from ..command import Command
from .shape_commands import AddShapeCommand

logger = logging.getLogger(__name__)


class AddShapeWithIOUCheckCommand(AddShapeCommand):
    """Command to add shape with IOU overlap checking"""
    
    def __init__(self, frame_path: str, shape_data: dict, 
                 iou_threshold: float = 0.5, overwrite_mode: bool = False):
        """
        Initialize AddShapeWithIOUCheckCommand
        
        Args:
            frame_path: Path to the frame/image file
            shape_data: Dictionary containing shape properties
            iou_threshold: IOU threshold for overlap detection
            overwrite_mode: If True, overwrite overlapping shapes; if False, skip
        """
        super().__init__(frame_path, shape_data)
        self.iou_threshold = iou_threshold
        self.overwrite_mode = overwrite_mode
        self.removed_shapes = []  # Store shapes that were removed due to overlap
        self.skipped = False  # Flag to indicate if shape was skipped
    
    def calculate_iou(self, points1: list, points2: list) -> float:
        """Calculate Intersection over Union between two bounding boxes."""
        # Get coordinates from all points to find bounding box
        x1_coords = [p[0] if isinstance(p, (list, tuple)) else p.x() for p in points1]
        y1_coords = [p[1] if isinstance(p, (list, tuple)) else p.y() for p in points1]
        x2_coords = [p[0] if isinstance(p, (list, tuple)) else p.x() for p in points2]
        y2_coords = [p[1] if isinstance(p, (list, tuple)) else p.y() for p in points2]
        
        x1_min, x1_max = min(x1_coords), max(x1_coords)
        y1_min, y1_max = min(y1_coords), max(y1_coords)
        x2_min, x2_max = min(x2_coords), max(x2_coords)
        y2_min, y2_max = min(y2_coords), max(y2_coords)
        
        # Calculate intersection area
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Calculate union area
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = area1 + area2 - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def execute(self, app: Any) -> bool:
        """
        Add shape with IOU checking
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Get shape points
            new_points = self.shape_data.get('points', [])
            if len(new_points) != 4:
                # Not a rectangle, just add normally
                return super().execute(app)
            
            # Check for overlapping shapes
            shapes_to_remove = []
            should_add_shape = True
            
            for existing_shape in app.canvas.shapes:
                # Only check IoU if both shapes have 4 points (rectangles)
                if len(existing_shape.points) == 4:
                    existing_points = [(p.x(), p.y()) for p in existing_shape.points]
                    iou = self.calculate_iou(new_points, existing_points)
                    
                    logger.debug(f"[BB Duplication] Checking IOU with existing shape: {iou:.3f}")
                    
                    if iou >= self.iou_threshold:
                        if self.overwrite_mode:
                            # Mark shape for removal
                            shapes_to_remove.append(existing_shape)
                            logger.debug(f"[BB Duplication] Overwriting existing BB (IOU={iou:.2f})")
                            print(f"[DEBUG BB Duplication] Overwriting existing BB with label '{existing_shape.label}' (IOU={iou:.2f})")
                        else:
                            # Skip this frame if any overlap found
                            should_add_shape = False
                            self.skipped = True
                            logger.debug(f"[BB Duplication] Skipping due to overlap (IOU={iou:.2f})")
                            break  # In skip mode, one overlap is enough to skip
            
            # Remove overlapping shapes if in overwrite mode
            if shapes_to_remove:
                for shape_to_remove in shapes_to_remove:
                    # Store shape data for undo
                    shape_data = {
                        'label': shape_to_remove.label,
                        'label2': shape_to_remove.label2 if hasattr(shape_to_remove, 'label2') else None,
                        'points': [(p.x(), p.y()) for p in shape_to_remove.points],
                        'difficult': shape_to_remove.difficult if hasattr(shape_to_remove, 'difficult') else False
                    }
                    if hasattr(shape_to_remove, 'line_color'):
                        shape_data['line_color'] = shape_to_remove.line_color
                    if hasattr(shape_to_remove, 'fill_color'):
                        shape_data['fill_color'] = shape_to_remove.fill_color
                    
                    self.removed_shapes.append(shape_data)
                    
                    # Remove from canvas
                    app.canvas.shapes.remove(shape_to_remove)
                    
                    # Remove from label list
                    if hasattr(app, 'remove_label'):
                        app.remove_label(shape_to_remove)
            
            # Add new shape if not skipped
            if should_add_shape:
                result = super().execute(app)
                if not result:
                    # If adding failed, restore removed shapes
                    self.restore_removed_shapes(app)
                return result
            else:
                # Shape was skipped due to overlap
                self.executed = False
                return True  # Return True to indicate command completed (even if skipped)
            
        except Exception as e:
            logger.error(f"Error adding shape with IOU check: {e}")
            # Restore removed shapes on error
            self.restore_removed_shapes(app)
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Undo the shape addition and restore removed shapes
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If shape was skipped, nothing to undo
            if self.skipped:
                self.executed = False
                return True
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # First undo the shape addition
            if not self.skipped:
                super().undo(app)
            
            # Then restore any shapes that were removed
            if self.removed_shapes:
                print(f"[DEBUG BB Duplication] Restoring {len(self.removed_shapes)} removed shapes during undo")
            self.restore_removed_shapes(app)
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing shape addition with IOU check: {e}")
            return False
    
    def redo(self, app: Any) -> bool:
        """
        Redo the shape addition with IOU checking
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If shape was skipped, nothing to redo
            if self.skipped:
                self.executed = False
                return True
            
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # First remove the shapes that were originally removed
            if self.removed_shapes:
                for shape_data in self.removed_shapes:
                    # Find and remove matching shape
                    for existing_shape in app.canvas.shapes[:]:  # Use slice to avoid modification during iteration
                        if (hasattr(existing_shape, 'label') and existing_shape.label == shape_data.get('label', '') and
                            len(existing_shape.points) == len(shape_data.get('points', []))):
                            # Check if points match (approximately)
                            existing_points = [(p.x(), p.y()) for p in existing_shape.points]
                            shape_points = shape_data.get('points', [])
                            if len(existing_points) == len(shape_points):
                                match = True
                                for i, (ep, sp) in enumerate(zip(existing_points, shape_points)):
                                    if abs(ep[0] - sp[0]) > 1 or abs(ep[1] - sp[1]) > 1:
                                        match = False
                                        break
                                
                                if match:
                                    # Remove from canvas
                                    app.canvas.shapes.remove(existing_shape)
                                    # Remove from label list
                                    if hasattr(app, 'remove_label'):
                                        app.remove_label(existing_shape)
                                    break
            
            # Then add the new shape
            result = super().execute(app)
            return result
            
        except Exception as e:
            logger.error(f"Error redoing shape addition with IOU check: {e}")
            return False
    
    def restore_removed_shapes(self, app: Any):
        """Restore shapes that were removed due to overlap"""
        from PyQt5.QtCore import QPointF
        from libs.shape import Shape
        
        for shape_data in self.removed_shapes:
            shape = Shape()
            shape.label = shape_data.get('label', '')
            shape.label1 = shape.label  # Set label1 same as label
            shape.label2 = shape_data.get('label2', None)
            shape.points = [QPointF(x, y) for x, y in shape_data.get('points', [])]
            shape.close()
            
            if 'line_color' in shape_data:
                shape.line_color = shape_data['line_color']
            if 'fill_color' in shape_data:
                shape.fill_color = shape_data['fill_color']
            if 'difficult' in shape_data:
                shape.difficult = shape_data['difficult']
            
            # Add back to canvas
            app.canvas.shapes.append(shape)
            if hasattr(app, 'add_label'):
                app.add_label(shape)
        
        # Update canvas
        if hasattr(app.canvas, 'load_shapes'):
            app.canvas.load_shapes(app.canvas.shapes)
        elif hasattr(app.canvas, 'update'):
            app.canvas.update()
    
    @property
    def description(self) -> str:
        """Get command description"""
        label = self.shape_data.get('label', 'unknown')
        if self.skipped:
            return f"Skip adding shape '{label}' (overlap detected)"
        else:
            return f"Add shape '{label}' with IOU check"