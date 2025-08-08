#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify Undo/Redo functionality
Run this to see debug output
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_undo_keys():
    """Test Qt key constants"""
    print("Testing Qt key constants:")
    print(f"  Qt.Key_Z = {Qt.Key_Z} (should be 90)")
    print(f"  Qt.Key_Y = {Qt.Key_Y} (should be 89)")
    print(f"  Qt.ControlModifier = {Qt.ControlModifier}")
    print()

def main():
    print("=" * 60)
    print("UNDO/REDO DEBUG TEST")
    print("=" * 60)
    
    # Test Qt constants
    test_undo_keys()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Import MainWindow after QApplication is created
    from labelImg import MainWindow
    
    print("Creating MainWindow...")
    window = MainWindow()
    
    print("\nInstructions:")
    print("1. Open an image file")
    print("2. Create a bounding box")
    print("3. Press Ctrl+Z to undo")
    print("4. Check the console output for debug messages")
    print()
    print("Watch for these debug messages:")
    print("  - [DEBUG] keyPressEvent: ...")
    print("  - [DEBUG] Ctrl+Z detected...")
    print("  - [DEBUG] undo_action called!")
    print("  - [UndoManager] ...")
    print()
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()