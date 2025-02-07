import sys
import os
import unittest
import argparse
import coverage

def run_tests(with_coverage):
    """Runs unit tests with or without coverage measurement."""
    
    if with_coverage:
        cov = coverage.Coverage(source=["."])  # Change to ["src"] if your code is in a subfolder
        cov.start()
    
    # Ensure root directory is in Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Discover and run tests
    testsuite = unittest.TestLoader().discover('test')  # Ensure tests are in /test directory
    unittest.TextTestRunner(verbosity=2).run(testsuite)

    if with_coverage:
        cov.stop()
        cov.save()
        cov.report()
        cov.html_report(directory="coverage_html_report")
        print("\nCoverage HTML report generated in 'coverage_html_report/index.html'")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run unit tests with optional coverage.")
    parser.add_argument('--coverage', action='store_true', help="Enable test coverage reporting.")

    args = parser.parse_args()
    run_tests(args.coverage)
