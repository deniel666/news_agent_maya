## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-09 - N+1 Queries with Synchronous Database Inserts
**Learning:** Sequential synchronous database checks and inserts inside a loop block the event loop heavily. Utilizing an N+1 approach for database existence checks (e.g., checking URLs one by one) and inserting records iteratively is a major bottleneck, especially as the data batch size scales.
**Action:** When inserting large batches, extract unique identifiers and execute a single batched `.in_()` query to find existing records. Keep an in-memory set to detect duplicates within the loop, add new elements to a batch list, and perform a single `.insert(batch)` at the end. Wrap both the `.in_()` read and bulk `.insert()` in `asyncio.to_thread` for synchronous DB drivers to keep the event loop non-blocking.