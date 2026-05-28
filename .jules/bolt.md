## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.
## 2026-02-13 - API Calls on Keystroke
**Learning:** The frontend makes a backend API call on every single keystroke in the `ContentLibrary` search bar because Tanstack Query's `useQuery` dependencies include `searchQuery` directly without debouncing. This creates a significant performance bottleneck by hammering the server with requests for partial search terms (e.g. typing "test" triggers 4 sequential requests).
**Action:** For performance optimization, always debounce state variables tied to input fields before passing them as dependencies to Tanstack `useQuery` to prevent excessive API calls. Utilize the `useDebounce` hook available at `frontend/src/hooks/useDebounce.ts`.
