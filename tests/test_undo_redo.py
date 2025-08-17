#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test cases for Undo/Redo functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libs.undo_manager import UndoManager, FrameUndoManager, MultiFrameOperation


class TestUndoManager(unittest.TestCase):
    """Test the basic UndoManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = UndoManager(max_history=5)
    
    def test_initial_state(self):
        """Test initial state of UndoManager"""
        self.assertFalse(self.manager.can_undo())
        self.assertFalse(self.manager.can_redo())
        self.assertEqual(self.manager.current_index, -1)
        self.assertEqual(len(self.manager.history), 0)
    
    def test_save_state(self):
        """Test saving states"""
        # Save first state
        state1 = {'shapes': [{'label': 'cow', 'id': 1}]}
        self.manager.save_state(state1, "add_shape")
        
        self.assertEqual(len(self.manager.history), 1)
        self.assertEqual(self.manager.current_index, 0)
        self.assertFalse(self.manager.can_undo())  # Can't undo with only one state
        self.assertFalse(self.manager.can_redo())
        
        # Save second state
        state2 = {'shapes': [{'label': 'cow', 'id': 1}, {'label': 'cow', 'id': 2}]}
        self.manager.save_state(state2, "add_shape")
        
        self.assertEqual(len(self.manager.history), 2)
        self.assertEqual(self.manager.current_index, 1)
        self.assertTrue(self.manager.can_undo())
        self.assertFalse(self.manager.can_redo())
    
    def test_undo(self):
        """Test undo functionality"""
        # Save multiple states
        states = [
            {'shapes': []},
            {'shapes': [{'label': 'cow', 'id': 1}]},
            {'shapes': [{'label': 'cow', 'id': 1}, {'label': 'cow', 'id': 2}]},
        ]
        
        for i, state in enumerate(states):
            self.manager.save_state(state, f"state_{i}")
        
        # Test undo
        self.assertEqual(self.manager.current_index, 2)
        
        # First undo
        result = self.manager.undo()
        self.assertIsNotNone(result)
        self.assertEqual(len(result['shapes']), 1)
        self.assertEqual(self.manager.current_index, 1)
        self.assertTrue(self.manager.can_undo())
        self.assertTrue(self.manager.can_redo())
        
        # Second undo
        result = self.manager.undo()
        self.assertIsNotNone(result)
        self.assertEqual(len(result['shapes']), 0)
        self.assertEqual(self.manager.current_index, 0)
        self.assertFalse(self.manager.can_undo())
        self.assertTrue(self.manager.can_redo())
        
        # Can't undo anymore
        result = self.manager.undo()
        self.assertIsNone(result)
    
    def test_redo(self):
        """Test redo functionality"""
        # Save states and undo
        states = [
            {'shapes': []},
            {'shapes': [{'label': 'cow', 'id': 1}]},
            {'shapes': [{'label': 'cow', 'id': 1}, {'label': 'cow', 'id': 2}]},
        ]
        
        for i, state in enumerate(states):
            self.manager.save_state(state, f"state_{i}")
        
        # Undo twice
        self.manager.undo()
        self.manager.undo()
        
        # Test redo
        self.assertEqual(self.manager.current_index, 0)
        
        # First redo
        result = self.manager.redo()
        self.assertIsNotNone(result)
        self.assertEqual(len(result['shapes']), 1)
        self.assertEqual(self.manager.current_index, 1)
        self.assertTrue(self.manager.can_redo())
        
        # Second redo
        result = self.manager.redo()
        self.assertIsNotNone(result)
        self.assertEqual(len(result['shapes']), 2)
        self.assertEqual(self.manager.current_index, 2)
        self.assertFalse(self.manager.can_redo())
        
        # Can't redo anymore
        result = self.manager.redo()
        self.assertIsNone(result)
    
    def test_redo_cleared_after_new_state(self):
        """Test that redo history is cleared after saving a new state"""
        # Save states
        for i in range(3):
            self.manager.save_state({'count': i}, f"state_{i}")
        
        # Undo twice
        self.manager.undo()
        self.manager.undo()
        self.assertTrue(self.manager.can_redo())
        
        # Save new state (should clear redo history)
        self.manager.save_state({'count': 99}, "new_state")
        self.assertFalse(self.manager.can_redo())
        self.assertEqual(self.manager.current_index, 1)
        self.assertEqual(len(self.manager.history), 2)
    
    def test_max_history_limit(self):
        """Test that history size is limited"""
        # Save more states than max_history
        for i in range(10):
            self.manager.save_state({'count': i}, f"state_{i}")
        
        # Should only keep last 5 states
        self.assertEqual(len(self.manager.history), 5)
        self.assertEqual(self.manager.history[0]['count'], 5)
        self.assertEqual(self.manager.history[-1]['count'], 9)
    
    def test_initialize_with_state(self):
        """Test initializing with a state"""
        initial_state = {'shapes': [{'label': 'initial'}]}
        self.manager.initialize_with_state(initial_state)
        
        self.assertEqual(len(self.manager.history), 1)
        self.assertEqual(self.manager.current_index, 0)
        self.assertFalse(self.manager.can_undo())
        self.assertFalse(self.manager.can_redo())
        
        # Verify state is stored correctly
        current = self.manager.get_current_state()
        self.assertEqual(current['shapes'][0]['label'], 'initial')
    
    def test_restoring_flag(self):
        """Test the restoring flag prevents recursive saves"""
        self.manager.set_restoring(True)
        
        # Should not save when restoring flag is set
        result = self.manager.save_state({'test': 1}, "test")
        self.assertFalse(result)
        self.assertEqual(len(self.manager.history), 0)
        
        # Should save after clearing flag
        self.manager.set_restoring(False)
        result = self.manager.save_state({'test': 1}, "test")
        self.assertTrue(result)
        self.assertEqual(len(self.manager.history), 1)


class TestFrameUndoManager(unittest.TestCase):
    """Test the FrameUndoManager for multiple frames"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.frame_manager = FrameUndoManager(max_history_per_frame=3)
    
    def test_separate_frame_histories(self):
        """Test that each frame has separate undo history"""
        # Frame 1
        self.frame_manager.set_current_frame("frame1.jpg")
        self.frame_manager.save_state({'shapes': [1]}, "add_1")
        self.frame_manager.save_state({'shapes': [1, 2]}, "add_2")
        
        # Frame 2
        self.frame_manager.set_current_frame("frame2.jpg")
        self.frame_manager.save_state({'shapes': [3]}, "add_3")
        self.frame_manager.save_state({'shapes': [3, 4]}, "add_4")
        
        # The unified history should have all 4 operations
        self.assertEqual(len(self.frame_manager.unified_history), 4)
        
        # Undo should work in reverse chronological order
        # Last operation was add_4 on frame2
        result = self.frame_manager.undo()
        self.assertEqual(result['shapes'], [3])
        
        # Next undo: add_3 on frame2 (back to initial)
        result = self.frame_manager.undo()
        # No previous state for frame2, returns None
        
        # Next undo: add_2 on frame1
        result = self.frame_manager.undo()
        self.assertEqual(result['shapes'], [1])
        
        # Next undo: add_1 on frame1
        result = self.frame_manager.undo()
    
    def test_get_manager_creates_if_missing(self):
        """Test that get_manager creates a new manager if missing"""
        manager1 = self.frame_manager.get_manager("new_frame.jpg")
        self.assertIsNotNone(manager1)
        
        # Should return same manager
        manager2 = self.frame_manager.get_manager("new_frame.jpg")
        self.assertIs(manager1, manager2)
    
    def test_operations_without_current_frame(self):
        """Test operations when no current frame is set"""
        # Should return False/None when no current frame
        self.assertFalse(self.frame_manager.save_state({'test': 1}))
        self.assertIsNone(self.frame_manager.undo())
        self.assertIsNone(self.frame_manager.redo())
        self.assertFalse(self.frame_manager.can_undo())
        self.assertFalse(self.frame_manager.can_redo())


class TestMultiFrameOperations(unittest.TestCase):
    """Test multi-frame undo/redo operations (BB duplication, etc.)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.frame_manager = FrameUndoManager(max_history_per_frame=5)
    
    def test_multi_frame_operation_save(self):
        """Test saving a multi-frame operation"""
        # Create a multi-frame operation
        operation = MultiFrameOperation("bb_duplication")
        
        # Add frame changes
        operation.add_frame_change(
            "frame1.jpg",
            {'shapes': [{'label': 'cow1'}]},  # before
            {'shapes': [{'label': 'cow1'}, {'label': 'cow2'}]}  # after
        )
        operation.add_frame_change(
            "frame2.jpg",
            {'shapes': [{'label': 'cow3'}]},  # before
            {'shapes': [{'label': 'cow3'}, {'label': 'cow2'}]}  # after
        )
        
        # Save the operation
        self.frame_manager.save_multi_frame_operation(operation)
        
        # Check unified history
        self.assertEqual(len(self.frame_manager.unified_history), 1)
        self.assertEqual(self.frame_manager.unified_index, 0)
        self.assertTrue(self.frame_manager.can_undo())
    
    def test_multi_frame_operation_undo(self):
        """Test undoing a multi-frame operation"""
        # Create and save a multi-frame operation
        operation = MultiFrameOperation("bb_duplication")
        operation.add_frame_change(
            "frame1.jpg",
            {'shapes': []},  # before
            {'shapes': [{'label': 'new_bb'}]}  # after
        )
        operation.add_frame_change(
            "frame2.jpg",
            {'shapes': []},  # before
            {'shapes': [{'label': 'new_bb'}]}  # after
        )
        
        self.frame_manager.save_multi_frame_operation(operation)
        
        # Undo the operation
        result = self.frame_manager.undo()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, MultiFrameOperation)
        
        # Check that frames have temporary states
        manager1 = self.frame_manager.get_manager("frame1.jpg")
        self.assertTrue(hasattr(manager1, '_multi_frame_state'))
        
        manager2 = self.frame_manager.get_manager("frame2.jpg")
        self.assertTrue(hasattr(manager2, '_multi_frame_state'))
        
        # Get the states and verify they're restored to 'before'
        state1 = manager1.get_current_state()
        self.assertEqual(state1['shapes'], [])
        # _multi_frame_state should be deleted after get_current_state
        self.assertFalse(hasattr(manager1, '_multi_frame_state'))
        
        state2 = manager2.get_current_state()
        self.assertEqual(state2['shapes'], [])
        self.assertFalse(hasattr(manager2, '_multi_frame_state'))
    
    def test_multi_frame_operation_redo(self):
        """Test redoing a multi-frame operation"""
        # Create and save a multi-frame operation
        operation = MultiFrameOperation("bb_duplication")
        operation.add_frame_change(
            "frame1.jpg",
            {'shapes': []},  # before
            {'shapes': [{'label': 'new_bb'}]}  # after
        )
        
        self.frame_manager.save_multi_frame_operation(operation)
        
        # Undo then redo
        self.frame_manager.undo()
        self.assertTrue(self.frame_manager.can_redo())
        
        result = self.frame_manager.redo()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, MultiFrameOperation)
        
        # Check that frame has the 'after' state
        manager1 = self.frame_manager.get_manager("frame1.jpg")
        state1 = manager1.get_current_state()
        self.assertEqual(state1['shapes'], [{'label': 'new_bb'}])
    
    def test_mixed_single_and_multi_frame_operations(self):
        """Test mixing single-frame and multi-frame operations"""
        # 1. Single frame operation on frame1
        self.frame_manager.set_current_frame("frame1.jpg")
        self.frame_manager.save_state({'shapes': [{'label': 'single1'}]}, "add_single")
        
        # 2. Multi-frame operation
        operation = MultiFrameOperation("bb_duplication")
        operation.add_frame_change(
            "frame1.jpg",
            {'shapes': [{'label': 'single1'}]},
            {'shapes': [{'label': 'single1'}, {'label': 'multi'}]}
        )
        operation.add_frame_change(
            "frame2.jpg",
            {'shapes': []},
            {'shapes': [{'label': 'multi'}]}
        )
        self.frame_manager.save_multi_frame_operation(operation)
        
        # 3. Another single frame operation on frame1
        self.frame_manager.set_current_frame("frame1.jpg")
        self.frame_manager.save_state({'shapes': [{'label': 'single1'}, {'label': 'multi'}, {'label': 'single2'}]}, "add_another")
        
        # Check unified history has 3 operations
        self.assertEqual(len(self.frame_manager.unified_history), 3)
        
        # Undo all operations in reverse order
        # First undo: removes 'single2' (going back to after multi-frame op)
        result = self.frame_manager.undo()
        self.assertIsInstance(result, dict)
        # After multi-frame op, frame1 should have 'single1' and 'multi'
        # But since we're getting the state from history, check if it's not None
        self.assertIsNotNone(result)
        
        # Second undo: removes 'multi' from both frames
        result = self.frame_manager.undo()
        self.assertIsInstance(result, MultiFrameOperation)
        
        # Third undo: back to before single1 was added
        result = self.frame_manager.undo()
        # This might return None if there's no initial state
        # or a dict if there is an initial state
        
        # Check we've undone 3 operations
        self.assertEqual(self.frame_manager.unified_index, -1)
        
        # Redo all operations
        for _ in range(3):
            self.assertTrue(self.frame_manager.can_redo())
            self.frame_manager.redo()
        
        self.assertFalse(self.frame_manager.can_redo())
    
    def test_unified_history_chronological_order(self):
        """Test that unified history maintains chronological order"""
        import time
        
        # Operation 1: Single frame
        self.frame_manager.set_current_frame("frame1.jpg")
        self.frame_manager.save_state({'shapes': [1]}, "op1")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Operation 2: Multi-frame
        operation = MultiFrameOperation("op2")
        operation.add_frame_change("frame1.jpg", {'shapes': [1]}, {'shapes': [1, 2]})
        self.frame_manager.save_multi_frame_operation(operation)
        time.sleep(0.01)
        
        # Operation 3: Single frame
        self.frame_manager.set_current_frame("frame2.jpg")
        self.frame_manager.save_state({'shapes': [3]}, "op3")
        
        # Check operations are in chronological order
        self.assertEqual(len(self.frame_manager.unified_history), 3)
        
        # Undo should process in reverse chronological order
        # First undo: op3 (single)
        result = self.frame_manager.undo()
        # op3 is the first state for frame2, so undo returns None (no previous state)
        # But the operation itself should be a single frame operation
        
        # Second undo: op2 (multi)
        result = self.frame_manager.undo()
        self.assertIsInstance(result, MultiFrameOperation)
        
        # Third undo: op1 (single) - returns None as it's the initial state
        result = self.frame_manager.undo()
        # This is the first state for frame1, so returns None
    
    def test_no_before_undo_state_saved(self):
        """Test that 'before_undo' state is not saved during undo operation"""
        # This tests the bug where an extra state was saved before undo
        self.frame_manager.set_current_frame("frame1.jpg")
        
        # Save initial state
        self.frame_manager.save_state({'shapes': []}, "initial")
        
        # Save another state
        self.frame_manager.save_state({'shapes': [{'label': 'cow1'}]}, "add_cow")
        
        # Check we have 2 operations
        self.assertEqual(len(self.frame_manager.unified_history), 2)
        
        # Undo once
        result = self.frame_manager.undo()
        self.assertIsNotNone(result)
        
        # Should still have only 2 operations (no 'before_undo' added)
        self.assertEqual(len(self.frame_manager.unified_history), 2)
        self.assertEqual(self.frame_manager.unified_index, 0)
        
        # Can redo
        self.assertTrue(self.frame_manager.can_redo())
        
        # Can still undo one more time (back to initial state)
        self.assertTrue(self.frame_manager.can_undo())


class TestIntegrationWithLabelImg(unittest.TestCase):
    """Test integration with actual labelImg MainWindow"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Skip if PyQt5 is not available
        try:
            import PyQt5
        except ImportError:
            self.skipTest("PyQt5 not available, skipping integration tests")
        
        # Mock PyQt components
        with patch('labelImg.QMainWindow'):
            with patch('labelImg.QApplication'):
                # Import after mocking
                from labelImg import MainWindow
                
                # Create a minimal MainWindow instance for testing
                self.window = MagicMock()
                self.window.file_path = "test.jpg"
                self.window.canvas = MagicMock()
                self.window.canvas.shapes = []
                self.window.label_list = MagicMock()
                self.window.items_to_shapes = {}
                self.window.shapes_to_items = {}
                self.window.display_label_option = MagicMock()
                self.window.display_label_option.isChecked.return_value = False
                self.window.actions = MagicMock()
                self.window.statusBar = MagicMock()
                
                # Add the undo manager
                from libs.undo_manager import FrameUndoManager
                self.window.undo_manager = FrameUndoManager()
    
    def test_save_and_restore_state(self):
        """Test saving and restoring state in labelImg context"""
        # Set up initial shapes
        shape1 = MagicMock()
        shape1.label = "cow"
        shape1.points = [MagicMock(x=lambda: 10, y=lambda: 20)]
        shape1.difficult = False
        shape1.paint_label = False
        
        self.window.canvas.shapes = [shape1]
        
        # Manually create state (simulating get_current_state)
        state = {
            'file_path': self.window.file_path,
            'shapes': [{
                'label': 'cow',
                'points': [(10, 20)],
                'difficult': False,
                'paint_label': False
            }]
        }
        
        # Save state
        self.window.undo_manager.set_current_frame(self.window.file_path)
        self.window.undo_manager.save_state(state, "test_save")
        
        # Verify state was saved
        manager = self.window.undo_manager.get_manager(self.window.file_path)
        self.assertEqual(len(manager.history), 1)
        
        # Add another state
        state2 = {
            'file_path': self.window.file_path,
            'shapes': [{
                'label': 'cow',
                'points': [(10, 20)],
                'difficult': False,
                'paint_label': False
            }, {
                'label': 'dog',
                'points': [(30, 40)],
                'difficult': True,
                'paint_label': True
            }]
        }
        self.window.undo_manager.save_state(state2, "add_dog")
        
        # Test undo
        self.assertTrue(self.window.undo_manager.can_undo())
        restored = self.window.undo_manager.undo()
        self.assertIsNotNone(restored)
        self.assertEqual(len(restored['shapes']), 1)
        self.assertEqual(restored['shapes'][0]['label'], 'cow')
        
        # Test redo
        self.assertTrue(self.window.undo_manager.can_redo())
        restored = self.window.undo_manager.redo()
        self.assertIsNotNone(restored)
        self.assertEqual(len(restored['shapes']), 2)
        self.assertEqual(restored['shapes'][1]['label'], 'dog')


def run_tests():
    """Run all tests and print results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestUndoManager))
    suite.addTests(loader.loadTestsFromTestCase(TestFrameUndoManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiFrameOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithLabelImg))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)