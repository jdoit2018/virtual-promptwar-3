"""
apps/api/tests/run_all.py
Unified test runner to execute all integration tests sequentially in a single process.
This ensures code coverage is tracked perfectly without file combination issues.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.phase2_test import run_all_tests as run_2
from tests.phase4_test import run_all_tests as run_4
from tests.edge_cases_test import run_edge_cases as run_edge
from tests.coverage_test import run_coverage_tests

async def main():
    print("Starting unified test runner...")
    await run_2()
    await run_4()
    await run_edge()
    await run_coverage_tests()
    print("All test suites completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
