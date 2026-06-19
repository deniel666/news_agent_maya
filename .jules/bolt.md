## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-18 - Un-debounced Search Queries
**Learning:** `ContentLibrary.tsx` uses `searchQuery` directly in the `useQuery` queryKey. This causes a new API call for every keystroke when typing in the search box, leading to excessive backend load and jittery UI updates. This happens because TanStack Query refetches when any part of the queryKey changes.
**Action:** Always debounce text inputs that are used in `useQuery` dependencies to prevent rapid-fire API requests.
