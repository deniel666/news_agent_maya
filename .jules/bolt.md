## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-24 - ThreadPoolExecutor vs ProcessPoolExecutor for XML Parsing
**Learning:** Offloading `feedparser` and `BeautifulSoup` tasks to `asyncio.to_thread` (ThreadPoolExecutor) resulted in slower performance (2.4s vs 1.4s serial) due to GIL contention. Switching to `ProcessPoolExecutor` yielded a 3x speedup (0.5s).
**Action:** Prefer `ProcessPoolExecutor` over `asyncio.to_thread` for CPU-bound XML/HTML parsing tasks involving `feedparser` or `BeautifulSoup`.
