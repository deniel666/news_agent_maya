## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2024-06-05 - Debounce React State for Tanstack Query Dependencies
**Learning:** Debouncing state variables tied to input fields before passing them as dependencies to Tanstack useQuery prevents excessive API calls on every keystroke, which is crucial for frontend performance.
**Action:** Always debounce state variables tied to input fields before passing them to useQuery.
