"""Tests for NBA data models."""

import pytest
from datetime import datetime, timezone
from courtvision.models.nba import (
    Bet,
    GameStatus,
    HealthResponse,
    LeaderboardEntry,
    Market,
    MarketStatus,
    NBAGame,
    Outcome,
    Player,
    Prediction,
    PredictionFactors,
    PredictionTier,
    PredictorStats,
    Team,
)


class TestTeam:
    """Tests for Team model."""

    def test_create_team_basic(self):
        team = Team(
            id=1,
            name="Boston Celtics",
            abbreviation="BOS",
            conference="East",
            division="Atlantic",
        )
        assert team.id == 1
        assert team.name == "Boston Celtics"
        assert team.abbreviation == "BOS"
        assert team.wins == 0
        assert team.losses == 0
        assert team.win_pct == 0.0

    def test_create_team_full(self):
        team = Team(
            id=1, name="Boston Celtics", abbreviation="BOS",
            conference="East", division="Atlantic",
            wins=64, losses=18, win_pct=0.780,
            home_record="37-4", away_record="27-14",
            streak="W3", points_per_game=120.6,
            points_allowed=109.2, net_rating=11.4,
        )
        assert team.wins == 64
        assert team.losses == 18
        assert team.win_pct == 0.780
        assert team.home_record == "37-4"
        assert team.away_record == "27-14"
        assert team.streak == "W3"
        assert team.points_per_game == 120.6
        assert team.net_rating == 11.4

    def test_team_defaults(self):
        team = Team(id=1, name="Test", abbreviation="TST", conference="E", division="D")
        assert team.points_per_game == 0.0
        assert team.net_rating == 0.0
        assert team.home_record == "0-0"
        assert team.away_record == "0-0"
        assert team.streak == ""


class TestPlayer:
    """Tests for Player model."""

    def test_create_player_basic(self):
        player = Player(id=101, name="Jayson Tatum", team_id=1, position="SF")
        assert player.id == 101
        assert player.name == "Jayson Tatum"
        assert player.position == "SF"
        assert player.games_played == 0
        assert player.status == "active"

    def test_create_player_full_stats(self):
        player = Player(
            id=101, name="Jayson Tatum", team_id=1, position="SF",
            games_played=74, points_per_game=27.4, rebounds_per_game=8.7,
            assists_per_game=5.5, field_goal_pct=0.463, three_point_pct=0.376,
        )
        assert player.points_per_game == 27.4
        assert player.rebounds_per_game == 8.7
        assert player.field_goal_pct == 0.463
        assert player.three_point_pct == 0.376

    def test_player_defaults(self):
        player = Player(id=1, name="Test", team_id=1, position="PG")
        assert player.minutes_per_game == 0.0
        assert player.steals_per_game == 0.0
        assert player.blocks_per_game == 0.0
        assert player.free_throw_pct == 0.0


class TestNBAGame:
    """Tests for NBAGame model."""

    def _make_teams(self):
        home = Team(id=1, name="Boston Celtics", abbreviation="BOS",
                    conference="East", division="Atlantic", wins=64, losses=18)
        away = Team(id=2, name="New York Knicks", abbreviation="NYK",
                    conference="East", division="Atlantic", wins=50, losses=32)
        return home, away

    def test_create_game_scheduled(self):
        home, away = self._make_teams()
        game = NBAGame(
            id="NBA-001",
            home_team=home, away_team=away,
            scheduled_at=datetime(2025, 5, 15, 19, 0, tzinfo=timezone.utc),
        )
        assert game.id == "NBA-001"
        assert game.status == GameStatus.SCHEDULED
        assert game.home_score is None
        assert game.is_playoff is False

    def test_create_game_playoff(self):
        home, away = self._make_teams()
        game = NBAGame(
            id="NBA-PO-001",
            home_team=home, away_team=away,
            scheduled_at=datetime(2025, 5, 15, 19, 0, tzinfo=timezone.utc),
            is_playoff=True, playoff_round="First Round",
        )
        assert game.is_playoff is True
        assert game.playoff_round == "First Round"

    def test_game_display_name(self):
        home, away = self._make_teams()
        game = NBAGame(
            id="NBA-001", home_team=home, away_team=away,
            scheduled_at=datetime(2025, 5, 15, tzinfo=timezone.utc),
        )
        assert game.display_name == "NYK @ BOS"

    def test_game_finished_with_scores(self):
        home, away = self._make_teams()
        game = NBAGame(
            id="NBA-002", home_team=home, away_team=away,
            scheduled_at=datetime(2025, 5, 14, tzinfo=timezone.utc),
            status=GameStatus.FINISHED, home_score=112, away_score=98,
        )
        assert game.home_score == 112
        assert game.away_score == 98

    def test_game_live(self):
        home, away = self._make_teams()
        game = NBAGame(
            id="NBA-LIVE", home_team=home, away_team=away,
            scheduled_at=datetime(2025, 5, 15, tzinfo=timezone.utc),
            status=GameStatus.LIVE, home_score=87, away_score=82,
        )
        assert game.status == GameStatus.LIVE
        assert game.home_score == 87


class TestPredictionFactors:
    """Tests for PredictionFactors model."""

    def test_create_factors(self):
        factors = PredictionFactors(
            team_form=75.0, home_advantage=65.0, player_impact=80.0,
            matchup_history=55.0, rest_advantage=50.0,
            injury_factor=40.0, market_sentiment=60.0,
        )
        assert factors.team_form == 75.0
        assert factors.home_advantage == 65.0

    def test_factors_bounds_validation(self):
        with pytest.raises(Exception):
            PredictionFactors(team_form=150.0)  # > 100

    def test_factors_negative_validation(self):
        with pytest.raises(Exception):
            PredictionFactors(team_form=-5.0)  # < 0

    def test_factors_defaults(self):
        factors = PredictionFactors(
            team_form=0.0, home_advantage=0.0, player_impact=0.0,
            matchup_history=0.0, rest_advantage=0.0,
            injury_factor=0.0, market_sentiment=0.0,
        )
        assert factors.team_form == 0.0
        assert factors.home_advantage == 0.0
        assert factors.market_sentiment == 0.0


class TestPrediction:
    """Tests for Prediction model."""

    def _make_factors(self):
        return PredictionFactors(
            team_form=75.0, home_advantage=65.0, player_impact=80.0,
            matchup_history=55.0, rest_advantage=50.0,
            injury_factor=40.0, market_sentiment=60.0,
        )

    def test_create_prediction(self):
        pred = Prediction(
            game_id="NBA-001",
            home_team="Boston Celtics",
            away_team="New York Knicks",
            predicted_winner="Boston Celtics",
            confidence=0.72,
            home_win_probability=0.65,
            away_win_probability=0.35,
            predicted_total=218.5,
            over_probability=0.55,
            factors=self._make_factors(),
            key_insights=["Home court advantage", "Better recent form"],
        )
        assert pred.predicted_winner == "Boston Celtics"
        assert pred.confidence == 0.72
        assert len(pred.key_insights) == 2

    def test_prediction_confidence_bounds(self):
        with pytest.raises(Exception):
            Prediction(
                game_id="NBA-001", home_team="A", away_team="B",
                predicted_winner="A", confidence=1.5,
                home_win_probability=0.75, away_win_probability=0.25,
                predicted_total=220.0, over_probability=0.5,
                factors=self._make_factors(),
            )

    def test_prediction_probability_sum_validation(self):
        # Probabilities should individually be valid
        pred = Prediction(
            game_id="NBA-001", home_team="A", away_team="B",
            predicted_winner="A", confidence=0.5,
            home_win_probability=0.5, away_win_probability=0.5,
            predicted_total=220.0, over_probability=0.5,
            factors=self._make_factors(),
        )
        assert pred.home_win_probability == 0.5
        assert pred.away_win_probability == 0.5

    def test_prediction_defaults(self):
        pred = Prediction(
            game_id="NBA-001", home_team="A", away_team="B",
            predicted_winner="A", confidence=0.0,
            home_win_probability=0.5, away_win_probability=0.5,
            predicted_total=220.0, over_probability=0.5,
            factors=self._make_factors(),
        )
        assert pred.confidence == 0.0
        assert pred.risk_assessment == ""
        assert pred.recommended_bet == ""
        assert pred.model_version == "courtvision-v1.0"

    def test_prediction_key_insights_default_empty(self):
        pred = Prediction(
            game_id="NBA-001", home_team="A", away_team="B",
            predicted_winner="A", confidence=0.5,
            home_win_probability=0.5, away_win_probability=0.5,
            predicted_total=220.0, over_probability=0.5,
            factors=self._make_factors(),
        )
        assert pred.key_insights == []


class TestMarket:
    """Tests for Market model."""

    def test_create_market(self):
        market = Market(
            market_id=1, game_id="NBA-001",
            home_team="Boston Celtics", away_team="New York Knicks",
            status=MarketStatus.ACTIVE, home_odds=1.85, away_odds=2.10,
            total_liquidity=15000.0,
            scheduled_tipoff=datetime(2025, 5, 15, tzinfo=timezone.utc),
        )
        assert market.market_id == 1
        assert market.status == MarketStatus.ACTIVE
        assert market.chain_id == 80002
        assert market.protocol == "azuro"

    def test_market_defaults(self):
        market = Market(
            market_id=1, game_id="NBA-001",
            home_team="A", away_team="B",
            status=MarketStatus.ACTIVE, home_odds=1.9, away_odds=1.9,
            total_liquidity=0.0,
            scheduled_tipoff=datetime(2025, 5, 15, tzinfo=timezone.utc),
        )
        assert market.home_pool == 0.0
        assert market.away_pool == 0.0


class TestBet:
    """Tests for Bet model."""

    def test_create_bet(self):
        bet = Bet(
            id="bet-001", market_id=1, user_address="0x1234",
            outcome=Outcome.HOME_WIN, amount=100.0, odds_at_bet=1.85,
            potential_payout=185.0,
        )
        assert bet.outcome == Outcome.HOME_WIN
        assert bet.amount == 100.0
        assert bet.status == "pending"

    def test_bet_outcome_types(self):
        for outcome in Outcome:
            bet = Bet(
                id=f"bet-{outcome.value}", market_id=1,
                user_address="0x0", outcome=outcome, amount=50.0,
                odds_at_bet=2.0, potential_payout=100.0,
            )
            assert bet.outcome == outcome


class TestPredictorStats:
    """Tests for PredictorStats model."""

    def test_create_stats_bronze(self):
        stats = PredictorStats(user_address="0x1234")
        assert stats.tier == PredictionTier.BRONZE
        assert stats.total_predictions == 0
        assert stats.accuracy == 0.0

    def test_create_stats_platinum(self):
        stats = PredictorStats(
            user_address="0x5678",
            total_predictions=60, correct_predictions=42,
            accuracy=0.70, current_streak=8, best_streak=12,
            tier=PredictionTier.PLATINUM, pending_rewards=150.0,
        )
        assert stats.tier == PredictionTier.PLATINUM
        assert stats.best_streak == 12


class TestLeaderboardEntry:
    """Tests for LeaderboardEntry model."""

    def test_create_entry(self):
        entry = LeaderboardEntry(
            rank=1, user_address="0x1234", accuracy=0.72,
            total_predictions=45, correct_predictions=32,
            best_streak=8, tier=PredictionTier.GOLD,
        )
        assert entry.rank == 1
        assert entry.tier == PredictionTier.GOLD


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_health_defaults(self):
        health = HealthResponse()
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.chain == "polygon-amoy"
        assert health.protocol == "azuro"

    def test_health_with_data(self):
        health = HealthResponse(
            uptime_seconds=3600.5,
            games_analyzed=15,
            predictions_generated=12,
        )
        assert health.uptime_seconds == 3600.5
        assert health.games_analyzed == 15
