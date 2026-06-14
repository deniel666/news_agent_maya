## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-06-14 - React Performance - Debouncing Input State vs useQuery
**Learning:** In the frontend, state variables tied directly to input fields (like `searchQuery`) can trigger excessive API calls when passed directly to `useQuery` dependencies, as they update on every keystroke. This degrades performance significantly as it spams the backend API with intermediate queries.
**Action:** Always debounce input-bound state variables (e.g., using a `useDebounce` hook with a delay like 500ms) before passing them into the `useQuery` dependency array to optimize network performance.
