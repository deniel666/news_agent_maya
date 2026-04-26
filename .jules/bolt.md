## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2025-04-26 - React Query Debouncing
**Learning:** Typing rapidly in search inputs directly tied to `useQuery` dependencies causes excessive sequential backend requests, which can block the main thread and throttle backend performance.
**Action:** Always wrap user-typed text inputs with a `useDebounce` hook before passing them to Tanstack React Query dependencies or backend API parameters to coalesce sequential updates.
