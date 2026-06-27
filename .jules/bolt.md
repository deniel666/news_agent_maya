## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-09 - Supabase Upsert Race Conditions
**Learning:** Attempting to optimize N+1 updates of heterogeneous data via Supabase `.upsert()` using a read-modify-write pattern inside a background task introduces a severe race condition. It silently overwrites any user edits made while the task was running with stale data, and triggers PostgreSQL constraint violations if the initial read didn't fetch all `NOT NULL` columns.
**Action:** When performing bulk database operations involving varying data in a background task, avoid `.upsert()` unless the payload acts as a strict insert or is guaranteed to be fully complete. For identical batch updates, chunked `.in_()` remains the safest and most efficient approach.
