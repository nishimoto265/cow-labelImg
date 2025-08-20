#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for undo/redo integration
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPointF

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from labelImg import MainWindow
from libs.shape import Shape
from libs.undo.commands.shape_commands import AddShapeCommand, DeleteShapeCommand
from libs.undo.commands.label_commands import ChangeLabelCommand


def test_undo_redo_integration():
    """Test undo/redo functionality"""
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    print("=" * 60)
    print("Testing Undo/Redo Integration")
    print("=" * 60)
    
    # Test 1: AddShapeCommand
    print("\n1. Testing AddShapeCommand...")
    shape_data = {
        'label': 'test_label',
        'points': [(100, 100), (200, 100), (200, 200), (100, 200)],
        'difficult': False
    }
    
    add_cmd = AddShapeCommand("test.jpg", shape_data)
    
    # Execute command
    if window.undo_manager.execute_command(add_cmd):
        print("   ✓ AddShapeCommand executed")
        print(f"   Canvas has {len(window.canvas.shapes)} shapes")
    else:
        print("   ✗ AddShapeCommand failed")
    
    # Test undo
    if window.undo_manager.can_undo():
        print("   Can undo: Yes")
        if window.undo_manager.undo():
            print("   ✓ Undo successful")
            print(f"   Canvas has {len(window.canvas.shapes)} shapes")
        else:
            print("   ✗ Undo failed")
    
    # Test redo
    if window.undo_manager.can_redo():
        print("   Can redo: Yes")
        if window.undo_manager.redo():
            print("   ✓ Redo successful")
            print(f"   Canvas has {len(window.canvas.shapes)} shapes")
        else:
            print("   ✗ Redo failed")
    
    # Test 2: Multiple commands
    print("\n2. Testing multiple commands...")
    for i in range(3):
        shape_data = {
            'label': f'shape_{i}',
            'points': [(100+i*50, 100), (200+i*50, 100), (200+i*50, 200), (100+i*50, 200)],
            'difficult': False
        }
        cmd = AddShapeCommand("test.jpg", shape_data)
        window.undo_manager.execute_command(cmd)
    
    print(f"   Added 3 shapes. Canvas has {len(window.canvas.shapes)} shapes")
    
    # Undo all
    print("\n3. Testing undo all...")
    undo_count = 0
    while window.undo_manager.can_undo():
        if window.undo_manager.undo():
            undo_count += 1
    
    print(f"   Undid {undo_count} commands")
    print(f"   Canvas has {len(window.canvas.shapes)} shapes")
    
    # Redo some
    print("\n4. Testing partial redo...")
    redo_count = 0
    for _ in range(2):
        if window.undo_manager.can_redo():
            if window.undo_manager.redo():
                redo_count += 1
    
    print(f"   Redid {redo_count} commands")
    print(f"   Canvas has {len(window.canvas.shapes)} shapes")
    
    # Test UI update
    print("\n5. Testing UI updates...")
    print(f"   Undo action enabled: {window.actions.undo.isEnabled() if hasattr(window.actions, 'undo') else 'N/A'}")
    print(f"   Redo action enabled: {window.actions.redo.isEnabled() if hasattr(window.actions, 'redo') else 'N/A'}")
    
    # Test history info
    print("\n6. History information:")
    history = window.undo_manager.get_history_info()
    for item in history:
        print(f"   {item}")
    
    print("\n" + "=" * 60)
    print("Integration test completed!")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(test_undo_redo_integration())