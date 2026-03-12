import sys
import asyncio
from unittest.mock import MagicMock

# Mock out required modules
sys.modules['supabase'] = MagicMock()
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.models.schemas'] = MagicMock()
sys.modules['app.models.content'] = MagicMock()
sys.modules['app.models.sources'] = MagicMock()
sys.modules['app.models.editorial'] = MagicMock()
sys.modules['feedparser'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['aiohttp'] = MagicMock()
sys.modules['certifi'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['app.agents.pipeline'] = MagicMock()
sys.modules['app.agents.ondemand'] = MagicMock()
sys.modules['app.agents'] = MagicMock()
sys.modules['app.integrations.heygen'] = MagicMock()
sys.modules['app.integrations.blotato'] = MagicMock()

# Re-mock specific attributes for imports
models_schemas = sys.modules['app.models.schemas']
models_schemas.WeeklyBriefingCreate = MagicMock
models_schemas.WeeklyBriefing = MagicMock
models_schemas.WeeklyVideoCreate = MagicMock
models_schemas.WeeklyVideo = MagicMock
models_schemas.SocialPostCreate = MagicMock
models_schemas.SocialPost = MagicMock
models_schemas.PipelineStatus = MagicMock()
models_schemas.PipelineStatus.COMPLETED = MagicMock()
models_schemas.PipelineStatus.COMPLETED.value = "completed"
models_schemas.PipelineStatus.AWAITING_SCRIPT_APPROVAL = MagicMock()
models_schemas.PipelineStatus.AWAITING_SCRIPT_APPROVAL.value = "awaiting_script"
models_schemas.PipelineStatus.AWAITING_VIDEO_APPROVAL = MagicMock()
models_schemas.PipelineStatus.AWAITING_VIDEO_APPROVAL.value = "awaiting_video"

models_content = sys.modules['app.models.content']
models_content.Story = MagicMock
models_content.StoryCreate = MagicMock
models_content.StoryUpdate = MagicMock
models_content.StoryWithAssets = MagicMock
models_content.VideoAsset = MagicMock
models_content.VideoAssetCreate = MagicMock
models_content.PublishRecord = MagicMock
models_content.PublishRecordCreate = MagicMock
models_content.ContentStats = MagicMock
models_content.StoryStatus = MagicMock
models_content.StoryType = MagicMock

models_sources = sys.modules['app.models.sources']
models_sources.OnDemandJob = MagicMock
models_sources.Language = MagicMock
models_sources.NewsSource = MagicMock
models_sources.NewsSourceCreate = MagicMock
models_sources.NewsSourceUpdate = MagicMock
models_sources.SourceType = MagicMock

import app.services.database as db
# Setup the pipeline status mock locally inside the module
db.PipelineStatus = models_schemas.PipelineStatus

async def main():
    service = db.DatabaseService()
    service.mock_mode = False

    # Mock the internal client
    service.client = MagicMock()

    # Mock query result structure
    mock_result = MagicMock()
    mock_result.count = 5
    mock_result.data = [
        {"id": "1", "status": "completed", "story_type": "news", "language": "en", "platform": "twitter"},
        {"id": "2", "status": "published", "story_type": "article", "language": "ms", "platform": "facebook"}
    ]

    # When select is called, return the query builder which returns mock_result on execute
    mock_query_builder = MagicMock()
    mock_query_builder.select.return_value = mock_query_builder
    mock_query_builder.gte.return_value = mock_query_builder
    mock_query_builder.execute.return_value = mock_result

    service.client.table.return_value = mock_query_builder

    print("Testing get_dashboard_stats...")
    dash_stats = await service.get_dashboard_stats()
    print("Dashboard stats:", dash_stats)

    print("\nTesting get_content_stats...")
    content_stats = await service.get_content_stats()
    print("Content stats:", content_stats)

if __name__ == "__main__":
    asyncio.run(main())
