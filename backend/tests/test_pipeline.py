"""Tests for Maya pipeline."""

import sys
from unittest.mock import MagicMock

# Mock supabase to prevent connection attempts during import
# This is necessary because some modules might trigger Supabase client creation
mock_supabase = MagicMock()
sys.modules["supabase"] = mock_supabase
sys.modules["supabase.client"] = MagicMock()

import pytest
from unittest.mock import AsyncMock, patch
from app.agents.pipeline import MayaPipeline
from app.models.schemas import PipelineStatus, NewsArticle
from datetime import datetime

class TestMayaPipelineIntegration:
    """Integration tests for MayaPipeline."""

    @pytest.fixture
    def mock_db(self):
        with patch('app.agents.pipeline.get_db_service') as mock:
            mock.return_value.create_briefing = AsyncMock()
            mock.return_value.update_briefing = AsyncMock()
            mock.return_value.get_briefing_by_thread = AsyncMock()
            yield mock

    @pytest.fixture
    def mock_aggregator(self):
        with patch('app.agents.nodes.get_news_aggregator') as mock:
            # Return some dummy articles to trigger categorization
            article = NewsArticle(
                source_type="rss",
                source_name="Test Source",
                title="Test Article",
                content="Test Content",
                url="http://test.com",
                published_at=datetime.utcnow()
            )
            mock.return_value.aggregate_all = AsyncMock(return_value=[article])
            yield mock

    @pytest.fixture
    def mock_llm(self):
        with patch('app.agents.nodes.get_llm') as mock:
            mock_llm_instance = AsyncMock()
            # Mock invoke to return a message-like object
            mock_msg = MagicMock()
            mock_msg.content = "local" # Default category response
            mock_llm_instance.ainvoke.return_value = mock_msg
            mock.return_value = mock_llm_instance
            yield mock

    @pytest.fixture
    def mock_notification(self):
        with patch('app.agents.nodes.get_notification_service') as mock:
            mock.return_value.send_script_approval_request = AsyncMock()
            mock.return_value.send_video_approval_request = AsyncMock()
            yield mock

    @pytest.fixture
    def mock_heygen(self):
        with patch('app.agents.nodes.get_heygen_client') as mock:
            mock.return_value.generate_video = AsyncMock(return_value={"video_id": "vid_123"})
            mock.return_value.wait_for_video = AsyncMock(
                return_value={"video_url": "http://video.com/1.mp4", "duration": 60}
            )
            yield mock

    @pytest.fixture
    def mock_blotato(self):
        with patch('app.agents.nodes.get_blotato_client') as mock:
            mock.return_value.schedule_multi_platform = AsyncMock(return_value=[])
            yield mock

    @pytest.mark.asyncio
    async def test_start_briefing_flow(
        self, mock_db, mock_aggregator, mock_llm, mock_notification, mock_heygen, mock_blotato
    ):
        """Test the full briefing flow (happy path)."""
        pipeline = MayaPipeline()

        # Start the briefing
        # With current logic, it should run through to completion because routing defaults to continue
        result = await pipeline.start_briefing(week_number=1, year=2026)

        assert result["week_number"] == 1
        assert result["year"] == 2026

        # Verify aggregation was called
        mock_aggregator.return_value.aggregate_all.assert_called_once()

        # Verify LLM was called
        # 1. Categorize (1 article)
        # 2. Synthesize Local
        # 3. Synthesize Business
        # 4. Synthesize AI
        # 5. Caption generation
        # Total = 5
        assert mock_llm.return_value.ainvoke.call_count >= 5

        # Verify notifications
        mock_notification.return_value.send_script_approval_request.assert_called_once()
        mock_notification.return_value.send_video_approval_request.assert_called_once()

        # Verify video generation
        mock_heygen.return_value.generate_video.assert_called_once()

        # Verify publishing
        mock_blotato.return_value.schedule_multi_platform.assert_called_once()
