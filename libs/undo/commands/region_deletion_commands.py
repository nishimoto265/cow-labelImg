"""
Region deletion commands for undo/redo functionality
"""

import logging
from typing import Any, List, Tuple, Dict
from ..command import Command

logger = logging.getLogger(__name__)


class RegionDeletionCommand(Command):
    """
    Command to delete multiple shapes within a region in the current frame
    """
    
    def __init__(self, frame_path: str, shapes_to_delete: List[Tuple[int, Any]]):
        """
        Initialize RegionDeletionCommand
        
        Args:
            frame_path: Path to the frame/image file
            shapes_to_delete: List of (index, shape) tuples to delete
        """
        super().__init__()
        self.frame_path = frame_path
        self.deleted_shapes = []
        
        # Store shape data for restoration (in original order)
        for shape_index, shape in shapes_to_delete:
            shape_data = {
                'index': shape_index,
                'label': shape.label if hasattr(shape, 'label') else '',
                'points': [(p.x(), p.y()) for p in shape.points] if hasattr(shape, 'points') else [],
                'difficult': shape.difficult if hasattr(shape, 'difficult') else False,
                'shape_ref': shape  # Keep reference to original shape object
            }
            
            # Store dual label data
            if hasattr(shape, 'label2') and shape.label2 is not None:
                shape_data['label2'] = shape.label2
            
            # Store additional properties if they exist
            if hasattr(shape, 'line_color'):
                shape_data['line_color'] = shape.line_color
            if hasattr(shape, 'fill_color'):
                shape_data['fill_color'] = shape.fill_color
                
            self.deleted_shapes.append(shape_data)
    
    def execute(self, app: Any) -> bool:
        """
        Delete all shapes in the region
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Delete shapes in reverse order (highest index first) to maintain indices
            for shape_data in reversed(self.deleted_shapes):
                shape_ref = shape_data.get('shape_ref')
                if shape_ref and shape_ref in app.canvas.shapes:
                    # Remove from label list
                    if hasattr(app, 'remove_label'):
                        app.remove_label(shape_ref)
                    # Remove from canvas
                    app.canvas.shapes.remove(shape_ref)
            
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
            
        except Exception as e:
            logger.error(f"Error executing RegionDeletionCommand: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def undo(self, app: Any) -> bool:
        """
        Restore all deleted shapes
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load target frame if different
            if app.file_path != self.frame_path:
                app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore shapes in original order
            from libs.shape import Shape
            from PyQt5.QtCore import QPointF
            
            for shape_data in self.deleted_shapes:
                # Create new shape
                shape = Shape()
                shape.label = shape_data.get('label', '')
                shape.points = [QPointF(x, y) for x, y in shape_data.get('points', [])]
                shape.difficult = shape_data.get('difficult', False)
                
                # Restore dual label if present
                if 'label2' in shape_data:
                    shape.label2 = shape_data['label2']
                
                # Restore colors if present
                if 'line_color' in shape_data:
                    shape.line_color = shape_data['line_color']
                if 'fill_color' in shape_data:
                    shape.fill_color = shape_data['fill_color']
                
                # Insert at original position if possible
                original_index = shape_data['index']
                if original_index <= len(app.canvas.shapes):
                    app.canvas.shapes.insert(original_index, shape)
                else:
                    app.canvas.shapes.append(shape)
                
                # Add to label list
                if hasattr(app, 'add_label'):
                    app.add_label(shape)
            
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
            
        except Exception as e:
            logger.error(f"Error undoing RegionDeletionCommand: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def redo(self, app: Any) -> bool:
        """
        Re-execute the deletion
        """
        return self.execute(app)