"""Standalone test runner for migration tests (bypasses FastAPI app fixtures)."""

import subprocess
import sys
from pathlib import Path


def run_migration_tests():
    """Run migration tests with minimal fixtures."""
    test_dir = Path(__file__).parent

    # Run tests with minimal fixtures
    test_files = [
        "test_migration_0b4b33664011_fresh.py",
        "test_migration_0b4b33664011_existing.py",
        "test_migration_0b4b33664011_rollback.py",
    ]

    results = {}
    for test_file in test_files:
        print(f"\n{'='*80}")
        print(f"Running {test_file}")
        print("="*80)

        result = subprocess.run(
            [
                "uv",
                "run",
                "pytest",
                str(test_dir / test_file),
                "-v",
                "--tb=short",
                "-p",
                "no:warnings",
                "--override-ini=asyncio_default_fixture_loop_scope=function",
            ],
            capture_output=False,
            text=True, check=False,
        )

        results[test_file] = result.returncode

    return results


if __name__ == "__main__":
    results = run_migration_tests()

    print(f"\n{'='*80}")
    print("Test Summary")
    print("="*80)
    for test_file, returncode in results.items():
        status = "PASSED" if returncode == 0 else "FAILED"
        print(f"{test_file}: {status}")

    # Exit with non-zero if any tests failed
    if any(code != 0 for code in results.values()):
        sys.exit(1)
