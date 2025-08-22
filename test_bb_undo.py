#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for BB duplication undo/redo functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPointF
from libs.shape import Shape
from libs.undo.commands.bb_duplication_commands import AddShapeWithIOUCheckCommand

def test_bb_duplication_undo():
    """Test BB duplication with overlap removal and undo"""
    
    # Create a mock app object
    class MockApp:
        def __init__(self):
            self.file_path = "test.jpg"
            self.canvas = MockCanvas()
            self.removed_labels = []
        
        def load_file(self, path, preserve_zoom=True):
            pass
        
        def add_label(self, shape):
            print(f"[Test] Added label: {shape.label}")
        
        def remove_label(self, shape):
            print(f"[Test] Removed label: {shape.label}")
            self.removed_labels.append(shape.label)
        
        def set_dirty(self):
            pass
    
    class MockCanvas:
        def __init__(self):
            self.shapes = []
            
            # Add an existing shape that will be removed
            existing_shape = Shape()
            existing_shape.label = "Existing_BB"
            existing_shape.points = [
                QPointF(100, 100),
                QPointF(200, 100),
                QPointF(200, 200),
                QPointF(100, 200)
            ]
            existing_shape.close()
            self.shapes.append(existing_shape)
        
        def update(self):
            pass
        
        def load_shapes(self, shapes):
            pass
    
    app = MockApp()
    
    print("=== Initial state ===")
    print(f"Canvas shapes: {[s.label for s in app.canvas.shapes]}")
    
    # Create a new shape that overlaps with existing one
    new_shape_data = {
        'label': 'New_BB',
        'points': [
            (105, 105),  # Overlapping position
            (205, 105),
            (205, 205),
            (105, 205)
        ],
        'difficult': False
    }
    
    # Create command with overwrite mode
    cmd = AddShapeWithIOUCheckCommand(
        frame_path="test.jpg",
        shape_data=new_shape_data,
        iou_threshold=0.5,
        overwrite_mode=True  # This should remove the existing BB
    )
    
    print("\n=== Execute: Add new BB with overwrite ===")
    result = cmd.execute(app)
    print(f"Execute result: {result}")
    print(f"Canvas shapes: {[s.label for s in app.canvas.shapes]}")
    print(f"Removed shapes stored: {len(cmd.removed_shapes)}")
    
    print("\n=== Undo: Should restore removed BB ===")
    result = cmd.undo(app)
    print(f"Undo result: {result}")
    print(f"Canvas shapes: {[s.label for s in app.canvas.shapes]}")
    
    print("\n=== Redo: Should remove existing BB again ===")
    result = cmd.redo(app)
    print(f"Redo result: {result}")
    print(f"Canvas shapes: {[s.label for s in app.canvas.shapes]}")
    
    print("\n=== Test completed ===")
    if len(app.canvas.shapes) == 1 and app.canvas.shapes[0].label == 'New_BB':
        print("Test PASSED: BB duplication undo/redo works correctly")
    else:
        print("Test FAILED: Unexpected state")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_bb_duplication_undo()
    sys.exit(0)