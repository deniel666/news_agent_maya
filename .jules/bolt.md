## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-02-09 - N+1 Query in Editorial Pipeline
**Learning:** The `EditorialPipelineService` was fetching duplicate check queries one by one for each aggregated article via `supabase.table("raw_stories").select("id").eq("original_url", article.url)`. This results in an N+1 query problem, severely slowing down aggregation. Additionally, batching Supabase queries using `.in_` can hit URI length limits since it uses GET requests.
**Action:** Pre-fetch existing entries in chunks (e.g. 50 items per batch) using `.in_()` to bring the operation from O(N) database calls down to O(N/batch_size) calls. Store the fetched existing identifiers in a local Python `set` for O(1) duplicate lookups in the loop.
