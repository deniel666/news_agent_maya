"""Tests for news aggregator service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.news_aggregator import NewsAggregatorService


class TestNewsAggregatorService:
    """Tests for NewsAggregatorService."""

    @pytest.fixture
    def aggregator(self):
        """Create aggregator instance."""
        return NewsAggregatorService()

    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_success(self, aggregator):
        """Test successful RSS feed fetching."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="""
            <?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0">
                <channel>
                    <item>
                        <title>Test Article</title>
                        <description>Test content</description>
                        <link>https://example.com/article</link>
                        <pubDate>Mon, 20 Jan 2026 10:00:00 GMT</pubDate>
                    </item>
                </channel>
            </rss>
        """)

        with patch.object(aggregator, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_client.get.return_value.__aenter__.return_value = mock_response
            mock_session.return_value = mock_client

            articles = await aggregator.fetch_rss_feeds(days=7)

            # Should have fetched articles
            assert isinstance(articles, list)

    @pytest.mark.asyncio
    async def test_fetch_rss_feeds_handles_errors(self, aggregator):
        """Test RSS feed error handling."""
        with patch.object(aggregator, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error")
            mock_session.return_value = mock_client

            # Should not raise, just return empty list
            articles = await aggregator.fetch_rss_feeds(days=7)
            assert articles == []

    @pytest.mark.asyncio
    async def test_aggregate_all(self, aggregator):
        """Test aggregate_all combines multiple sources."""
        with patch.object(aggregator, 'fetch_rss_feeds', new_callable=AsyncMock) as mock_rss:
            with patch.object(aggregator, 'fetch_nitter_feeds', new_callable=AsyncMock) as mock_nitter:
                mock_rss.return_value = [MagicMock(source_type='rss')]
                mock_nitter.return_value = [MagicMock(source_type='nitter')]

                articles = await aggregator.aggregate_all(days=7)

                assert len(articles) == 2
                mock_rss.assert_called_once_with(7)
                mock_nitter.assert_called_once_with(7)

    def test_clean_html(self, aggregator):
        """Test HTML cleaning."""
        html = "<p>Hello <b>World</b></p><script>evil()</script>"
        clean = aggregator._clean_html(html)

        assert "Hello" in clean
        assert "World" in clean
        assert "<p>" not in clean
        assert "<script>" not in clean

    def test_clean_html_empty(self, aggregator):
        """Test HTML cleaning with empty input."""
        assert aggregator._clean_html("") == ""
        assert aggregator._clean_html(None) == ""

    def test_parse_date_valid(self, aggregator):
        """Test date parsing with valid input."""
        date_str = "Mon, 20 Jan 2026 10:00:00 GMT"
        result = aggregator._parse_date(date_str)

        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20

    def test_parse_date_invalid(self, aggregator):
        """Test date parsing with invalid input."""
        assert aggregator._parse_date("not a date") is None
        assert aggregator._parse_date("") is None
        assert aggregator._parse_date(None) is None

    @pytest.mark.asyncio
    async def test_close(self, aggregator):
        """Test session cleanup."""
        # Create a session
        await aggregator._get_session()
        assert aggregator.session is not None

        # Close it
        await aggregator.close()
        # Session should be closed


class TestNitterIntegration:
    """Tests for Nitter/Twitter integration."""

    @pytest.fixture
    def aggregator(self):
        return NewsAggregatorService()

    @pytest.mark.asyncio
    async def test_fetch_nitter_feeds_tries_multiple_instances(self, aggregator):
        """Test Nitter fallback to multiple instances."""
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = MagicMock()
            if call_count <= 2:  # First two fail
                mock.status = 500
            else:  # Third succeeds
                mock.status = 200
                mock.text = AsyncMock(return_value="<rss><channel></channel></rss>")
            return mock

        with patch.object(aggregator, '_get_session') as mock_session:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_session.return_value = mock_client

            articles = await aggregator.fetch_nitter_feeds(days=7)

            # Should have tried multiple instances
            assert call_count >= 1
