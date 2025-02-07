"""
Test Runner Module
==================
This module provides functionality for running unit tests with optional test coverage.

Authors:
--------
- Vincent Lefeuve (vincent.lefeuve.24@imperial.ac.uk)

Functions:
----------
- `run_tests(with_coverage: bool) -> None`:
    Runs all unit tests, optionally measuring test coverage.

- `main()`:
    Parses command-line arguments and executes the test runner accordingly.

Usage:
------
To run all tests:
```shell
python3 run_tests.py
```

To run all tests with coverage:
```shell
python3 run_tests.py --coverage
```
Args:
    with_coverage (bool): If True, runs tests with code coverage analysis.

Behaviour:
    - If `with_coverage` is True, it starts `coverage.py` before running tests.
    - Discovers and runs all unit tests in the `test/` directory.
    - If `with_coverage` is enabled, it generates an **HTML coverage report** in `coverage_html_report/`.

Authors: 
- Vincent Lefeuve (vincent.lefeuve24@imperial.ac.uk)

"""

import sys
import os
import unittest
import argparse
import coverage


def run_tests(with_coverage: bool) -> None:
    """
    Runs unit tests with or without coverage measurement.

    Args:
        with_coverage (bool): If True, runs tests with code coverage analysis.

    Returns:
        None
    """

    if with_coverage:
        cov = coverage.Coverage(
            source=["."]
        )  # Change to ["src"] if your code is in a subfolder
        cov.start()

    # Ensure root directory is in Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Discover and run tests
    testsuite = unittest.TestLoader().discover(
        "test"
    )  # Ensure tests are in /test directory
    unittest.TextTestRunner(verbosity=2).run(testsuite)

    if with_coverage:
        cov.stop()
        cov.save()
        cov.report()
        cov.html_report(directory="coverage_html_report")
        print("\nCoverage HTML report generated in 'coverage_html_report/index.html'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run unit tests with optional coverage."
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Enable test coverage reporting."
    )

    args = parser.parse_args()
    run_tests(args.coverage)
