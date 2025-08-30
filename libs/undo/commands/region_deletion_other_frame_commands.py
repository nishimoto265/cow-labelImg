"""
Region deletion commands for other frames
"""

import logging
import os
from typing import Any, List, Tuple, Dict
from ..command import Command

logger = logging.getLogger(__name__)


class RegionDeletionOtherFrameCommand(Command):
    """
    Command to delete shapes within a region in another frame (not current)
    This command loads the frame, performs deletion, and saves it
    """
    
    def __init__(self, frame_path: str, region_x1: float, region_y1: float, 
                 region_x2: float, region_y2: float):
        """
        Initialize RegionDeletionOtherFrameCommand
        
        Args:
            frame_path: Path to the frame/image file
            region_x1, region_y1, region_x2, region_y2: Region bounds
        """
        super().__init__()
        self.frame_path = frame_path
        self.region_x1 = region_x1
        self.region_y1 = region_y1
        self.region_x2 = region_x2
        self.region_y2 = region_y2
        self.deleted_shapes_data = []  # Will store deleted shapes for undo
        self._description = f"Delete shapes in region for {os.path.basename(frame_path)}"
    
    def execute(self, app: Any) -> bool:
        """
        Delete shapes in the region for the specified frame
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"[RegionDeletionOtherFrame] Executing deletion for frame: {self.frame_path}")
            
            # Save current frame path
            original_frame = app.file_path
            
            # Load the target frame
            app.load_file(self.frame_path, preserve_zoom=True)
            
            print(f"[RegionDeletionOtherFrame] Loaded frame with {len(app.canvas.shapes)} shapes")
            
            # Find and delete shapes in region
            self.deleted_shapes_data = []
            shapes_to_delete = []
            
            for i, shape in enumerate(app.canvas.shapes):
                if self.is_shape_contained_in_region(shape, 
                                                     self.region_x1, self.region_y1, 
                                                     self.region_x2, self.region_y2):
                    # Store shape data for undo
                    shape_data = {
                        'index': i,
                        'label': shape.label if hasattr(shape, 'label') else '',
                        'points': [(p.x(), p.y()) for p in shape.points] if hasattr(shape, 'points') else [],
                        'difficult': shape.difficult if hasattr(shape, 'difficult') else False
                    }
                    
                    # Store dual label data
                    if hasattr(shape, 'label2') and shape.label2 is not None:
                        shape_data['label2'] = shape.label2
                    
                    # Store additional properties if they exist
                    if hasattr(shape, 'line_color'):
                        shape_data['line_color'] = shape.line_color
                    if hasattr(shape, 'fill_color'):
                        shape_data['fill_color'] = shape.fill_color
                    
                    self.deleted_shapes_data.append(shape_data)
                    shapes_to_delete.append(shape)
                    print(f"[RegionDeletionOtherFrame] Will delete shape: {shape.label}")
            
            # Delete shapes in reverse order
            for shape in reversed(shapes_to_delete):
                if hasattr(app, 'remove_label'):
                    app.remove_label(shape)
                app.canvas.shapes.remove(shape)
            
            print(f"[RegionDeletionOtherFrame] Deleted {len(shapes_to_delete)} shapes")
            
            # Save the modified frame
            if len(shapes_to_delete) > 0:
                app.save_file()
                print(f"[RegionDeletionOtherFrame] Saved frame")
            
            # Return to original frame
            if original_frame != self.frame_path:
                app.load_file(original_frame, preserve_zoom=True)
            
            self.executed = True
            return True
            
        except Exception as e:
            logger.error(f"Error executing RegionDeletionOtherFrameCommand: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def is_shape_contained_in_region(self, shape, region_x1, region_y1, region_x2, region_y2):
        """Check if a shape is completely contained within the specified region."""
        # Get shape bounds
        points = shape.points
        if len(points) < 2:
            return False
        
        x_coords = [p.x() for p in points]
        y_coords = [p.y() for p in points]
        shape_x1, shape_x2 = min(x_coords), max(x_coords)
        shape_y1, shape_y2 = min(y_coords), max(y_coords)
        
        # Check if shape is completely inside region
        return (region_x1 <= shape_x1 and 
                region_y1 <= shape_y1 and
                region_x2 >= shape_x2 and
                region_y2 >= shape_y2)
    
    def undo(self, app: Any) -> bool:
        """
        Restore deleted shapes
        
        Args:
            app: MainWindow instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Save current frame path
            original_frame = app.file_path
            
            # Load the target frame
            app.load_file(self.frame_path, preserve_zoom=True)
            
            # Restore shapes
            from libs.shape import Shape
            from PyQt5.QtCore import QPointF
            
            for shape_data in self.deleted_shapes_data:
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
            
            # Save the restored frame
            if len(self.deleted_shapes_data) > 0:
                app.save_file()
            
            # Return to original frame
            if original_frame != self.frame_path:
                app.load_file(original_frame, preserve_zoom=True)
            
            self.executed = False
            return True
            
        except Exception as e:
            logger.error(f"Error undoing RegionDeletionOtherFrameCommand: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def redo(self, app: Any) -> bool:
        """
        Re-execute the deletion
        """
        return self.execute(app)
    
    @property
    def description(self) -> str:
        """Get command description"""
        return self._description
    
    def can_merge_with(self, other: 'Command') -> bool:
        """Region deletions cannot be merged"""
        return False
    
    def merge(self, other: 'Command') -> bool:
        """Region deletions cannot be merged"""
        return False
    
    @property
    def affects_save_state(self) -> bool:
        """Region deletions affect save state"""
        return True