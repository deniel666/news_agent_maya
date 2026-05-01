## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-01 - Debouncing React Query State
**Learning:** Passing rapidly changing state variables (like search inputs) directly to Tanstack `useQuery` causes excessive API calls, as each keystroke triggers a refetch.
**Action:** Always debounce state variables tied to input fields before passing them as dependencies to `useQuery` to reduce unnecessary network requests and server load.
