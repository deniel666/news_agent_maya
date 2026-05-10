## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-02-09 - N+1 Queries in Editorial Pipeline
**Learning:** Sequential processing arrays of scraped objects to deduplicate them via single `select()` queries and insert via single `insert()` calls causes severe I/O bottlenecks in data aggregation scripts. Furthermore, Supabase POSTGREST `.in_()` operations can crash if the value array is too long.
**Action:** Extract unique keys, chunk them (e.g. 50 items per chunk), and perform batched `select().in_()` checks. Follow this with chunked batch `insert()` operations and `asyncio.gather` for downstream concurrent processing (e.g. AI scoring).
