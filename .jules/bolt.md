## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-22 - Debounce state variables tied to input fields passed to Tanstack useQuery
**Learning:** React state variables updated directly by user input components (like search fields) trigger a re-render on every keystroke. When these variables are passed as dependencies to data fetching hooks like Tanstack Query's `useQuery`, it results in an excessive number of API calls being fired off sequentially.
**Action:** Always debounce state variables tied to input fields before passing them as dependencies to `useQuery` (e.g., using `useDebounce` with a 300ms-500ms delay) to significantly reduce the frequency of API calls and improve perceived application performance.
