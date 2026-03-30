## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-13 - Parallel Independent Synchronous DB Queries
**Learning:** Sequential synchronous database queries (like Supabase `.execute()` without async await natively) inside aggregator functions create unnecessary I/O blocking bottlenecks. Waiting for sequential responses wastes idle time.
**Action:** Always wrap independent synchronous queries using `asyncio.to_thread` and await them concurrently using `asyncio.gather`.
