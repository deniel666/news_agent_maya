"""Tests for API endpoints."""

import sys
from unittest.mock import MagicMock

# Mock supabase to prevent connection attempts during import
if "supabase" not in sys.modules:
    mock_supabase = MagicMock()
    sys.modules["supabase"] = mock_supabase
    sys.modules["supabase.client"] = MagicMock()

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns app info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Maya AI News Anchor"
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDashboardAPI:
    """Tests for dashboard API endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_dashboard_stats(self, client):
        """Test dashboard stats endpoint."""
        with patch('app.api.dashboard.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.get_dashboard_stats = AsyncMock(return_value={
                "total_briefings": 5,
                "completed_briefings": 3,
                "pending_approvals": 1,
                "total_videos": 3,
                "total_posts": 12,
            })
            mock_db.return_value = mock_service

            response = client.get("/api/v1/dashboard/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_briefings" in data
            assert "pending_approvals" in data

    def test_get_weekly_summary(self, client):
        """Test weekly summary endpoint."""
        with patch('app.api.dashboard.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.get_briefing_by_week = AsyncMock(return_value=None)
            mock_db.return_value = mock_service

            response = client.get("/api/v1/dashboard/weekly-summary")

            assert response.status_code == 200
            data = response.json()
            assert "weeks" in data
            assert len(data["weeks"]) == 4  # Last 4 weeks


class TestBriefingsAPI:
    """Tests for briefings API endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_list_briefings_empty(self, client):
        """Test listing briefings when empty."""
        with patch('app.api.briefings.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.list_briefings = AsyncMock(return_value=[])
            mock_db.return_value = mock_service

            response = client.get("/api/v1/briefings/")

            assert response.status_code == 200
            assert response.json() == []

    def test_create_briefing_duplicate(self, client):
        """Test creating duplicate briefing returns error."""
        with patch('app.api.briefings.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.get_briefing_by_week = AsyncMock(return_value=MagicMock())
            mock_db.return_value = mock_service

            response = client.post("/api/v1/briefings/")

            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

    def test_get_briefing_not_found(self, client):
        """Test getting non-existent briefing."""
        with patch('app.api.briefings.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.get_briefing_by_thread = AsyncMock(return_value=None)
            mock_db.return_value = mock_service

            response = client.get("/api/v1/briefings/2026-W99")

            assert response.status_code == 404


class TestApprovalsAPI:
    """Tests for approvals API endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_pending_approvals(self, client):
        """Test getting pending approvals."""
        with patch('app.api.approvals.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.get_pending_approvals = AsyncMock(return_value=[])
            mock_db.return_value = mock_service

            response = client.get("/api/v1/approvals/pending")

            assert response.status_code == 200
            data = response.json()
            assert "script_approvals" in data
            assert "video_approvals" in data

    def test_approve_script_not_found(self, client):
        """Test approving script for non-existent briefing."""
        with patch('app.api.approvals.get_db_service') as mock_db:
            mock_service = MagicMock()
            mock_service.get_briefing_by_thread = AsyncMock(return_value=None)
            mock_db.return_value = mock_service

            response = client.post(
                "/api/v1/approvals/script",
                json={"thread_id": "2026-W99", "approved": True}
            )

            assert response.status_code == 404


class TestSettingsAPI:
    """Tests for settings API endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_settings_status(self, client):
        """Test settings status endpoint."""
        response = client.get("/api/v1/settings/status")

        assert response.status_code == 200
        data = response.json()
        assert "heygen_configured" in data
        assert "openai_configured" in data

    def test_get_news_sources(self, client):
        """Test news sources endpoint."""
        response = client.get("/api/v1/settings/news-sources")

        assert response.status_code == 200
        data = response.json()
        assert "rss_feeds" in data
        assert "twitter_accounts" in data
        assert "telegram_channels" in data

    def test_test_connection_unknown_service(self, client):
        """Test connection test with unknown service."""
        response = client.post(
            "/api/v1/settings/test-connection",
            json={"service": "unknown"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
