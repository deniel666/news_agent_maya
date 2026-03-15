## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-03-15 - Batched DB Writes in Aggregator
**Learning:** Sequential database operations (`select` and `insert`) within a loop inside `aggregate_and_store` created an O(N) blocking network I/O bottleneck. The Supabase Python client is synchronous, making the issue worse.
**Action:** Always use batch queries (`in_`), bulk inserts (`insert` with lists), and run concurrent tasks using `asyncio.gather(..., return_exceptions=True)` paired with `asyncio.to_thread` for DB updates to optimize loop bottlenecks.
