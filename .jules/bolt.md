## 2026-02-18 - [Offload CPU-Bound Feed Parsing]
**Learning:** `feedparser.parse` and `BeautifulSoup` operations are synchronous and CPU-bound, which can block the asyncio event loop for significant periods (hundreds of milliseconds per feed) when processing large feeds or multiple feeds concurrently.
**Action:** Encapsulate CPU-intensive parsing logic into synchronous helper methods and execute them in a separate thread using `asyncio.to_thread`. This ensures the event loop remains responsive for other I/O tasks.
