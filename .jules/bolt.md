## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-28 - N+1 I/O Blocking in Editorial Pipeline
**Learning:** The `EditorialPipelineService.aggregate_and_store` function was iterating through fetched articles, performing a synchronous Supabase `.select()` and `.insert()` for each article. Because the supabase-python client is synchronous, this caused severe N+1 blocking I/O on the main event loop, significantly slowing down the pipeline execution.
**Action:** Extract unique keys (URLs), use a single bulk `.in_()` query to fetch existing records, filter duplicates linearly in memory using a `set`, and then perform a single bulk `.insert()` of all new records. Always wrap synchronous blocking db calls in `asyncio.to_thread` to avoid freezing the event loop.
