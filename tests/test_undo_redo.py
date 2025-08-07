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

from libs.undo_manager import UndoManager, FrameUndoManager


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
        
        # Check frame 1 can undo
        self.frame_manager.set_current_frame("frame1.jpg")
        self.assertTrue(self.frame_manager.can_undo())
        result = self.frame_manager.undo()
        self.assertEqual(result['shapes'], [1])
        
        # Check frame 2 is unaffected
        self.frame_manager.set_current_frame("frame2.jpg")
        self.assertTrue(self.frame_manager.can_undo())
        result = self.frame_manager.undo()
        self.assertEqual(result['shapes'], [3])
    
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


class TestIntegrationWithLabelImg(unittest.TestCase):
    """Test integration with actual labelImg MainWindow"""
    
    def setUp(self):
        """Set up test fixtures"""
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