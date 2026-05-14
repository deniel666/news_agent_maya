## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-14 - Excessive API Calls in React Query with Uncontrolled Input
**Learning:** Attaching TanStack `useQuery` dependencies directly to uncontrolled or rapid-fire state inputs (like text search boxes) triggers redundant, expensive API calls on every keystroke, stressing the backend and degrading frontend responsiveness.
**Action:** Always wrap state variables tied to user input fields with a `useDebounce` hook before passing them as dependencies to TanStack's `useQuery`.
