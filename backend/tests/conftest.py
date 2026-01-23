"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

# Configure async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "test-uuid",
            "thread_id": "2026-W01",
            "year": 2026,
            "week_number": 1,
            "status": "aggregating",
            "created_at": "2026-01-01T00:00:00Z",
        }
    ]
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.execute.return_value.count = 0
    return mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    mock = AsyncMock()
    mock.ainvoke.return_value.content = "Test response"
    return mock


@pytest.fixture
def mock_heygen():
    """Mock HeyGen client."""
    mock = AsyncMock()
    mock.generate_video.return_value = {
        "video_id": "test-video-id",
        "status": "pending",
    }
    mock.get_video_status.return_value = {
        "video_id": "test-video-id",
        "status": "completed",
        "video_url": "https://example.com/video.mp4",
        "duration": 150,
    }
    return mock


@pytest.fixture
def sample_articles():
    """Sample news articles for testing."""
    return [
        {
            "source_type": "rss",
            "source_name": "CNA",
            "title": "Singapore announces new tech initiative",
            "content": "The Singapore government announced a new technology initiative...",
            "url": "https://example.com/article1",
            "published_at": "2026-01-20T10:00:00Z",
        },
        {
            "source_type": "rss",
            "source_name": "Straits Times",
            "title": "Regional trade deal signed",
            "content": "ASEAN countries signed a new regional trade agreement...",
            "url": "https://example.com/article2",
            "published_at": "2026-01-19T08:00:00Z",
        },
        {
            "source_type": "nitter",
            "source_name": "@TechInAsia",
            "title": None,
            "content": "Breaking: Major AI startup raises $100M in Series B...",
            "url": "https://nitter.net/TechInAsia/status/123",
            "published_at": "2026-01-18T15:30:00Z",
        },
    ]


@pytest.fixture
def sample_state():
    """Sample pipeline state for testing."""
    return {
        "week_number": 1,
        "year": 2026,
        "thread_id": "2026-W01",
        "raw_articles": [],
        "local_news": [],
        "business_news": [],
        "ai_news": [],
        "local_script": None,
        "business_script": None,
        "ai_script": None,
        "full_script": None,
        "heygen_video_id": None,
        "video_url": None,
        "video_duration": None,
        "caption": None,
        "post_results": None,
        "status": "aggregating",
        "error": None,
        "script_approved": None,
        "script_feedback": None,
        "video_approved": None,
    }
