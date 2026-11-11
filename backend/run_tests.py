"""
PharmaMind AI - Automated Test Runner
Runs all unit and integration test suites.
"""

import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

for p in [BASE_DIR, PARENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover and add all tests from unit and integration
    unit_suite = loader.discover(
        start_dir=os.path.join(BASE_DIR, "tests", "unit"),
        pattern="test_*.py",
        top_level_dir=BASE_DIR
    )
    integration_suite = loader.discover(
        start_dir=os.path.join(BASE_DIR, "tests", "integration"),
        pattern="test_*.py",
        top_level_dir=BASE_DIR
    )

    suite.addTests(unit_suite)
    suite.addTests(integration_suite)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
