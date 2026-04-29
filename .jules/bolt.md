## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-05-18 - Missing debounce on search query hooks
**Learning:** The `ContentLibrary` component was directly passing user input (`searchQuery` state from a text input) into a Tanstack `useQuery` dependency array and parameter payload, leading to an immediate API call fired on every single keystroke.
**Action:** Always wrap user text inputs linked to query dependencies with a `useDebounce` hook to significantly reduce rapid-fire network requests and backend load, ensuring only meaningful searches execute.
