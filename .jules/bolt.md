## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2024-06-01 - Debouncing Frontend Search Inputs Tied to API
**Learning:** Directly binding a fast-changing state value (like search inputs) to Tanstack `useQuery` dependencies causes an API call and component re-render on every keystroke, which is a significant performance bottleneck.
**Action:** Always use a debounced state value for API-bound dependencies on the frontend.
