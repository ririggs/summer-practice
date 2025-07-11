#!/usr/bin/env python3
import unittest
import sys

if __name__ == '__main__':
    test_suite = unittest.defaultTestLoader.discover('.', pattern='test_*.py')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    sys.exit(not result.wasSuccessful()) 