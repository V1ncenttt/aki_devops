import sys
import os
import unittest

# Get the root directory (parent of the /test folder)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import controller  # Now you can import your root modules

if __name__ == '__main__':
    testsuite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner(verbosity=2).run(testsuite)
