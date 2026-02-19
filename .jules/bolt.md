## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-09 - Blocking CPU Tasks in AsyncIO Loop
**Learning:** `feedparser.parse` and `BeautifulSoup` are CPU-bound operations that can block the main asyncio event loop, causing latency spikes even when using `asyncio.gather`.
**Action:** Offload CPU-intensive parsing to a thread pool using `asyncio.to_thread` to keep the event loop responsive.
