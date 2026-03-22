## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-12 - N+1 Query Anti-Pattern in Editorial Pipeline
**Learning:** `EditorialPipelineService.aggregate_and_store` had a classic N+1 query anti-pattern inside an async loop. Calling synchronous Supabase commands like `.select().execute()` sequentially blocked the event loop.
**Action:** Extract identifiers, use batched `.in_()` queries, and wrap the blocking Supabase operations in `asyncio.to_thread` for concurrent execution. Always bulk `.insert()` to reduce network latency.
