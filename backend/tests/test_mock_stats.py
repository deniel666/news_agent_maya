import asyncio
from unittest.mock import MagicMock

class MockDb:
    def execute(self):
        import time
        time.sleep(0.1)
        return MagicMock(data=[])

    def execute_slow(self):
        import time
        time.sleep(0.1)
        return MagicMock(count=10, data=[])

class StatsClient:
    def __init__(self):
        self.client = MagicMock()
        self.client.table.return_value.select.return_value.execute.side_effect = self.execute_slow
        self.client.table.return_value.select.return_value.gte.return_value.execute.side_effect = self.execute_slow

    def execute_slow(self):
        import time
        time.sleep(0.1)
        return MagicMock(count=10, data=[])

    async def get_dashboard_stats_seq(self):
        briefings = self.client.table("weekly_briefings").select("id", count="exact").execute()
        videos = self.client.table("weekly_videos").select("id", count="exact").execute()
        posts = self.client.table("social_posts").select("id", count="exact").execute()
        return {"total": briefings.count + videos.count + posts.count}

    async def get_dashboard_stats_concurrent(self):
        import asyncio

        briefings_query = self.client.table("weekly_briefings").select("id", count="exact")
        videos_query = self.client.table("weekly_videos").select("id", count="exact")
        posts_query = self.client.table("social_posts").select("id", count="exact")

        briefings, videos, posts = await asyncio.gather(
            asyncio.to_thread(briefings_query.execute),
            asyncio.to_thread(videos_query.execute),
            asyncio.to_thread(posts_query.execute)
        )
        return {"total": briefings.count + videos.count + posts.count}

async def main():
    import time
    client = StatsClient()

    start = time.time()
    await client.get_dashboard_stats_seq()
    print(f"Seq: {time.time() - start:.2f}s")

    start = time.time()
    await client.get_dashboard_stats_concurrent()
    print(f"Concurrent: {time.time() - start:.2f}s")

asyncio.run(main())
