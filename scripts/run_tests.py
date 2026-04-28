#!/usr/bin/env python3
"""
Test runner script for the multi-agent system
"""

import unittest
import sys
import os

def run_all_tests():
    """Run all test suites"""
    # Add the project root to the path
    project_root = os.path.dirname(os.path.abspath(__file__)) + "/.."
    sys.path.insert(0, project_root)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    
    # Load all test modules
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_memory_tests():
    """Run memory system tests specifically"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_memory_systems')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_production_tests():
    """Run production readiness tests specifically"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_production_readiness')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "memory":
            success = run_memory_tests()
        elif test_type == "production":
            success = run_production_tests()
        else:
            print("Usage: python run_tests.py [memory|production]")
            sys.exit(1)
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)