import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Set up path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock database module before importing editorial_pipeline
sys.modules['app.core.database'] = MagicMock()
mock_supabase = MagicMock()
sys.modules['app.core.database'].supabase = mock_supabase

# Mock aggregator and editorial agent
sys.modules['app.services.news_aggregator'] = MagicMock()
sys.modules['app.services.editorial_agent'] = MagicMock()

# Import the service
from app.services.editorial_pipeline import EditorialPipelineService
from app.models.schemas import NewsArticle
from datetime import datetime

async def main():
    service = EditorialPipelineService()

    # Mock articles
    articles = [
        NewsArticle(source_type="rss", source_name="Test", title="Test 1", content="Content 1", url="http://test.com/1", published_at=datetime.utcnow()),
        NewsArticle(source_type="rss", source_name="Test", title="Test 2", content="Content 2", url="http://test.com/2", published_at=datetime.utcnow()),
        NewsArticle(source_type="rss", source_name="Test", title="Test 3", content="Content 3", url="http://test.com/1", published_at=datetime.utcnow()) # Duplicate
    ]
    service.aggregator.aggregate_all = AsyncMock(return_value=articles)

    # Mock DB responses
    # 1st call is for fetching existing URLs
    mock_in_execute = MagicMock()
    mock_in_execute.execute.return_value = MagicMock(data=[{"original_url": "http://test.com/2"}])
    mock_in = MagicMock()
    mock_in.in_.return_value = mock_in_execute
    mock_select = MagicMock()
    mock_select.select.return_value = mock_in

    # 2nd call is for insertion
    mock_insert_execute = MagicMock()
    mock_insert_execute.execute.return_value = MagicMock(data=[{"id": "uuid-1"}, {"id": "uuid-2"}])
    mock_insert = MagicMock()
    mock_insert.insert.return_value = mock_insert_execute

    # Set up the table mock to return either select or insert depending on the method called
    def table_mock(name):
        mock_obj = MagicMock()
        if name == "raw_stories":
            mock_obj.select = mock_select.select
            mock_obj.insert = mock_insert.insert
        return mock_obj

    mock_supabase.table = table_mock

    # Mock scoring
    service._score_story = AsyncMock()

    print("Running aggregate_and_store...")
    result = await service.aggregate_and_store(auto_score=True)

    print("\nResult:")
    print(result)

    print("\nVerification:")
    assert result['total_fetched'] == 3, f"Expected 3 fetched, got {result['total_fetched']}"
    assert result['skipped_duplicates'] == 2, f"Expected 2 skipped (1 from db, 1 from intra-batch), got {result['skipped_duplicates']}"
    assert result['stored'] == 2, f"Expected 2 stored (mocked response), got {result['stored']}"

    print("All tests passed! Batched processing working correctly.")

if __name__ == "__main__":
    asyncio.run(main())
