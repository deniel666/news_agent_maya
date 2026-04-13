## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2024-05-18 - Automated Reviews and Supabase Concurrency
**Learning:** Automated code reviews can sometimes hallucinate or aggressively misunderstand context, such as falsely assuming a function is synchronous when it is explicitly defined with `async def`, leading to incorrect "blocking" feedback about `SyntaxError`s when using `asyncio` to wrap synchronous clients. Also, using `asyncio.to_thread` with `asyncio.gather` is an effective, valid way to parallelize multiple synchronous I/O blocks (like `supabase-python` queries) inside an existing `async` function.
**Action:** When a reviewer flags a critical syntax error (like `await outside async`), do not immediately revert valid optimizations. Instead, verify the actual file syntax independently (e.g. using `python -m py_compile` and checking the function signature). If the reviewer is proven wrong, confidently proceed with the valid approach.
