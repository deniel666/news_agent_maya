## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-09 - Async Event Loop Blocking in Aggregators
**Learning:** `feedparser.parse` and `BeautifulSoup` are synchronous and CPU-bound. Running them directly inside `async` functions blocks the event loop, preventing concurrent I/O operations from progressing efficiently.
**Action:** Offload CPU-bound parsing logic to a thread pool using `loop.run_in_executor`.
