#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test to verify Undo/Redo logic without GUI
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.undo_manager import FrameUndoManager


def test_basic_undo():
    """Test basic undo functionality"""
    print("Testing basic undo functionality...")
    print("-" * 40)
    
    # Create manager
    manager = FrameUndoManager()
    test_file = "test_image.jpg"
    
    # Set current frame
    manager.set_current_frame(test_file)
    print(f"Current frame set to: {test_file}")
    
    # Initial state (empty)
    initial_state = {
        'file_path': test_file,
        'shapes': []
    }
    manager.save_state(initial_state, "initial")
    print(f"Saved initial state: 0 shapes")
    
    # Add first shape
    state1 = {
        'file_path': test_file,
        'shapes': [{'label': 'cow1', 'points': [(10, 10), (20, 20)]}]
    }
    manager.save_state(state1, "add_shape_1")
    print(f"Saved state 1: 1 shape")
    
    # Add second shape
    state2 = {
        'file_path': test_file,
        'shapes': [
            {'label': 'cow1', 'points': [(10, 10), (20, 20)]},
            {'label': 'cow2', 'points': [(30, 30), (40, 40)]}
        ]
    }
    manager.save_state(state2, "add_shape_2")
    print(f"Saved state 2: 2 shapes")
    
    # Check undo availability
    print(f"\nCan undo? {manager.can_undo()}")
    print(f"Can redo? {manager.can_redo()}")
    
    # Perform undo
    print("\nPerforming undo...")
    restored = manager.undo()
    if restored:
        print(f"Restored to: {len(restored['shapes'])} shapes")
        for i, shape in enumerate(restored['shapes']):
            print(f"  Shape {i}: {shape['label']}")
    else:
        print("Undo failed!")
    
    # Check status after undo
    print(f"\nAfter undo:")
    print(f"Can undo? {manager.can_undo()}")
    print(f"Can redo? {manager.can_redo()}")
    
    # Perform another undo
    print("\nPerforming second undo...")
    restored = manager.undo()
    if restored:
        print(f"Restored to: {len(restored['shapes'])} shapes")
    else:
        print("Undo failed!")
    
    # Try redo
    print("\nPerforming redo...")
    restored = manager.redo()
    if restored:
        print(f"Restored to: {len(restored['shapes'])} shapes")
        for i, shape in enumerate(restored['shapes']):
            print(f"  Shape {i}: {shape['label']}")
    else:
        print("Redo failed!")
    
    print("\n" + "=" * 40)
    print("Test completed!")


def test_keyboard_constants():
    """Test Qt keyboard constants"""
    print("\nTesting Qt keyboard constants...")
    print("-" * 40)
    
    try:
        from PyQt5.QtCore import Qt
        print(f"Qt.Key_Z = {Qt.Key_Z} (decimal)")
        print(f"Qt.Key_Z = 0x{Qt.Key_Z:X} (hex)")
        print(f"Qt.Key_Y = {Qt.Key_Y} (decimal)")
        print(f"Qt.Key_Y = 0x{Qt.Key_Y:X} (hex)")
        print(f"Qt.ControlModifier = {Qt.ControlModifier}")
        print(f"Qt.ControlModifier = 0x{Qt.ControlModifier:X} (hex)")
        
        # Test key combination
        print(f"\nCtrl+Z would be: modifiers=0x{Qt.ControlModifier:X}, key=0x{Qt.Key_Z:X}")
        
    except ImportError:
        print("PyQt5 not available for keyboard constant test")


if __name__ == '__main__':
    print("=" * 60)
    print("UNDO/REDO SIMPLE TEST")
    print("=" * 60)
    print()
    
    # Test basic undo logic
    test_basic_undo()
    
    # Test keyboard constants
    test_keyboard_constants()