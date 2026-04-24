## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2024-04-24 - Search Input Debouncing
**Learning:** Frequent API calls from uncontrolled `onChange` search inputs create frontend and backend overhead. The `useDebounce` hook provides an elegant way to rate-limit these calls in React without degrading the typing experience.
**Action:** Always debounce state variables tied to user input before passing them as dependencies to network fetching hooks like `useQuery`.
