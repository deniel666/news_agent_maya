## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-10 - CPU Blocking in Async Tasks
**Learning:** Even with `asyncio.gather` for I/O, heavy CPU-bound tasks like `feedparser.parse` and `BeautifulSoup` cleaning inside the async loop block the event loop, causing latency spikes and timeouts in other concurrent tasks.
**Action:** Offload CPU-intensive parsing to `asyncio.to_thread` to keep the event loop responsive.
