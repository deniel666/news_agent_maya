## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2025-04-20 - Search Input Debounce
**Learning:** `searchQuery` state variables used directly as query parameters in Tanstack `useQuery` without debouncing can trigger excessive API calls while typing, impacting performance and backend stability.
**Action:** Implement and use a `useDebounce` hook for state variables tied to input fields before passing them into query dependencies.
