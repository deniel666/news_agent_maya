## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2024-05-02 - Debouncing React State for Tanstack Query
**Learning:** When using Tanstack's `useQuery` where a query key dependency is tied to a rapidly updating state value (like an `onChange` search text input), it triggers excessive unneeded API requests. The query fetches on every single keystroke.
**Action:** Use a `useDebounce` hook to create a delayed version of the state variable, and pass *that* debounced variable to the `useQuery` dependency array and query function instead of the raw state variable.
