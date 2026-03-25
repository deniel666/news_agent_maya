## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-19 - [Editorial Pipeline DB Optimization]
**Learning:** Sequential processing in background jobs with nested DB lookups (e.g. `aggregate_and_store` iterating over multiple RSS feeds and executing `.select().eq()` for each URL to skip duplicates) creates severe N+1 I/O bottlenecks and increases pipeline execution time heavily due to network latency per round trip.
**Action:** Extract list of identifiers (URLs), perform a batched `.select().in_()` query to initialize an O(1) in-memory lookup `set`. Add new items directly to this `set` during loop iteration to correctly deduplicate intra-batch occurrences, and use chunked bulk `.insert()` outside the loop. Use `asyncio.to_thread()` on batch DB calls and parallelize dependent async processes (like AI scoring) using `asyncio.gather(*tasks, return_exceptions=True)`.
