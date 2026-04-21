## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2025-04-21 - Debouncing State Passed to Tanstack React Query
**Learning:** React Query queries will run on every change of any dependency inside the query key and queryFn. Passing search input directly causes an excessive number of API calls while a user is typing. Debouncing the input value before adding it as a query parameter or key efficiently prevents rapid continuous network requests on each keystroke without needing complex `useEffect` timeout management.
**Action:** Always wrap user-facing rapid input values in a `useDebounce` hook before feeding them into a `useQuery` query object to avoid triggering unneeded and frequent API calls that slow down frontend performance.
