## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-18 - Concurrent aggregate queries for Dashboard Stats
**Learning:** The `get_content_stats` method in `DatabaseService` is used to build the dashboard overview. It previously made 5 separate, sequential round-trip queries to Supabase to fetch total counts across different tables (`stories`, `video_assets`, `publish_records`). This results in O(N) network latency for each new metric added.
**Action:** Use `asyncio.to_thread` wrapped around synchronous `supabase-python` queries and await them concurrently using `asyncio.gather`. This reduces network latency from `O(N)` queries to `O(1)` (bound by the single slowest query).
