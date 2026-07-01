from __future__ import annotations

import pathlib
import unittest


def run_all_tests() -> unittest.result.TestResult:
    tests_dir = pathlib.Path(__file__).parent
    suite = unittest.defaultTestLoader.discover(start_dir=str(tests_dir), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    result = run_all_tests()
    raise SystemExit(0 if result.wasSuccessful() else 1)
