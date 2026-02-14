## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-14 - Blocking CPU Operations in Async Loop
**Learning:** `feedparser.parse` and `BeautifulSoup` operations are CPU-intensive and blocking. Running them directly in an async function blocks the event loop, degrading performance for all concurrent tasks.
**Action:** Offload CPU-bound parsing to a thread pool using `asyncio.to_thread` (or `loop.run_in_executor`) to keep the event loop responsive.
