## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-02-12 - Missing Debounce on Search Input in ContentLibrary
**Learning:** The `ContentLibrary` component was directly passing the `searchQuery` state to `useQuery`, triggering a new API call on every keystroke when typing in the search input. This can lead to excessive API requests and backend overload.
**Action:** Use the `useDebounce` hook to debounce the `searchQuery` state before passing it to `useQuery` to reduce the number of API calls during rapid typing.
