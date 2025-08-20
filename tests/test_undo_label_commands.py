#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for Label-related Commands
TDD approach - write tests first, then implementation
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChangeLabelCommand(unittest.TestCase):
    """Test ChangeLabelCommand functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        
        # Create mock shape with label
        self.mock_shape = Mock()
        self.mock_shape.label = "cow_1"
        
        # Create mock list item
        self.mock_item = Mock()
        self.mock_item.text.return_value = "cow_1"
        
        self.app.canvas.shapes = [self.mock_shape]
        self.app.shapes_to_items = {self.mock_shape: self.mock_item}
        self.app.items_to_shapes = {self.mock_item: self.mock_shape}
        self.app.set_dirty = Mock()
        self.app.save_file = Mock()
        self.app.load_file = Mock()
        self.app.update_combo_box = Mock()
        self.app.auto_saving = Mock()
        self.app.auto_saving.isChecked.return_value = False
    
    def test_change_label_command_creation(self):
        """Test creating ChangeLabelCommand"""
        try:
            from libs.undo.commands.label_commands import ChangeLabelCommand
            
            cmd = ChangeLabelCommand("frame1.png", 0, "cow_1", "cow_2")
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape_index, 0)
            self.assertEqual(cmd.old_label, "cow_1")
            self.assertEqual(cmd.new_label, "cow_2")
            
        except ImportError:
            self.skipTest("ChangeLabelCommand not implemented yet")
    
    def test_change_label_execute(self):
        """Test executing ChangeLabelCommand"""
        try:
            from libs.undo.commands.label_commands import ChangeLabelCommand
            
            cmd = ChangeLabelCommand("frame1.png", 0, "cow_1", "cow_2")
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # Should change shape label
            self.assertEqual(self.mock_shape.label, "cow_2")
            # Should update list item text
            self.mock_item.setText.assert_called_with("cow_2")
            # Should mark as dirty
            self.app.set_dirty.assert_called()
            # Should update combo box
            self.app.update_combo_box.assert_called()
            
        except ImportError:
            self.skipTest("ChangeLabelCommand not implemented yet")
    
    def test_change_label_undo(self):
        """Test undoing ChangeLabelCommand"""
        try:
            from libs.undo.commands.label_commands import ChangeLabelCommand
            
            cmd = ChangeLabelCommand("frame1.png", 0, "cow_1", "cow_2")
            
            # Execute first
            self.mock_shape.label = "cow_2"
            
            # Undo
            result = cmd.undo(self.app)
            
            self.assertTrue(result)
            # Should restore original label
            self.assertEqual(self.mock_shape.label, "cow_1")
            # Should update list item
            self.mock_item.setText.assert_called_with("cow_1")
            
        except ImportError:
            self.skipTest("ChangeLabelCommand not implemented yet")


class TestApplyQuickIDCommand(unittest.TestCase):
    """Test ApplyQuickIDCommand functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        self.app.selectedShape = Mock()
        self.app.selectedShape.label = "old_label"
        
        # Mock Quick ID related methods
        self.app.get_class_name_for_quick_id = Mock(return_value="1")
        self.app.shapes_to_items = {}
        self.app.set_dirty = Mock()
        self.app.update_combo_box = Mock()
    
    def test_apply_quick_id_command_creation(self):
        """Test creating ApplyQuickIDCommand"""
        try:
            from libs.undo.commands.label_commands import ApplyQuickIDCommand
            
            cmd = ApplyQuickIDCommand("frame1.png", self.app.selectedShape, "5")
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.quick_id, "5")
            self.assertEqual(cmd.old_label, "old_label")
            
        except ImportError:
            self.skipTest("ApplyQuickIDCommand not implemented yet")
    
    def test_apply_quick_id_execute(self):
        """Test executing ApplyQuickIDCommand"""
        try:
            from libs.undo.commands.label_commands import ApplyQuickIDCommand
            
            self.app.get_class_name_for_quick_id.return_value = "5"
            
            cmd = ApplyQuickIDCommand("frame1.png", self.app.selectedShape, "5")
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # Should apply quick ID
            self.assertEqual(self.app.selectedShape.label, "5")
            
        except ImportError:
            self.skipTest("ApplyQuickIDCommand not implemented yet")
    
    def test_apply_quick_id_undo(self):
        """Test undoing ApplyQuickIDCommand"""
        try:
            from libs.undo.commands.label_commands import ApplyQuickIDCommand
            
            cmd = ApplyQuickIDCommand("frame1.png", self.app.selectedShape, "5")
            cmd.old_label = "old_label"
            
            # Execute first
            self.app.selectedShape.label = "5"
            
            # Undo
            result = cmd.undo(self.app)
            
            self.assertTrue(result)
            # Should restore original label
            self.assertEqual(self.app.selectedShape.label, "old_label")
            
        except ImportError:
            self.skipTest("ApplyQuickIDCommand not implemented yet")


class TestPropagateLabelCommand(unittest.TestCase):
    """Test label propagation commands"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "frame1.png"
        self.app.m_img_list = ["frame1.png", "frame2.png", "frame3.png", "frame4.png"]
        self.app.cur_img_idx = 0
        
        # Mock shape to propagate
        self.source_shape = Mock()
        self.source_shape.label = "old_label"
        self.source_shape.points = []
        
        self.app.load_file = Mock()
        self.app.save_file = Mock()
        self.app.set_dirty = Mock()
    
    def test_propagate_label_command_creation(self):
        """Test creating PropagateLabelCommand"""
        try:
            from libs.undo.commands.label_commands import PropagateLabelCommand
            
            affected_frames = ["frame2.png", "frame3.png"]
            cmd = PropagateLabelCommand(
                self.source_shape,
                "new_label",
                affected_frames
            )
            
            self.assertEqual(cmd.source_shape, self.source_shape)
            self.assertEqual(cmd.new_label, "new_label")
            self.assertEqual(cmd.affected_frames, affected_frames)
            
        except ImportError:
            self.skipTest("PropagateLabelCommand not implemented yet")
    
    def test_propagate_label_execute(self):
        """Test executing PropagateLabelCommand"""
        try:
            from libs.undo.commands.label_commands import PropagateLabelCommand
            
            affected_frames = ["frame2.png", "frame3.png"]
            cmd = PropagateLabelCommand(
                self.source_shape,
                "new_label",
                affected_frames
            )
            
            # Should store original states
            self.assertIsNotNone(cmd.original_states)
            
        except ImportError:
            self.skipTest("PropagateLabelCommand not implemented yet")
    
    def test_propagate_quick_id_command(self):
        """Test PropagateQuickIDCommand"""
        try:
            from libs.undo.commands.label_commands import PropagateQuickIDCommand
            
            affected_frames = ["frame2.png", "frame3.png"]
            cmd = PropagateQuickIDCommand(
                self.source_shape,
                "5",  # Quick ID
                affected_frames
            )
            
            self.assertEqual(cmd.quick_id, "5")
            self.assertEqual(cmd.affected_frames, affected_frames)
            
        except ImportError:
            self.skipTest("PropagateQuickIDCommand not implemented yet")


class TestBatchChangeLabelCommand(unittest.TestCase):
    """Test batch label change commands"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        
        # Create multiple mock shapes
        self.shapes = []
        for i in range(3):
            shape = Mock()
            shape.label = f"old_{i}"
            self.shapes.append(shape)
        
        self.app.canvas = Mock()
        self.app.canvas.shapes = self.shapes
    
    def test_batch_change_label_creation(self):
        """Test creating BatchChangeLabelCommand"""
        try:
            from libs.undo.commands.label_commands import BatchChangeLabelCommand
            
            shape_indices = [0, 1, 2]
            cmd = BatchChangeLabelCommand(
                "frame1.png",
                shape_indices,
                "old_label",
                "new_label"
            )
            
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape_indices, shape_indices)
            self.assertEqual(cmd.new_label, "new_label")
            
        except ImportError:
            self.skipTest("BatchChangeLabelCommand not implemented yet")
    
    def test_batch_change_label_execute(self):
        """Test executing batch label change"""
        try:
            from libs.undo.commands.label_commands import BatchChangeLabelCommand
            
            shape_indices = [0, 1, 2]
            cmd = BatchChangeLabelCommand(
                "frame1.png",
                shape_indices,
                "old_label",
                "new_label"
            )
            
            result = cmd.execute(self.app)
            
            self.assertTrue(result)
            # All shapes should have new label
            for shape in self.shapes:
                self.assertEqual(shape.label, "new_label")
            
        except ImportError:
            self.skipTest("BatchChangeLabelCommand not implemented yet")
    
    def test_batch_change_label_undo(self):
        """Test undoing batch label change"""
        try:
            from libs.undo.commands.label_commands import BatchChangeLabelCommand
            
            # Store original labels
            original_labels = ["old_0", "old_1", "old_2"]
            
            cmd = BatchChangeLabelCommand(
                "frame1.png",
                [0, 1, 2],
                original_labels,
                "new_label"
            )
            
            # Execute first
            for shape in self.shapes:
                shape.label = "new_label"
            
            # Undo
            result = cmd.undo(self.app)
            
            self.assertTrue(result)
            # Should restore original labels
            for i, shape in enumerate(self.shapes):
                self.assertEqual(shape.label, f"old_{i}")
            
        except ImportError:
            self.skipTest("BatchChangeLabelCommand not implemented yet")


class TestClickChangeLabelCommand(unittest.TestCase):
    """Test click-to-change label functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.click_change_label_mode = True
        self.app.continuous_tracking_mode = False
        
        self.mock_shape = Mock()
        self.mock_shape.label = "old_label"
        
        self.mock_item = Mock()
        self.app.shapes_to_items = {self.mock_shape: self.mock_item}
    
    def test_click_change_label_command(self):
        """Test ClickChangeLabelCommand"""
        try:
            from libs.undo.commands.label_commands import ClickChangeLabelCommand
            
            cmd = ClickChangeLabelCommand(
                "frame1.png",
                self.mock_shape,
                self.mock_item,
                "old_label",
                "new_label"
            )
            
            self.assertEqual(cmd.frame_path, "frame1.png")
            self.assertEqual(cmd.shape, self.mock_shape)
            self.assertEqual(cmd.old_label, "old_label")
            self.assertEqual(cmd.new_label, "new_label")
            
        except ImportError:
            self.skipTest("ClickChangeLabelCommand not implemented yet")
    
    def test_click_change_with_propagation(self):
        """Test click change with continuous tracking mode"""
        try:
            from libs.undo.commands.label_commands import ClickChangeLabelCommand
            
            self.app.continuous_tracking_mode = True
            
            cmd = ClickChangeLabelCommand(
                "frame1.png",
                self.mock_shape,
                self.mock_item,
                "old_label",
                "new_label",
                propagate=True,
                affected_frames=["frame2.png", "frame3.png"]
            )
            
            # Should handle propagation
            self.assertTrue(cmd.propagate)
            self.assertEqual(len(cmd.affected_frames), 2)
            
        except ImportError:
            self.skipTest("ClickChangeLabelCommand not implemented yet")


if __name__ == '__main__':
    unittest.main()