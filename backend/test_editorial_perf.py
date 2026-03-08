import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Mock sys.modules before importing app code
sys.modules['supabase'] = MagicMock()
mock_supabase = MagicMock()
sys.modules['app.core.database'] = MagicMock()
sys.modules['app.core.database'].supabase = mock_supabase

sys.modules['app.services.news_aggregator'] = MagicMock()
sys.modules['app.services.editorial_agent'] = MagicMock()

# Now import the pipeline
from app.services.editorial_pipeline import EditorialPipelineService
from app.models.schemas import NewsArticle
from datetime import datetime

async def main():
    print("Testing aggregate_and_store performance optimization...")

    # Setup mock aggregator
    mock_aggregator = AsyncMock()

    # Create test articles
    articles = [
        NewsArticle(
            source_type="rss",
            source_name="Test Source",
            title=f"Test Article {i}",
            content=f"Content {i}",
            url=f"https://example.com/article-{i}",
            published_at=datetime.utcnow(),
            category=None,
            relevance_score=None
        ) for i in range(10)
    ]
    # Add a duplicate URL within the batch
    articles.append(
        NewsArticle(
            source_type="rss",
            source_name="Test Source",
            title=f"Test Article Dup",
            content=f"Content Dup",
            url=f"https://example.com/article-1",
            published_at=datetime.utcnow(),
            category=None,
            relevance_score=None
        )
    )

    mock_aggregator.aggregate_all.return_value = articles

    # Setup pipeline
    pipeline = EditorialPipelineService()
    pipeline.aggregator = mock_aggregator

    # Setup mock supabase
    # 1. Existing URLs query mock
    mock_existing_resp = MagicMock()
    mock_existing_resp.data = [{"original_url": "https://example.com/article-0"}]

    # Create the chain for: supabase.table().select().in_().execute()
    mock_in = MagicMock()
    mock_in.execute.return_value = mock_existing_resp

    mock_select = MagicMock()
    mock_select.in_.return_value = mock_in

    # 2. Insert mock
    mock_insert_resp = MagicMock()
    mock_insert_resp.data = [{"id": f"story-id-{i}"} for i in range(1, 10)]

    mock_insert = MagicMock()
    mock_insert.execute.return_value = mock_insert_resp

    def table_mock(table_name):
        t = MagicMock()
        if table_name == "raw_stories":
            t.select.return_value = mock_select
            t.insert.return_value = mock_insert
        return t

    mock_supabase.table.side_effect = table_mock

    # Mock _score_story
    pipeline._score_story = AsyncMock()

    # Run
    result = await pipeline.aggregate_and_store(days=1, auto_score=True)

    print(f"Result: {result}")

    # Verify behavior
    assert result["total_fetched"] == 11
    # 1 from existing DB + 1 dup in batch = 2 skipped
    assert result["skipped_duplicates"] == 2
    assert result["stored"] == 9

    # Verify queries were batched
    mock_select.in_.assert_called_once()
    in_args = mock_select.in_.call_args[0]
    assert in_args[0] == "original_url"
    assert len(in_args[1]) == 11 # 11 urls checked

    mock_insert.execute.assert_called_once()

    assert pipeline._score_story.call_count == 9

    print("Test passed! Optimization works correctly and batches as expected.")

if __name__ == "__main__":
    asyncio.run(main())