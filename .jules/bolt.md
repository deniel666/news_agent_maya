## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-09 - Blocking CPU in Async Aggregators
**Learning:** `feedparser.parse` and `BeautifulSoup` parsing are CPU-bound operations. When executed directly in an async loop, they block the event loop, negating the benefits of concurrency for other pending I/O tasks.
**Action:** Use `asyncio.to_thread` to offload CPU-intensive parsing to a separate thread, keeping the event loop free for network I/O.
