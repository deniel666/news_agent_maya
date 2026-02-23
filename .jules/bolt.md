## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-12 - Blocking Supabase Calls in Async Methods
**Learning:** The `DatabaseService` methods were defined as `async` but used the synchronous `supabase-python` client (`.execute()` blocks). This blocked the event loop. Furthermore, independent queries in `get_content_stats` were running sequentially.
**Action:** Use `asyncio.to_thread` to offload blocking DB calls and `asyncio.gather` to run independent queries in parallel.
