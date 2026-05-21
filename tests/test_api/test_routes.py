"""Tests for FastAPI routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from courtvision.api.main import app


@pytest.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for /api/v1/health."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["chain"] == "polygon-amoy"
        assert data["protocol"] == "azuro"
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_health_games_analyzed(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "games_analyzed" in data
        assert isinstance(data["games_analyzed"], int)

    @pytest.mark.asyncio
    async def test_health_predictions_generated(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "predictions_generated" in data
        assert isinstance(data["predictions_generated"], int)


class TestGamesEndpoints:
    """Tests for /api/v1/games/*."""

    @pytest.mark.asyncio
    async def test_get_upcoming_games(self, client):
        response = await client.get("/api/v1/games/upcoming")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        game = data[0]
        assert "id" in game
        assert "home_team" in game
        assert "away_team" in game

    @pytest.mark.asyncio
    async def test_get_upcoming_games_with_limit(self, client):
        response = await client.get("/api/v1/games/upcoming?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    @pytest.mark.asyncio
    async def test_get_game_by_id(self, client):
        response = await client.get("/api/v1/games/NBA-2025-PO-G101")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "NBA-2025-PO-G101"
        assert data["status"] == "finished"

    @pytest.mark.asyncio
    async def test_get_game_not_found(self, client):
        response = await client.get("/api/v1/games/NONEXISTENT")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_live_games(self, client):
        response = await client.get("/api/v1/games/live")
        # May return 200 with empty list or 404 if no live games
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_get_finished_games(self, client):
        response = await client.get("/api/v1/games/finished")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_finished_games_with_limit(self, client):
        response = await client.get("/api/v1/games/finished?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 1


class TestPredictionsEndpoints:
    """Tests for /api/v1/predictions/*."""

    @pytest.mark.asyncio
    async def test_get_game_prediction(self, client):
        response = await client.get("/api/v1/predictions/game/NBA-2025-PO-G001")
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "NBA-2025-PO-G001"
        assert "predicted_winner" in data
        assert "confidence" in data
        assert "home_win_probability" in data

    @pytest.mark.asyncio
    async def test_get_prediction_not_found_game(self, client):
        response = await client.get("/api/v1/predictions/game/NONEXISTENT")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_analyze_matchup(self, client):
        response = await client.post(
            "/api/v1/predictions/analyze",
            params={"home_team_id": 1, "away_team_id": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["home_team"] == "Boston Celtics"
        assert data["away_team"] == "New York Knicks"

    @pytest.mark.asyncio
    async def test_analyze_matchup_invalid_team(self, client):
        response = await client.post(
            "/api/v1/predictions/analyze",
            params={"home_team_id": 999, "away_team_id": 2},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_prediction_history(self, client):
        # First generate a prediction
        await client.get("/api/v1/predictions/game/NBA-2025-PO-G001")
        response = await client.get("/api/v1/predictions/history")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total" in data


class TestMarketsEndpoints:
    """Tests for /api/v1/markets/*."""

    @pytest.mark.asyncio
    async def test_get_active_markets_empty(self, client):
        response = await client.get("/api/v1/markets/active")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_create_market(self, client):
        response = await client.post(
            "/api/v1/markets/create",
            params={"game_id": "NBA-2025-PO-G001"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "NBA-2025-PO-G001"
        assert data["home_team"] == "Boston Celtics"

    @pytest.mark.asyncio
    async def test_create_market_not_found(self, client):
        response = await client.post(
            "/api/v1/markets/create",
            params={"game_id": "NONEXISTENT"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_market_stats(self, client):
        response = await client.get("/api/v1/markets/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_markets" in data
        assert "chain_id" in data

    @pytest.mark.asyncio
    async def test_get_market_by_id(self, client):
        # Create a market first
        await client.post("/api/v1/markets/create", params={"game_id": "NBA-2025-PO-G001"})
        response = await client.get("/api/v1/markets/1")
        assert response.status_code == 200
        data = response.json()
        assert data["market_id"] == 1

    @pytest.mark.asyncio
    async def test_get_market_not_found(self, client):
        response = await client.get("/api/v1/markets/999")
        assert response.status_code == 404


class TestLeaderboardEndpoint:
    """Tests for /api/v1/stats/leaderboard."""

    @pytest.mark.asyncio
    async def test_get_leaderboard(self, client):
        response = await client.get("/api/v1/stats/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        entry = data[0]
        assert "rank" in entry
        assert "user_address" in entry
        assert "accuracy" in entry

    @pytest.mark.asyncio
    async def test_leaderboard_limit(self, client):
        response = await client.get("/api/v1/stats/leaderboard?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_leaderboard_ordering(self, client):
        response = await client.get("/api/v1/stats/leaderboard")
        data = response.json()
        for i in range(1, len(data)):
            assert data[i]["accuracy"] <= data[i - 1]["accuracy"]
