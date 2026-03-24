## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-03-24 - N+1 I/O Blocking in Supabase Ingestion Pipelines
**Learning:** The `EditorialPipelineService` was exhibiting classic N+1 I/O blocking during ingestion: sequentially executing `.select().eq().execute()` inside a for-loop to check for duplicate original URLs, and sequentially inserting individual stories with `.insert().execute()`. Since `supabase-py` wraps synchronous REST API calls by default, this blocked the entire pipeline thread for each article.
**Action:** When ingesting batch data, always extract identifiers to perform a single batched `.in_()` read, deduplicate by tracking the items in a `set` (which also catches intra-batch duplicates), and perform a single bulk `.insert()`. Ensure synchronous Supabase calls are wrapped in `asyncio.to_thread()` to prevent event loop blocking.
