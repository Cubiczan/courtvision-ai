"""Tests for Azuro Protocol integration service."""

import pytest
from datetime import datetime, timezone, timedelta

from courtvision.models.nba import MarketStatus
from courtvision.services.azuro_service import AzuroService, POLYGON_AMOY_CHAIN_ID


class TestAzuroService:
    """Tests for AzuroService."""

    @pytest.fixture
    def azuro(self):
        return AzuroService()

    def test_initialization(self, azuro):
        assert hasattr(azuro, '_markets')
        assert hasattr(azuro, '_market_counter')

    def test_create_market(self, azuro):
        market = azuro.create_market(
            game_id="NBA-001",
            home_team="Boston Celtics",
            away_team="New York Knicks",
            scheduled_tipoff=datetime(2025, 5, 15, 19, 0, tzinfo=timezone.utc),
            home_odds=1.85,
            away_odds=2.10,
        )
        assert market.market_id == 1
        assert market.game_id == "NBA-001"
        assert market.home_team == "Boston Celtics"
        assert market.away_team == "New York Knicks"
        assert market.status == MarketStatus.ACTIVE
        assert market.home_odds == 1.85
        assert market.away_odds == 2.10
        assert market.total_liquidity == 0.0

    def test_create_multiple_markets(self, azuro):
        m1 = azuro.create_market("G1", "Team A", "Team B",
                                 datetime(2025, 5, 15, tzinfo=timezone.utc))
        m2 = azuro.create_market("G2", "Team C", "Team D",
                                 datetime(2025, 5, 16, tzinfo=timezone.utc))
        assert m1.market_id == 1
        assert m2.market_id == 2

    def test_get_market_found(self, azuro):
        created = azuro.create_market("G1", "A", "B",
                                      datetime(2025, 5, 15, tzinfo=timezone.utc))
        retrieved = azuro.get_market(created.market_id)
        assert retrieved is not None
        assert retrieved.game_id == "G1"

    def test_get_market_not_found(self, azuro):
        market = azuro.get_market(999)
        assert market is None

    def test_get_active_markets(self, azuro):
        azuro.create_market("G1", "A", "B", datetime(2025, 5, 15, tzinfo=timezone.utc))
        azuro.create_market("G2", "C", "D", datetime(2025, 5, 16, tzinfo=timezone.utc))
        active = azuro.get_active_markets()
        assert len(active) == 2

    def test_get_active_markets_empty(self, azuro):
        active = azuro.get_active_markets()
        assert active == []

    def test_lock_market(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        result = azuro.lock_market(market.market_id)
        assert result is True
        locked = azuro.get_market(market.market_id)
        assert locked.status == MarketStatus.LOCKED

    def test_lock_market_not_found(self, azuro):
        result = azuro.lock_market(999)
        assert result is False

    def test_lock_already_locked_market(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        azuro.lock_market(market.market_id)
        result = azuro.lock_market(market.market_id)
        assert result is False

    def test_resolve_market(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        result = azuro.resolve_market(market.market_id, 112, 98)
        assert result is True
        resolved = azuro.get_market(market.market_id)
        assert resolved.status == MarketStatus.RESOLVED

    def test_resolve_market_not_found(self, azuro):
        result = azuro.resolve_market(999, 100, 90)
        assert result is False

    def test_resolve_already_resolved(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        azuro.resolve_market(market.market_id, 100, 90)
        result = azuro.resolve_market(market.market_id, 110, 95)
        assert result is False

    def test_simulate_bet_home(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        result = azuro.simulate_bet(market.market_id, "home_win", 100.0)
        assert result["outcome"] == "home_win"
        assert result["amount"] == 100.0
        assert result["potential_payout"] > 0
        assert result["total_liquidity"] == 100.0

    def test_simulate_bet_away(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        result = azuro.simulate_bet(market.market_id, "away_win", 50.0)
        assert result["outcome"] == "away_win"
        assert result["amount"] == 50.0

    def test_simulate_bet_updates_odds(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc), 2.0, 2.0)
        azuro.simulate_bet(market.market_id, "home_win", 100.0)
        updated = azuro.get_market(market.market_id)
        assert updated.home_odds < 2.0  # More bets on home -> lower odds
        assert updated.away_odds >= 2.0  # Away odds stay at or above initial

    def test_simulate_bet_market_not_found(self, azuro):
        result = azuro.simulate_bet(999, "home_win", 100.0)
        assert "error" in result

    def test_multiple_bets_accumulate_liquidity(self, azuro):
        market = azuro.create_market("G1", "A", "B",
                                     datetime(2025, 5, 15, tzinfo=timezone.utc))
        azuro.simulate_bet(market.market_id, "home_win", 100.0)
        azuro.simulate_bet(market.market_id, "away_win", 80.0)
        azuro.simulate_bet(market.market_id, "home_win", 50.0)
        updated = azuro.get_market(market.market_id)
        assert updated.total_liquidity == 230.0

    def test_get_market_stats_empty(self, azuro):
        stats = azuro.get_market_stats()
        assert stats["total_markets"] == 0
        assert stats["active_markets"] == 0
        assert stats["total_liquidity"] == 0

    def test_get_market_stats_with_data(self, azuro):
        m1 = azuro.create_market("G1", "A", "B",
                                 datetime(2025, 5, 15, tzinfo=timezone.utc))
        azuro.simulate_bet(m1.market_id, "home_win", 100.0)
        stats = azuro.get_market_stats()
        assert stats["total_markets"] == 1
        assert stats["active_markets"] == 1
        assert stats["total_liquidity"] == 100.0

    def test_chain_id(self, azuro):
        assert POLYGON_AMOY_CHAIN_ID == 80002
