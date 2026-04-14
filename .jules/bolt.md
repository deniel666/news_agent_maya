## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-10 - Synchronous DB calls in Async Methods
**Learning:** The Supabase Python client `execute()` method is synchronous. When aggregating data across multiple tables (e.g., `get_dashboard_stats`), running these calls sequentially inside an `async def` blocks the main event loop and scales linearly with the number of queries.
**Action:** Always wrap independent synchronous Supabase DB calls in `asyncio.to_thread()` and await them concurrently using `asyncio.gather()` to maximize parallel I/O and unblock the event loop.
