#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for dual label functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPointF
from libs.shape import Shape
from libs.dualLabelDialog import DualLabelDialog

def test_shape_dual_label():
    """Test Shape class with dual labels"""
    print("=== Testing Shape class with dual labels ===")
    
    # Create a shape with both labels
    shape = Shape(label="Cow", label2="ID-001")
    shape.add_point(QPointF(100, 100))
    shape.add_point(QPointF(200, 100))
    shape.add_point(QPointF(200, 200))
    shape.add_point(QPointF(100, 200))
    shape.close()
    
    print(f"Shape label1: {shape.label1}")
    print(f"Shape label2: {shape.label2}")
    print(f"Shape label (backward compatibility): {shape.label}")
    
    # Test copy functionality
    shape_copy = shape.copy()
    print(f"\nCopied shape label1: {shape_copy.label1}")
    print(f"Copied shape label2: {shape_copy.label2}")
    
    # Test display settings
    shape.show_label1 = True
    shape.show_label2 = False
    print(f"\nShow label1: {shape.show_label1}")
    print(f"Show label2: {shape.show_label2}")
    
    print("\nShape dual label test completed")

def test_dual_label_dialog():
    """Test DualLabelDialog"""
    print("\n=== Testing DualLabelDialog ===")
    
    app = QApplication(sys.argv)
    
    # Create dialog with sample lists
    list1 = ["Cow", "Horse", "Sheep", "Goat"]
    list2 = ["ID-001", "ID-002", "ID-003", "ID-004", "ID-005"]
    
    dialog = DualLabelDialog(
        label1="Cow",
        label2="ID-001",
        list_item1=list1,
        list_item2=list2
    )
    
    print(f"Dialog created with initial values:")
    print(f"  Label 1: {dialog.edit1.text()}")
    print(f"  Label 2: {dialog.edit2.text()}")
    
    # Test validation
    dialog.edit1.setText("TestLabel1")
    dialog.edit2.setText("TestLabel2")
    dialog.post_process1()
    dialog.post_process2()
    
    print(f"\nAfter setting new values:")
    print(f"  Label 1: {dialog.edit1.text()}")
    print(f"  Label 2: {dialog.edit2.text()}")
    
    print("\nDualLabelDialog test completed")

def test_dual_label_command():
    """Test ChangeDualLabelCommand"""
    print("\n=== Testing ChangeDualLabelCommand ===")
    
    from libs.undo.commands.dual_label_commands import ChangeDualLabelCommand
    
    # Create a mock app object
    class MockApp:
        def __init__(self):
            self.file_path = "test.jpg"
            self.canvas = MockCanvas()
            self.shapes_to_items = {}
            self.auto_saving = MockCheckbox()
        
        def load_file(self, path, preserve_zoom=True):
            pass
        
        def set_dirty(self):
            pass
        
        def save_file(self):
            pass
    
    class MockCanvas:
        def __init__(self):
            # Create a test shape
            shape = Shape(label="Cow", label2="ID-001")
            shape.add_point(QPointF(100, 100))
            shape.add_point(QPointF(200, 100))
            shape.add_point(QPointF(200, 200))
            shape.add_point(QPointF(100, 200))
            shape.close()
            self.shapes = [shape]
        
        def load_shapes(self, shapes):
            pass
        
        def update(self):
            pass
    
    class MockCheckbox:
        def isChecked(self):
            return False
    
    app = MockApp()
    
    # Create command to change both labels
    cmd = ChangeDualLabelCommand(
        frame_path="test.jpg",
        shape_index=0,
        old_label1="Cow",
        new_label1="Horse",
        old_label2="ID-001",
        new_label2="ID-002",
        change_label1=True,
        change_label2=True
    )
    
    print(f"Initial shape labels:")
    print(f"  Label1: {app.canvas.shapes[0].label1}")
    print(f"  Label2: {app.canvas.shapes[0].label2}")
    
    # Execute command
    result = cmd.execute(app)
    print(f"\nAfter execute (result={result}):")
    print(f"  Label1: {app.canvas.shapes[0].label1}")
    print(f"  Label2: {app.canvas.shapes[0].label2}")
    
    # Undo command
    result = cmd.undo(app)
    print(f"\nAfter undo (result={result}):")
    print(f"  Label1: {app.canvas.shapes[0].label1}")
    print(f"  Label2: {app.canvas.shapes[0].label2}")
    
    # Redo command
    result = cmd.redo(app)
    print(f"\nAfter redo (result={result}):")
    print(f"  Label1: {app.canvas.shapes[0].label1}")
    print(f"  Label2: {app.canvas.shapes[0].label2}")
    
    print(f"\nCommand description: {cmd.description}")
    
    print("\nChangeDualLabelCommand test completed")

if __name__ == "__main__":
    print("Starting dual label system tests...\n")
    
    test_shape_dual_label()
    test_dual_label_dialog()
    test_dual_label_command()
    
    print("\n=== All tests completed successfully! ===")
    sys.exit(0)