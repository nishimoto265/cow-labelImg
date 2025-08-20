#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for UndoManager
TDD approach - write tests first, then implementation
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestUndoManager(unittest.TestCase):
    """Test UndoManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.actions = Mock()
        self.app.actions.undo = Mock()
        self.app.actions.redo = Mock()
        self.app.actions.undo.setEnabled = Mock()
        self.app.actions.redo.setEnabled = Mock()
    
    def test_undo_manager_creation(self):
        """Test creating UndoManager"""
        try:
            from libs.undo.manager import UndoManager
            
            manager = UndoManager(self.app, max_history=50)
            self.assertEqual(manager.app, self.app)
            self.assertEqual(manager.max_history, 50)
            self.assertEqual(manager.current_index, -1)
            self.assertEqual(len(manager.history), 0)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_execute_command(self):
        """Test executing a command"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class TestCommand(Command):
                def __init__(self):
                    super().__init__()
                    self.executed = False
                
                def execute(self, app):
                    self.executed = True
                    return True
                
                def undo(self, app):
                    self.executed = False
                    return True
                
                @property
                def description(self):
                    return "Test"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            cmd = TestCommand()
            
            result = manager.execute_command(cmd)
            
            self.assertTrue(result)
            self.assertTrue(cmd.executed)
            self.assertEqual(len(manager.history), 1)
            self.assertEqual(manager.current_index, 0)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_undo_single_command(self):
        """Test undoing a single command"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class TestCommand(Command):
                def __init__(self):
                    super().__init__()
                    self.value = 0
                
                def execute(self, app):
                    self.value = 1
                    return True
                
                def undo(self, app):
                    self.value = 0
                    return True
                
                @property
                def description(self):
                    return "Test"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            cmd = TestCommand()
            
            manager.execute_command(cmd)
            self.assertEqual(cmd.value, 1)
            
            result = manager.undo()
            
            self.assertTrue(result)
            self.assertEqual(cmd.value, 0)
            self.assertEqual(manager.current_index, -1)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_redo_single_command(self):
        """Test redoing a single command"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class TestCommand(Command):
                def __init__(self):
                    super().__init__()
                    self.value = 0
                
                def execute(self, app):
                    self.value += 1
                    return True
                
                def undo(self, app):
                    self.value -= 1
                    return True
                
                @property
                def description(self):
                    return "Test"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            cmd = TestCommand()
            
            manager.execute_command(cmd)
            self.assertEqual(cmd.value, 1)
            
            manager.undo()
            self.assertEqual(cmd.value, 0)
            
            result = manager.redo()
            
            self.assertTrue(result)
            self.assertEqual(cmd.value, 1)
            self.assertEqual(manager.current_index, 0)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_undo_redo_multiple_commands(self):
        """Test undo/redo with multiple commands"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            values = []
            
            class AppendCommand(Command):
                def __init__(self, value):
                    super().__init__()
                    self.value = value
                
                def execute(self, app):
                    values.append(self.value)
                    return True
                
                def undo(self, app):
                    values.remove(self.value)
                    return True
                
                @property
                def description(self):
                    return f"Append {self.value}"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            
            # Execute 3 commands
            manager.execute_command(AppendCommand(1))
            manager.execute_command(AppendCommand(2))
            manager.execute_command(AppendCommand(3))
            
            self.assertEqual(values, [1, 2, 3])
            
            # Undo all
            manager.undo()
            self.assertEqual(values, [1, 2])
            manager.undo()
            self.assertEqual(values, [1])
            manager.undo()
            self.assertEqual(values, [])
            
            # Redo all
            manager.redo()
            self.assertEqual(values, [1])
            manager.redo()
            self.assertEqual(values, [1, 2])
            manager.redo()
            self.assertEqual(values, [1, 2, 3])
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_history_truncation_after_new_command(self):
        """Test that history is truncated after executing new command following undo"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def __init__(self, name):
                    super().__init__()
                    self.name = name
                
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return self.name
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            
            # Execute commands
            manager.execute_command(SimpleCommand("A"))
            manager.execute_command(SimpleCommand("B"))
            manager.execute_command(SimpleCommand("C"))
            
            # Undo twice
            manager.undo()  # Undo C
            manager.undo()  # Undo B
            
            # Execute new command
            manager.execute_command(SimpleCommand("D"))
            
            # History should be [A, D], C and B should be removed
            self.assertEqual(len(manager.history), 2)
            self.assertEqual(manager.history[0].name, "A")
            self.assertEqual(manager.history[1].name, "D")
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_max_history_limit(self):
        """Test that history respects maximum size limit"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def __init__(self, id):
                    super().__init__()
                    self.id = id
                
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return f"Command {self.id}"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app, max_history=5)
            
            # Execute 10 commands
            for i in range(10):
                manager.execute_command(SimpleCommand(i))
            
            # Should only keep last 5
            self.assertEqual(len(manager.history), 5)
            self.assertEqual(manager.history[0].id, 5)
            self.assertEqual(manager.history[4].id, 9)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_can_undo_can_redo(self):
        """Test can_undo and can_redo methods"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Test"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            
            # Initially cannot undo or redo
            self.assertFalse(manager.can_undo())
            self.assertFalse(manager.can_redo())
            
            # After executing command, can undo but not redo
            manager.execute_command(SimpleCommand())
            self.assertTrue(manager.can_undo())
            self.assertFalse(manager.can_redo())
            
            # After undo, cannot undo but can redo
            manager.undo()
            self.assertFalse(manager.can_undo())
            self.assertTrue(manager.can_redo())
            
            # After redo, can undo but not redo
            manager.redo()
            self.assertTrue(manager.can_undo())
            self.assertFalse(manager.can_redo())
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_command_merging(self):
        """Test command merging functionality"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class MergableCommand(Command):
                def __init__(self, value):
                    super().__init__()
                    self.value = value
                    self.sum = value
                
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return f"Value {self.value}"
                
                def can_merge_with(self, other):
                    return isinstance(other, MergableCommand)
                
                def merge(self, other):
                    merged = MergableCommand(self.value)
                    merged.sum = self.sum + other.value
                    return merged
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            manager.merge_timeout = 1000  # 1 second
            
            # Execute first command
            cmd1 = MergableCommand(10)
            manager.execute_command(cmd1)
            
            # Execute second command quickly (should merge)
            time.sleep(0.1)
            cmd2 = MergableCommand(20)
            manager.execute_command(cmd2)
            
            # Should have merged into single command
            self.assertEqual(len(manager.history), 1)
            self.assertEqual(manager.history[0].sum, 30)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_ui_update(self):
        """Test that UI is updated after undo/redo"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Test"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            
            # Execute command
            manager.execute_command(SimpleCommand())
            
            # Check UI updated
            self.app.actions.undo.setEnabled.assert_called_with(True)
            self.app.actions.redo.setEnabled.assert_called_with(False)
            
            # Undo
            manager.undo()
            
            # Check UI updated
            self.app.actions.undo.setEnabled.assert_called_with(False)
            self.app.actions.redo.setEnabled.assert_called_with(True)
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")
    
    def test_clear_history(self):
        """Test clearing history"""
        try:
            from libs.undo.manager import UndoManager
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Test"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            manager = UndoManager(self.app)
            
            # Add some commands
            manager.execute_command(SimpleCommand())
            manager.execute_command(SimpleCommand())
            
            self.assertEqual(len(manager.history), 2)
            
            # Clear history
            manager.clear()
            
            self.assertEqual(len(manager.history), 0)
            self.assertEqual(manager.current_index, -1)
            self.assertFalse(manager.can_undo())
            self.assertFalse(manager.can_redo())
            
        except ImportError:
            self.skipTest("UndoManager not implemented yet")


if __name__ == '__main__':
    unittest.main()