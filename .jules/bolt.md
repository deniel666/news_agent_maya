## 2026-02-10 - Asyncio Gather Optimization
**Learning:** Sequential HTTP requests in loops are a major performance bottleneck in Python async code. `asyncio.gather` provides massive speedups (observed 2.5x - 3x improvement) for I/O-bound tasks.
**Action:** Always refactor sequential API calls in loops to concurrent tasks using `asyncio.gather`, especially for news aggregation or multi-source fetching.

## 2026-02-10 - Test Data Staleness
**Learning:** Hardcoding dates in tests for time-sensitive logic (like filtering news by age) causes tests to fail silently or explicitly in the future.
**Action:** Always use dynamic dates (e.g., `datetime.utcnow()`) in test data generation to ensure tests remain valid over time.
