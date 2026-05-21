"""Tests for the prediction engine."""

import pytest
from courtvision.engines.prediction import PredictionEngine
from courtvision.models.nba import (
    GameStatus,
    NBAGame,
    Prediction,
    Team,
)
from courtvision.services.nba_data import NBADataService


class TestPredictionEngine:
    """Tests for PredictionEngine."""

    @pytest.fixture
    def engine(self):
        return PredictionEngine(nba_data=NBADataService())

    def _make_game(self, game_id="TEST-001"):
        home = Team(
            id=1, name="Boston Celtics", abbreviation="BOS",
            conference="East", division="Atlantic",
            wins=64, losses=18, win_pct=0.780,
            points_per_game=120.6, points_allowed=109.2, net_rating=11.4,
        )
        away = Team(
            id=2, name="New York Knicks", abbreviation="NYK",
            conference="East", division="Atlantic",
            wins=50, losses=32, win_pct=0.610,
            points_per_game=112.3, points_allowed=108.7, net_rating=3.6,
        )
        from datetime import datetime, timezone, timedelta
        return NBAGame(
            id=game_id,
            home_team=home, away_team=away,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            is_playoff=True, playoff_round="First Round",
        )

    def test_initialization(self, engine):
        assert engine.nba is not None
        assert engine.qwen is not None

    def test_predict_game_sync(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert isinstance(prediction, Prediction)
        assert prediction.game_id == "TEST-001"
        assert 0 <= prediction.home_win_probability <= 1
        assert 0 <= prediction.away_win_probability <= 1
        assert prediction.predicted_winner in ["Boston Celtics", "New York Knicks"]

    def test_predict_game_caching(self, engine):
        game = self._make_game()
        p1 = engine.predict_game_sync(game)
        p2 = engine.predict_game_sync(game)
        assert p1.game_id == p2.game_id
        assert p1.home_win_probability == p2.home_win_probability

    def test_get_cached_prediction_exists(self, engine):
        game = self._make_game()
        engine.predict_game_sync(game)
        cached = engine.get_cached_prediction("TEST-001")
        assert cached is not None
        assert cached.game_id == "TEST-001"

    def test_get_cached_prediction_missing(self, engine):
        cached = engine.get_cached_prediction("NONEXISTENT")
        assert cached is None

    def test_stats_tracking(self, engine):
        game = self._make_game("STATS-001")
        assert engine.get_stats()["total_predictions_generated"] == 0
        engine.predict_game_sync(game)
        assert engine.get_stats()["total_predictions_generated"] == 1
        assert engine.get_stats()["cached_predictions"] == 1

    def test_multiple_predictions_different_games(self, engine):
        g1 = self._make_game("MULTI-001")
        g2 = self._make_game("MULTI-002")
        p1 = engine.predict_game_sync(g1)
        p2 = engine.predict_game_sync(g2)
        assert p1.game_id == "MULTI-001"
        assert p2.game_id == "MULTI-002"
        assert engine.get_stats()["total_predictions_generated"] == 2

    def test_prediction_has_factors(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert prediction.factors is not None
        assert 0 <= prediction.factors.team_form <= 100
        assert 0 <= prediction.factors.home_advantage <= 100

    def test_prediction_has_insights(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert isinstance(prediction.key_insights, list)

    def test_prediction_has_risk_assessment(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert isinstance(prediction.risk_assessment, str)
        assert len(prediction.risk_assessment) > 0

    def test_prediction_has_recommended_bet(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert isinstance(prediction.recommended_bet, str)

    def test_prediction_confidence_in_range(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert 0 <= prediction.confidence <= 1

    def test_prediction_total_points_reasonable(self, engine):
        game = self._make_game()
        prediction = engine.predict_game_sync(game)
        assert 150 <= prediction.predicted_total <= 300
