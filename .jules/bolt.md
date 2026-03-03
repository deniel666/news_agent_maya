## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-12 - Sequential Blocking Database Queries in FastAPI
**Learning:** The `supabase-python` library's `.execute()` methods are synchronous. Making multiple sequential calls to Supabase (like in `get_dashboard_stats` and `get_content_stats`) in a FastAPI `async def` endpoint not only sequentially blocks the current request—inflating latency—but also blocks the entire FastAPI asyncio event loop, causing application-wide performance degradation.
**Action:** Use `asyncio.to_thread()` to offload synchronous `supabase-python` API calls to worker threads, and use `asyncio.gather()` to execute multiple independent queries concurrently.
