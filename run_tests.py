#!/usr/bin/env python3
"""
Test runner for commission reconciliation tool
"""
import unittest
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """Run all tests and display results"""
    # Discover and run tests
    loader = unittest.TestLoader()
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    print("=" * 70)
    print("Commission Reconciliation Tool - Test Suite")
    print("=" * 70)
    print()
    
    exit_code = run_all_tests()
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        
    sys.exit(exit_code)