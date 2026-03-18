## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2025-02-14 - N+1 database queries in array processing
**Learning:** `EditorialPipelineService.aggregate_and_store` had an N+1 query problem, fetching the database to `.select()` and check if each item existed sequentially in a loop before individually calling `.insert()`. This is highly inefficient.
**Action:** When saving an array of items with presence checks, extract all identifiers (e.g. URLs), do one single batched `.in_()` read, deduplicate locally with a O(1) membership check using a `set`, and then perform a single bulk `.insert()` offloaded to `asyncio.to_thread`.
