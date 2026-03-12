## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2025-02-28 - Parallelize Synchronous Database Calls
**Learning:** The Supabase Python client's `.execute()` method is fundamentally synchronous and blocking. Because the underlying network calls block the thread, running multiple independent queries sequentially results in cumulative wait times (e.g., waiting for query A, then query B, then query C). Attempting to use Python's standard `async` keywords around `.execute()` doesn't prevent thread blocking.
**Action:** When making multiple independent queries to Supabase within an async context (such as FastAPI endpoints or background tasks), wrap the synchronous `.execute()` calls using `asyncio.to_thread` and execute them concurrently using `asyncio.gather`. This offloads the blocking I/O to a thread pool, allowing the event loop to proceed, and reduces the total latency of the operation to the duration of the single slowest query, rather than the sum of all queries.
