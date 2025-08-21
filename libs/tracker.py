#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Continuous tracking module for labelImg.
Provides IOU calculation utilities for shape matching.
"""


class Tracker:
    """
    Tracker class for continuous object tracking between frames.
    Provides IOU (Intersection over Union) calculation for shape matching.
    """
    
    def __init__(self, iou_threshold=0.4):
        """
        Initialize the tracker.
        
        Args:
            iou_threshold (float): Minimum IOU value to consider a match (default: 0.4)
        """
        self.iou_threshold = iou_threshold
        self.prev_frame_shapes = []
    
    def calculate_iou(self, shape1, shape2):
        """
        Calculate Intersection over Union between two shapes.
        
        Args:
            shape1: First shape object with points attribute
            shape2: Second shape object with points attribute
            
        Returns:
            float: IOU value between 0 and 1
        """
        # Get bounding boxes from shape points
        box1 = self._get_bbox_from_shape(shape1)
        box2 = self._get_bbox_from_shape(shape2)
        
        if box1 is None or box2 is None:
            return 0.0
        
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection area
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union area
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _get_bbox_from_shape(self, shape):
        """
        Extract bounding box coordinates from shape points.
        
        Args:
            shape: Shape object with points attribute
            
        Returns:
            tuple: (x1, y1, x2, y2) or None if shape has no points
        """
        if not hasattr(shape, 'points') or len(shape.points) < 2:
            return None
        
        # Extract x and y coordinates
        x_coords = [p.x() for p in shape.points]
        y_coords = [p.y() for p in shape.points]
        
        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
    
    def reset(self):
        """
        Reset the tracker state.
        """
        self.prev_frame_shapes = []
    
    def track_shapes(self, prev_shapes, curr_shapes):
        """
        Store shapes for tracking reference.
        
        Args:
            prev_shapes: List of shapes from previous frame
            curr_shapes: List of shapes from current frame
        """
        self.prev_frame_shapes = curr_shapes