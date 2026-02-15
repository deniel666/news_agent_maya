## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-27 - CPU-Bound Tasks in AsyncIO
**Learning:** `feedparser.parse` and `BeautifulSoup` are CPU-bound and block the asyncio event loop. Offloading `feedparser.parse` to `asyncio.to_thread` significantly improves concurrency. However, offloading lightweight tasks (like `_clean_html`) inside a loop introduces thread overhead that negates benefits.
**Action:** Offload only heavy CPU tasks (like parsing entire feeds) to threads; keep lightweight string processing synchronous or batch it.
