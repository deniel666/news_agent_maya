## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-09 - N+1 Queries in Editorial Pipeline
**Learning:** The `aggregate_and_store` function in `EditorialPipelineService` was performing individual `supabase.table("raw_stories").select().eq().execute()` and `.insert().execute()` calls inside a loop over articles. This blocked the event loop and scaled linearly with the number of articles.
**Action:** When inserting collections in the backend, extract identifiers (e.g. URLs), perform a single batched `.in_()` read wrapped in `asyncio.to_thread()`, deduplicate in memory, and perform a single bulk `.insert()` via `asyncio.to_thread()`. Always use `asyncio.gather` with `return_exceptions=True` when concurrently processing side effects like scoring.