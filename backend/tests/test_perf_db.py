import asyncio
import time
from unittest.mock import MagicMock

async def test_sequential():
    def execute():
        time.sleep(0.1)
        return "data"

    start = time.time()
    execute()
    execute()
    execute()
    execute()
    execute()
    print(f"Sequential: {time.time() - start:.2f}s")

async def test_concurrent():
    def execute():
        time.sleep(0.1)
        return "data"

    start = time.time()
    await asyncio.gather(
        asyncio.to_thread(execute),
        asyncio.to_thread(execute),
        asyncio.to_thread(execute),
        asyncio.to_thread(execute),
        asyncio.to_thread(execute)
    )
    print(f"Concurrent: {time.time() - start:.2f}s")

async def main():
    await test_sequential()
    await test_concurrent()

asyncio.run(main())
