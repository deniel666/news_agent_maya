## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2025-02-28 - Blocking Supabase Queries
**Learning:** The `supabase-python` client methods (e.g., `.execute()`) are synchronous and blocking. Because they were being called directly in async service methods, they blocked the FastAPI event loop, and consecutive independent queries were running sequentially rather than concurrently.
**Action:** Use `asyncio.to_thread` to offload blocking Supabase calls to a thread pool, and parallelize independent queries using `asyncio.gather`.
