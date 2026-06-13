## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-12 - Debouncing React Query Dependencies
**Learning:** Directly binding high-frequency state updates (like text input `onChange`) to a Tanstack `useQuery` query key dependency triggers excessive, rapid network requests. This causes severe backend load and frontend UI stuttering.
**Action:** Always debounce state variables tied to input fields before passing them as dependencies to `useQuery` hooks.
