#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite for Command base class
TDD approach - write tests first, then implementation
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# These imports will fail initially (TDD - Red phase)
# from libs.undo.command import Command
# from libs.undo.commands.composite_command import CompositeCommand


class TestCommandBase(unittest.TestCase):
    """Test the Command base class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        self.app.canvas = Mock()
        self.app.canvas.shapes = []
        
    def test_command_abstract_methods(self):
        """Test that Command is abstract and requires implementation"""
        # This will fail initially - Command class doesn't exist yet
        try:
            from libs.undo.command import Command
            
            # Should not be able to instantiate abstract class
            with self.assertRaises(TypeError):
                cmd = Command()
                
        except ImportError:
            self.skipTest("Command class not implemented yet")
    
    def test_command_execute_method(self):
        """Test that Command has execute method"""
        try:
            from libs.undo.command import Command
            
            class TestCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Test command"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            cmd = TestCommand()
            self.assertTrue(cmd.execute(self.app))
            
        except ImportError:
            self.skipTest("Command class not implemented yet")
    
    def test_command_undo_method(self):
        """Test that Command has undo method"""
        try:
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
                    return "Test command"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            cmd = TestCommand()
            cmd.execute(self.app)
            self.assertTrue(cmd.executed)
            
            cmd.undo(self.app)
            self.assertFalse(cmd.executed)
            
        except ImportError:
            self.skipTest("Command class not implemented yet")
    
    def test_command_description_property(self):
        """Test that Command has description property"""
        try:
            from libs.undo.command import Command
            
            class TestCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Test operation"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            cmd = TestCommand()
            self.assertEqual(cmd.description, "Test operation")
            
        except ImportError:
            self.skipTest("Command class not implemented yet")
    
    def test_command_merge_capability(self):
        """Test command merging functionality"""
        try:
            from libs.undo.command import Command
            
            class MergableCommand(Command):
                def __init__(self, value):
                    super().__init__()
                    self.value = value
                
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return f"Value: {self.value}"
                
                def can_merge_with(self, other):
                    return isinstance(other, MergableCommand)
                
                def merge(self, other):
                    return MergableCommand(self.value + other.value)
                
                @property
                def affects_save_state(self):
                    return True
            
            cmd1 = MergableCommand(10)
            cmd2 = MergableCommand(20)
            
            self.assertTrue(cmd1.can_merge_with(cmd2))
            merged = cmd1.merge(cmd2)
            self.assertEqual(merged.value, 30)
            
        except ImportError:
            self.skipTest("Command class not implemented yet")
    
    def test_command_affects_save_state(self):
        """Test affects_save_state property"""
        try:
            from libs.undo.command import Command
            
            class SaveStateCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Save state command"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            class NoSaveStateCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "No save state command"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return False
            
            save_cmd = SaveStateCommand()
            no_save_cmd = NoSaveStateCommand()
            
            self.assertTrue(save_cmd.affects_save_state)
            self.assertFalse(no_save_cmd.affects_save_state)
            
        except ImportError:
            self.skipTest("Command class not implemented yet")


class TestCompositeCommand(unittest.TestCase):
    """Test CompositeCommand for handling multiple operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.file_path = "test_frame.png"
        
    def test_composite_command_creation(self):
        """Test creating a composite command"""
        try:
            from libs.undo.commands.composite_command import CompositeCommand
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def __init__(self, name):
                    super().__init__()
                    self.name = name
                    self.executed = False
                
                def execute(self, app):
                    self.executed = True
                    return True
                
                def undo(self, app):
                    self.executed = False
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
            
            cmd1 = SimpleCommand("Command 1")
            cmd2 = SimpleCommand("Command 2")
            cmd3 = SimpleCommand("Command 3")
            
            composite = CompositeCommand([cmd1, cmd2, cmd3])
            self.assertEqual(len(composite.commands), 3)
            
        except ImportError:
            self.skipTest("CompositeCommand not implemented yet")
    
    def test_composite_command_execute(self):
        """Test executing all commands in composite"""
        try:
            from libs.undo.commands.composite_command import CompositeCommand
            from libs.undo.command import Command
            
            executed_order = []
            
            class TrackingCommand(Command):
                def __init__(self, id):
                    super().__init__()
                    self.id = id
                
                def execute(self, app):
                    executed_order.append(f"exec_{self.id}")
                    return True
                
                def undo(self, app):
                    executed_order.append(f"undo_{self.id}")
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
            
            commands = [TrackingCommand(i) for i in range(3)]
            composite = CompositeCommand(commands)
            
            result = composite.execute(self.app)
            self.assertTrue(result)
            self.assertEqual(executed_order, ["exec_0", "exec_1", "exec_2"])
            
        except ImportError:
            self.skipTest("CompositeCommand not implemented yet")
    
    def test_composite_command_undo(self):
        """Test undoing commands in reverse order"""
        try:
            from libs.undo.commands.composite_command import CompositeCommand
            from libs.undo.command import Command
            
            undo_order = []
            
            class TrackingCommand(Command):
                def __init__(self, id):
                    super().__init__()
                    self.id = id
                
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    undo_order.append(f"undo_{self.id}")
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
            
            commands = [TrackingCommand(i) for i in range(3)]
            composite = CompositeCommand(commands)
            
            composite.execute(self.app)
            composite.undo(self.app)
            
            # Should undo in reverse order
            self.assertEqual(undo_order, ["undo_2", "undo_1", "undo_0"])
            
        except ImportError:
            self.skipTest("CompositeCommand not implemented yet")
    
    def test_composite_command_partial_failure(self):
        """Test rollback when one command fails"""
        try:
            from libs.undo.commands.composite_command import CompositeCommand
            from libs.undo.command import Command
            
            class SuccessCommand(Command):
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
                    return "Success"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            class FailCommand(Command):
                def execute(self, app):
                    return False  # Fails
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Fail"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            cmd1 = SuccessCommand()
            cmd2 = SuccessCommand()
            cmd3 = FailCommand()  # This will fail
            cmd4 = SuccessCommand()
            
            composite = CompositeCommand([cmd1, cmd2, cmd3, cmd4])
            result = composite.execute(self.app)
            
            self.assertFalse(result)
            # First two should be rolled back
            self.assertFalse(cmd1.executed)
            self.assertFalse(cmd2.executed)
            
        except ImportError:
            self.skipTest("CompositeCommand not implemented yet")
    
    def test_composite_command_description(self):
        """Test composite command description"""
        try:
            from libs.undo.commands.composite_command import CompositeCommand
            from libs.undo.command import Command
            
            class SimpleCommand(Command):
                def execute(self, app):
                    return True
                
                def undo(self, app):
                    return True
                
                @property
                def description(self):
                    return "Simple"
                
                def can_merge_with(self, other):
                    return False
                
                def merge(self, other):
                    raise NotImplementedError
                
                @property
                def affects_save_state(self):
                    return True
            
            commands = [SimpleCommand() for _ in range(3)]
            composite = CompositeCommand(commands, "Batch operation")
            
            self.assertEqual(composite.description, "Batch operation")
            
            # Test default description
            composite2 = CompositeCommand(commands)
            self.assertIn("Composite", composite2.description)
            
        except ImportError:
            self.skipTest("CompositeCommand not implemented yet")


if __name__ == '__main__':
    unittest.main()