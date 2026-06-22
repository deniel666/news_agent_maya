## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-02-09 - React Query Debouncing Missing
**Learning:** Found multiple instances where search inputs directly trigger `useQuery` fetches on every keystroke (e.g., in ContentLibrary.tsx). This causes excessive network requests and UI stutter.
**Action:** Use the `useDebounce` hook (created if missing) to wrap the search input state before passing it into the `useQuery` dependency array. This prevents a flood of requests while typing.
