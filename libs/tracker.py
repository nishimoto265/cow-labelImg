#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Continuous tracking module for labelImg.
Implements IOU-based tracking with Hungarian algorithm for optimal matching.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment


class Tracker:
    """
    Tracker class for continuous object tracking between frames.
    Uses IOU (Intersection over Union) and Hungarian algorithm for matching.
    """
    
    def __init__(self, iou_threshold=0.4):
        """
        Initialize the tracker.
        
        Args:
            iou_threshold (float): Minimum IOU value to consider a match (default: 0.4)
        """
        self.iou_threshold = iou_threshold
        self.next_track_id = 1
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
    
    def create_cost_matrix(self, prev_shapes, curr_shapes):
        """
        Create cost matrix for Hungarian algorithm based on IOU.
        
        Args:
            prev_shapes: List of shapes from previous frame
            curr_shapes: List of shapes from current frame
            
        Returns:
            numpy.ndarray: Cost matrix where cost = 1 - IOU
        """
        n_prev = len(prev_shapes)
        n_curr = len(curr_shapes)
        cost_matrix = np.ones((n_prev, n_curr))
        
        for i, prev_shape in enumerate(prev_shapes):
            for j, curr_shape in enumerate(curr_shapes):
                iou = self.calculate_iou(prev_shape, curr_shape)
                cost_matrix[i, j] = 1 - iou  # Higher IOU = lower cost
        
        return cost_matrix
    
    def track_shapes(self, prev_shapes, curr_shapes):
        """
        Track shapes from previous frame to current frame.
        
        Args:
            prev_shapes: List of shapes from previous frame
            curr_shapes: List of shapes from current frame
            
        Returns:
            None (modifies curr_shapes in place)
        """
        if not prev_shapes:
            # First frame: assign new IDs to all shapes
            for shape in curr_shapes:
                shape.track_id = self.next_track_id
                self.next_track_id += 1
                shape.is_tracked = False
            return
        
        if not curr_shapes:
            # No shapes in current frame
            return
        
        # Create cost matrix and find optimal matching
        cost_matrix = self.create_cost_matrix(prev_shapes, curr_shapes)
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # Track matched shapes
        matched_curr_indices = set()
        
        for i, j in zip(row_ind, col_ind):
            iou = 1 - cost_matrix[i, j]
            if iou >= self.iou_threshold:
                # Successful match: inherit track_id and label
                curr_shapes[j].track_id = prev_shapes[i].track_id
                curr_shapes[j].label = prev_shapes[i].label
                curr_shapes[j].is_tracked = True
                matched_curr_indices.add(j)
        
        # Assign new IDs to unmatched shapes
        for j, shape in enumerate(curr_shapes):
            if j not in matched_curr_indices:
                shape.track_id = self.next_track_id
                self.next_track_id += 1
                shape.is_tracked = False
    
    def reset(self):
        """Reset the tracker state."""
        self.next_track_id = 1
        self.prev_frame_shapes = []
    
    def update_prev_shapes(self, shapes):
        """
        Update the previous frame shapes for next tracking.
        
        Args:
            shapes: List of current frame shapes
        """
        # Create deep copies to avoid reference issues
        self.prev_frame_shapes = []
        for shape in shapes:
            if hasattr(shape, 'copy'):
                self.prev_frame_shapes.append(shape.copy())
            else:
                # Fallback if shape doesn't have copy method
                self.prev_frame_shapes.append(shape)