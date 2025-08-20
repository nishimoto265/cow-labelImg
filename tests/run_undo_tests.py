#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run all undo/redo tests and report results
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    """Run all undo/redo tests"""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test modules
    test_modules = [
        'test_undo_command_base',
        'test_undo_manager',
        'test_undo_shape_commands',
        'test_undo_label_commands'
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
            print(f"[OK] Loaded tests from {module_name}")
        except Exception as e:
            print(f"[ERROR] Failed to load {module_name}: {e}")
    
    # Run tests
    print("\n" + "="*60)
    print("Running Undo/Redo System Tests")
    print("="*60 + "\n")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[FAILURE] Some tests failed")
        
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)