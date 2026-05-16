## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2023-10-24 - Bulk Supabase Updates
**Learning:** Using `.update().eq()` in a loop creates an N+1 bottleneck for network requests.
**Action:** For Supabase bulk updates, use chunked `.upsert()` payloads (batches of 50) instead.
