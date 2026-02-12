## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-23 - Blocking CPU in Async Loop
**Learning:** The `NewsAggregatorService` was parsing large XML feeds and cleaning HTML (`feedparser` + `BeautifulSoup`) directly in the async event loop. This blocks the loop, causing latency spikes for all concurrent tasks, negating the benefits of `asyncio`.
**Action:** Offload CPU-intensive parsing and data processing (like XML/HTML parsing) to a thread pool using `loop.run_in_executor`.
