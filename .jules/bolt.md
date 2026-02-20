## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-17 - CPU-bound operations in Async Loop
**Learning:** `feedparser.parse` and `BeautifulSoup` parsing are CPU-intensive and synchronous. When called directly within an async function, they block the event loop, causing jitter and unresponsiveness even if the network calls are async.
**Action:** Offload CPU-bound parsing tasks to a thread pool using `asyncio.to_thread` to keep the event loop non-blocking.
