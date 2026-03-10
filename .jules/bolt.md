## 2026-02-09 - Sequential I/O in Aggregators
**Learning:** The `NewsAggregatorService` was fetching RSS and Nitter feeds sequentially, which is a major bottleneck as these are I/O bound operations. This pattern often goes unnoticed in initial implementations but scales poorly.
**Action:** Always use `asyncio.gather` for independent I/O bound tasks in aggregators.

## 2026-02-14 - Event Loop Blocking via XML Parsing
**Learning:** Running `feedparser.parse()` and `BeautifulSoup` sequentially inside the `asyncio` event loop is a massive CPU bottleneck for the news aggregator service. Standard `asyncio` waits for network calls, but gets stuck performing intensive parsing computations. Furthermore, doing this concurrently with `ThreadPoolExecutor` isn't very effective because of the Python GIL contention over large parsing trees.
**Action:** When extracting data from large XML/HTML payloads in async python apps, use `ProcessPoolExecutor` via `loop.run_in_executor` and make sure the target functions are decoupled to the module scope so they can be effectively pickled.
