## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-30 - Debouncing text inputs tied to react-query dependencies
**Learning:** Using Tanstack `useQuery` directly with text input state variables triggers excessive API calls on every keystroke.
**Action:** Always debounce state variables tied to input fields before passing them as dependencies to `useQuery` to optimize network requests.
