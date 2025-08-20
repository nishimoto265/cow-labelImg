#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for Shape-related Commands
TDD approach - write tests first, then implementation
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
from PyQt5.QtCore import QPointF

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAddShapeCommand(unittest.TestCase):
    """Test AddShapeCommand functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        self.app.canvas.shapes = []
        self.app.label_list = Mock()
        self.app.items_to_shapes = {}
        self.app.shapes_to_items = {}
        self.app.auto_saving = Mock()
        self.app.auto_saving.isChecked.return_value = False
        self.app.set_dirty = Mock()
        self.app.save_file = Mock()
        self.app.add_label = Mock()
        self.app.load_file = Mock()
        
        self.shape_data = {
            'label': 'cow_1',
            'points': [(100, 100), (200, 100), (200, 200), (100, 200)],
            'line_color': (255, 0, 0, 128),
            'fill_color': (255, 0, 0, 50)
        }
    
    def test_add_shape_command_creation(self):
        """Test creating AddShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import AddShapeCommand
            
            cmd = AddShapeCommand("frame1.png", self.shape_data)
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape_data, self.shape_data)
            self.assertIsNone(cmd.shape_index)
            
        except ImportError:
            self.skipTest("AddShapeCommand not implemented yet")
    
    def test_add_shape_execute(self):
        """Test executing AddShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import AddShapeCommand
            from libs.shape import Shape
            
            cmd = AddShapeCommand("frame1.png", self.shape_data)
            
            # Execute command
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # Should add shape to canvas
            self.assertEqual(len(self.app.canvas.shapes), 1)
            # Should call add_label
            self.app.add_label.assert_called_once()
            # Should mark as dirty
            self.app.set_dirty.assert_called_once()
            # Should record shape index
            self.assertEqual(cmd.shape_index, 0)
            
        except ImportError:
            self.skipTest("AddShapeCommand not implemented yet")
    
    def test_add_shape_undo(self):
        """Test undoing AddShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import AddShapeCommand
            from libs.shape import Shape
            
            # Create mock shape
            mock_shape = Mock()
            mock_shape.label = "cow_1"
            
            cmd = AddShapeCommand("frame1.png", self.shape_data)
            
            # Simulate execute
            self.app.canvas.shapes.append(mock_shape)
            cmd.shape_index = 0
            cmd.added_shape = mock_shape
            
            # Add to items mapping
            mock_item = Mock()
            self.app.shapes_to_items[mock_shape] = mock_item
            self.app.items_to_shapes[mock_item] = mock_shape
            self.app.label_list.row.return_value = 0
            
            # Undo command
            result = cmd.undo(self.app)
            
            self.assertTrue(result)
            # Should remove shape from canvas
            self.assertEqual(len(self.app.canvas.shapes), 0)
            # Should remove from mappings
            self.assertEqual(len(self.app.shapes_to_items), 0)
            self.assertEqual(len(self.app.items_to_shapes), 0)
            # Should mark as dirty
            self.app.set_dirty.assert_called()
            
        except ImportError:
            self.skipTest("AddShapeCommand not implemented yet")
    
    def test_add_shape_with_frame_switch(self):
        """Test AddShapeCommand with frame switching"""
        try:
            from libs.undo.commands.shape_commands import AddShapeCommand
            
            # Set current frame different from target
            self.app.file_path = "current_frame.png"
            
            cmd = AddShapeCommand("target_frame.png", self.shape_data)
            result = cmd.execute(self.app)
            
            # Should load target frame
            self.app.load_file.assert_called_with("target_frame.png", preserve_zoom=True)
            
        except ImportError:
            self.skipTest("AddShapeCommand not implemented yet")


class TestDeleteShapeCommand(unittest.TestCase):
    """Test DeleteShapeCommand functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        
        # Create mock shape
        self.mock_shape = Mock()
        self.mock_shape.label = "cow_1"
        self.mock_shape.points = [QPointF(100, 100), QPointF(200, 200)]
        
        self.app.canvas.shapes = [self.mock_shape]
        self.app.set_dirty = Mock()
        self.app.save_file = Mock()
        self.app.load_file = Mock()
        self.app.auto_saving = Mock()
        self.app.auto_saving.isChecked.return_value = False
    
    def test_delete_shape_command_creation(self):
        """Test creating DeleteShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import DeleteShapeCommand
            
            cmd = DeleteShapeCommand("frame1.png", 0, self.mock_shape)
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape_index, 0)
            self.assertIsNotNone(cmd.shape_data)
            
        except ImportError:
            self.skipTest("DeleteShapeCommand not implemented yet")
    
    def test_delete_shape_execute(self):
        """Test executing DeleteShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import DeleteShapeCommand
            
            cmd = DeleteShapeCommand("frame1.png", 0, self.mock_shape)
            
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # Should remove shape from canvas
            self.assertEqual(len(self.app.canvas.shapes), 0)
            # Should mark as dirty
            self.app.set_dirty.assert_called_once()
            
        except ImportError:
            self.skipTest("DeleteShapeCommand not implemented yet")
    
    def test_delete_shape_undo(self):
        """Test undoing DeleteShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import DeleteShapeCommand
            
            cmd = DeleteShapeCommand("frame1.png", 0, self.mock_shape)
            
            # Execute first (remove shape)
            self.app.canvas.shapes.clear()
            
            # Undo (restore shape)
            result = cmd.undo(self.app)
            
            self.assertTrue(result)
            # Should restore shape to canvas
            self.assertEqual(len(self.app.canvas.shapes), 1)
            # Should be at correct position
            self.assertEqual(self.app.canvas.shapes[0].label, "cow_1")
            
        except ImportError:
            self.skipTest("DeleteShapeCommand not implemented yet")


class TestMoveShapeCommand(unittest.TestCase):
    """Test MoveShapeCommand functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        
        # Create mock shape
        self.mock_shape = Mock()
        self.mock_shape.points = [
            QPointF(100, 100), QPointF(200, 100),
            QPointF(200, 200), QPointF(100, 200)
        ]
        
        self.app.canvas.shapes = [self.mock_shape]
        self.app.set_dirty = Mock()
        self.app.load_file = Mock()
        
        self.old_points = [(100, 100), (200, 100), (200, 200), (100, 200)]
        self.new_points = [(150, 150), (250, 150), (250, 250), (150, 250)]
    
    def test_move_shape_command_creation(self):
        """Test creating MoveShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import MoveShapeCommand
            
            cmd = MoveShapeCommand("frame1.png", 0, self.old_points, self.new_points)
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape_index, 0)
            self.assertEqual(cmd.old_points, self.old_points)
            self.assertEqual(cmd.new_points, self.new_points)
            
        except ImportError:
            self.skipTest("MoveShapeCommand not implemented yet")
    
    def test_move_shape_execute(self):
        """Test executing MoveShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import MoveShapeCommand
            
            cmd = MoveShapeCommand("frame1.png", 0, self.old_points, self.new_points)
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # Should update shape points
            shape = self.app.canvas.shapes[0]
            # Check first point moved
            self.assertEqual(shape.points[0].x(), 150)
            self.assertEqual(shape.points[0].y(), 150)
            
        except ImportError:
            self.skipTest("MoveShapeCommand not implemented yet")
    
    def test_move_shape_undo(self):
        """Test undoing MoveShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import MoveShapeCommand
            
            cmd = MoveShapeCommand("frame1.png", 0, self.old_points, self.new_points)
            
            # Execute (move to new position)
            cmd.execute(self.app)
            
            # Undo (move back to old position)
            result = cmd.undo(self.app)
            
            self.assertTrue(result)
            shape = self.app.canvas.shapes[0]
            # Should restore original position
            self.assertEqual(shape.points[0].x(), 100)
            self.assertEqual(shape.points[0].y(), 100)
            
        except ImportError:
            self.skipTest("MoveShapeCommand not implemented yet")
    
    def test_move_shape_merge(self):
        """Test merging consecutive move commands"""
        try:
            from libs.undo.commands.shape_commands import MoveShapeCommand
            
            # First move: 100,100 -> 150,150
            cmd1 = MoveShapeCommand("frame1.png", 0,
                                   [(100, 100)], [(150, 150)])
            
            # Second move: 150,150 -> 200,200
            cmd2 = MoveShapeCommand("frame1.png", 0,
                                   [(150, 150)], [(200, 200)])
            
            # Should be mergeable
            self.assertTrue(cmd1.can_merge_with(cmd2))
            
            # Merge should keep first old position and last new position
            merged = cmd1.merge(cmd2)
            self.assertEqual(merged.old_points, [(100, 100)])
            self.assertEqual(merged.new_points, [(200, 200)])
            
        except ImportError:
            self.skipTest("MoveShapeCommand not implemented yet")


class TestResizeShapeCommand(unittest.TestCase):
    """Test ResizeShapeCommand functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        
        self.mock_shape = Mock()
        self.old_rect = (100, 100, 200, 200)  # x, y, width, height
        self.new_rect = (100, 100, 300, 300)  # Resized
        
        self.app.canvas.shapes = [self.mock_shape]
        self.app.set_dirty = Mock()
    
    def test_resize_shape_command_creation(self):
        """Test creating ResizeShapeCommand"""
        try:
            from libs.undo.commands.shape_commands import ResizeShapeCommand
            
            cmd = ResizeShapeCommand("frame1.png", 0, self.old_rect, self.new_rect)
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape_index, 0)
            self.assertEqual(cmd.old_rect, self.old_rect)
            self.assertEqual(cmd.new_rect, self.new_rect)
            
        except ImportError:
            self.skipTest("ResizeShapeCommand not implemented yet")
    
    def test_resize_shape_merge(self):
        """Test merging consecutive resize commands"""
        try:
            from libs.undo.commands.shape_commands import ResizeShapeCommand
            
            # First resize: 200x200 -> 250x250
            cmd1 = ResizeShapeCommand("frame1.png", 0,
                                    (100, 100, 200, 200),
                                    (100, 100, 250, 250))
            
            # Second resize: 250x250 -> 300x300
            cmd2 = ResizeShapeCommand("frame1.png", 0,
                                    (100, 100, 250, 250),
                                    (100, 100, 300, 300))
            
            # Should be mergeable
            self.assertTrue(cmd1.can_merge_with(cmd2))
            
            # Merge should keep original size and final size
            merged = cmd1.merge(cmd2)
            self.assertEqual(merged.old_rect, (100, 100, 200, 200))
            self.assertEqual(merged.new_rect, (100, 100, 300, 300))
            
        except ImportError:
            self.skipTest("ResizeShapeCommand not implemented yet")


class TestDuplicateShapeCommand(unittest.TestCase):
    """Test shape duplication commands"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        self.app.canvas.shapes = []
        self.app.add_label = Mock()
        self.app.set_dirty = Mock()
        
        self.source_shape = Mock()
        self.source_shape.label = "cow_1"
        self.source_shape.points = [QPointF(100, 100), QPointF(200, 200)]
    
    def test_duplicate_shape_in_frame(self):
        """Test duplicating shape within same frame"""
        try:
            from libs.undo.commands.shape_commands import DuplicateShapeCommand
            
            cmd = DuplicateShapeCommand("frame1.png", self.source_shape)
            
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # Should add duplicated shape
            self.assertEqual(len(self.app.canvas.shapes), 1)
            # Should have same label
            self.assertEqual(self.app.canvas.shapes[0].label, "cow_1")
            
        except ImportError:
            self.skipTest("DuplicateShapeCommand not implemented yet")
    
    def test_multi_frame_duplicate(self):
        """Test duplicating shape to multiple frames"""
        try:
            from libs.undo.commands.shape_commands import MultiFrameDuplicateCommand
            
            target_frames = ["frame1.png", "frame2.png", "frame3.png"]
            cmd = MultiFrameDuplicateCommand(self.source_shape, target_frames)
            
            # Should create composite command with multiple add commands
            self.assertEqual(len(cmd.commands), 3)
            
        except ImportError:
            self.skipTest("MultiFrameDuplicateCommand not implemented yet")


if __name__ == '__main__':
    unittest.main()