## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-02-12 - Missing debouncing on search queries
**Learning:** React state variables bound to user input (like search queries) that are directly passed as dependencies to Tanstack `useQuery` trigger an API call on every keystroke, which is a major frontend performance bottleneck.
**Action:** Always debounce state variables tied to input fields before passing them to `useQuery`.
