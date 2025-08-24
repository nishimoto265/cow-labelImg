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
                 change_label2: bool = True,
                 direct_file_edit: bool = False):
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
            direct_file_edit: If True, edit annotation file directly without loading frame
        """
        self.frame_path = frame_path
        self.shape_index = shape_index
        self.old_label1 = old_label1
        self.new_label1 = new_label1
        self.old_label2 = old_label2
        self.new_label2 = new_label2
        self.change_label1 = change_label1
        self.change_label2 = change_label2
        self.direct_file_edit = direct_file_edit
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
            if self.direct_file_edit:
                # Edit annotation file directly without loading frame
                return self._edit_annotation_file(app, self.new_label1, self.new_label2)
            else:
                # Original behavior - load frame and change in UI
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
                else:
                    # Keep existing label1
                    if hasattr(shape, 'label1'):
                        shape.label1 = shape.label1
                    else:
                        shape.label1 = shape.label
                
                if self.change_label2:
                    shape.label2 = self.new_label2
                else:
                    # Keep existing label2
                    if not hasattr(shape, 'label2'):
                        shape.label2 = ''
                
                # Update shape colors based on current color mode
                if hasattr(app, 'update_shape_color'):
                    app.update_shape_color(shape)
                else:
                    # Fallback: update colors based on label
                    from libs.utils import generate_color_by_text
                    color_label = app.get_color_label_for_shape(shape) if hasattr(app, 'get_color_label_for_shape') else shape.label1
                    shape.line_color = generate_color_by_text(color_label)
                    shape.fill_color = generate_color_by_text(color_label)
                
                # Update the item in the label list
                item = app.shapes_to_items.get(shape)
                if item:
                    # Update item text to show both labels correctly
                    text_parts = []
                    # Use the current label1 value
                    label1_text = shape.label1 if hasattr(shape, 'label1') else shape.label
                    if label1_text:
                        text_parts.append(label1_text)
                    # Use the current label2 value
                    if hasattr(shape, 'label2') and shape.label2:
                        text_parts.append(shape.label2)
                    
                    # Format correctly: "label1 | label2" or just "label1"
                    text = " | ".join(text_parts) if len(text_parts) > 1 else (text_parts[0] if text_parts else "")
                    item.setText(text)
                    
                    # Update item background color
                    from libs.utils import generate_color_by_text
                    color_label = app.get_color_label_for_shape(shape) if hasattr(app, 'get_color_label_for_shape') else shape.label1
                    item.setBackground(generate_color_by_text(color_label))
                
                # Update canvas to reflect color changes
                app.canvas.load_shapes(app.canvas.shapes)
                app.canvas.repaint()
                
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
    
    def _edit_annotation_file(self, app: Any, label1: str, label2: str) -> bool:
        """Edit annotation file directly for dual labels"""
        try:
            import os
            
            # Get annotation path
            annotation_path = app.get_annotation_path(self.frame_path)
            if not annotation_path or not os.path.exists(annotation_path):
                logger.debug(f"Annotation file not found: {annotation_path}")
                return False
            
            # Check format
            if annotation_path.endswith('.txt'):
                # YOLO format
                from libs.yolo_io import YoloReader, YOLOWriter
                from PyQt5.QtGui import QImage
                
                # Get image
                img = QImage()
                if not img.load(self.frame_path):
                    logger.error(f"Could not load image: {self.frame_path}")
                    return False
                
                # Read existing annotations
                reader = YoloReader(annotation_path, img)
                shapes = reader.get_shapes()
                
                # Check if shape index is valid
                if self.shape_index >= len(shapes):
                    logger.debug(f"Shape index {self.shape_index} out of range")
                    return False
                
                # Update the labels
                old_shape = shapes[self.shape_index]
                
                # Handle both dict and tuple formats for shape update
                if isinstance(old_shape, dict):
                    new_shape = old_shape.copy()
                    if self.change_label1:
                        new_shape['label'] = label1
                    if self.change_label2:
                        new_shape['label2'] = label2
                else:
                    # Tuple format - need to rebuild
                    shape_label = label1 if self.change_label1 else old_shape[0]
                    new_shape = (shape_label, old_shape[1], old_shape[2], old_shape[3], old_shape[4])
                    if self.change_label2:
                        # Convert to dict to add label2
                        new_shape = {
                            'label': shape_label,
                            'label2': label2,
                            'points': old_shape[1],
                            'difficult': old_shape[4]
                        }
                shapes[self.shape_index] = new_shape
                
                # Write back to file using YOLOWriter
                img_folder = os.path.dirname(self.frame_path)
                img_name = os.path.basename(self.frame_path)
                img_size = [img.height(), img.width(), 3 if img.hasAlphaChannel() else 1]
                
                writer = YOLOWriter(img_folder, img_name, img_size)
                writer.verified = True
                
                # Add shapes to writer
                for shape_data in shapes:
                    # Handle both dict and tuple formats
                    if isinstance(shape_data, dict):
                        shape_label = shape_data.get('label', '')
                        label2 = shape_data.get('label2', None)
                        points = shape_data.get('points', [])
                        difficult = shape_data.get('difficult', False)
                    else:
                        # Tuple format (backward compatibility)
                        shape_label, points, _, _, difficult = shape_data
                        label2 = None
                    
                    # Convert points to bounding box for YOLO format
                    if len(points) >= 4:
                        x_min = min(p[0] for p in points)
                        y_min = min(p[1] for p in points)
                        x_max = max(p[0] for p in points)
                        y_max = max(p[1] for p in points)
                        writer.add_bnd_box(x_min, y_min, x_max, y_max, shape_label, difficult, label2)
                
                # Save with the class lists
                class_list1 = app.label_hist if hasattr(app, 'label_hist') else []
                class_list2 = app.label2_hist if hasattr(app, 'label2_hist') else []
                writer.save(class_list=class_list1, class_list2=class_list2, target_file=annotation_path)
                
                logger.debug(f"Changed labels in {annotation_path}")
            else:
                # Pascal VOC XML format - not fully supporting dual labels yet
                logger.warning("Direct file edit for dual labels in Pascal VOC format not fully implemented")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error editing annotation file: {e}")
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
            if self.direct_file_edit:
                # Edit annotation file directly without loading frame
                return self._edit_annotation_file(app, self.old_label1, self.old_label2)
            else:
                # Original behavior - load frame and change in UI
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
                
                # Update shape colors based on current color mode
                if hasattr(app, 'update_shape_color'):
                    app.update_shape_color(shape)
                else:
                    # Fallback: update colors based on label
                    from libs.utils import generate_color_by_text
                    color_label = app.get_color_label_for_shape(shape) if hasattr(app, 'get_color_label_for_shape') else shape.label1
                    shape.line_color = generate_color_by_text(color_label)
                    shape.fill_color = generate_color_by_text(color_label)
                
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
                    
                    # Update item background color
                    from libs.utils import generate_color_by_text
                    color_label = app.get_color_label_for_shape(shape) if hasattr(app, 'get_color_label_for_shape') else shape.label1
                    item.setBackground(generate_color_by_text(color_label))
                
                # Update canvas
                app.canvas.load_shapes(app.canvas.shapes)
                app.canvas.repaint()
                
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