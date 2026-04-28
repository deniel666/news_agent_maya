## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2024-04-28 - [Frontend Search Debouncing Optimization]
 **Learning:** In highly interactive React components utilizing `react-query` with search input fields as query dependencies, lack of debouncing causes excessive backend API requests and potential UI rendering issues on every keystroke. Using a custom `useDebounce` hook wrapping `setTimeout` inside `useEffect` effectively mitigates this without sacrificing responsiveness.
 **Action:** Always look for and implement debouncing on any text input fields that directly trigger search API queries or expensive client-side filtering via `react-query` hooks.
