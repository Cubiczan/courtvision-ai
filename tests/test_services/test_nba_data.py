"""Tests for NBA data service."""

import pytest
from datetime import datetime, timezone, timedelta

from courtvision.models.nba import GameStatus, NBAGame, Team
from courtvision.services.nba_data import (
    EAST_TEAMS,
    NBADataService,
    PLAYOFF_GAMES,
    WEST_TEAMS,
)


class TestNBADataService:
    """Tests for NBADataService."""

    @pytest.fixture
    def service(self):
        return NBADataService()

    def test_service_initialization(self, service):
        assert len(service.games) > 0
        assert len(service.teams) == 16  # 8 East + 8 West

    def test_get_upcoming_games(self, service):
        games = service.get_upcoming_games()
        assert len(games) > 0
        for game in games:
            assert game.status == GameStatus.SCHEDULED

    def test_get_upcoming_games_with_limit(self, service):
        games = service.get_upcoming_games(limit=3)
        assert len(games) <= 3

    def test_get_live_games(self, service):
        games = service.get_live_games()
        assert isinstance(games, list)
        for game in games:
            assert game.status == GameStatus.LIVE

    def test_get_finished_games(self, service):
        games = service.get_finished_games()
        assert len(games) > 0
        for game in games:
            assert game.status == GameStatus.FINISHED

    def test_get_game_by_id_found(self, service):
        game = service.get_game_by_id("NBA-2025-PO-G101")
        assert game is not None
        assert game.status == GameStatus.FINISHED
        assert game.home_score == 112

    def test_get_game_by_id_not_found(self, service):
        game = service.get_game_by_id("NON-EXISTENT")
        assert game is None

    def test_get_team_by_id(self, service):
        team = service.get_team_by_id(1)
        assert team is not None
        assert team.name == "Boston Celtics"
        assert team.abbreviation == "BOS"

    def test_get_team_by_id_not_found(self, service):
        team = service.get_team_by_id(999)
        assert team is None

    def test_get_team_players_existing(self, service):
        players = service.get_team_players(1)  # Celtics
        assert len(players) > 0
        assert players[0].name == "Jayson Tatum"

    def test_get_team_players_missing(self, service):
        players = service.get_team_players(999)
        assert players == []

    def test_get_playoff_teams(self, service):
        playoffs = service.get_playoff_teams()
        assert "east" in playoffs
        assert "west" in playoffs
        assert len(playoffs["east"]) == 8
        assert len(playoffs["west"]) == 8

    def test_get_game_context(self, service):
        game = service.get_game_by_id("NBA-2025-PO-G101")
        assert game is not None
        context = service.get_game_context(game)
        assert isinstance(context, str)
        assert len(context) > 0

    def test_get_all_games(self, service):
        games = service.get_all_games()
        assert len(games) == len(PLAYOFF_GAMES)

    def test_add_game(self, service):
        new_game = NBAGame(
            id="CUSTOM-001",
            home_team=Team(id=1, name="A", abbreviation="A", conference="E", division="D"),
            away_team=Team(id=2, name="B", abbreviation="B", conference="E", division="D"),
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        initial_count = len(service.get_all_games())
        service.add_game(new_game)
        assert len(service.get_all_games()) == initial_count + 1

    def test_playoff_teams_data_integrity(self):
        for team in EAST_TEAMS:
            assert team.conference == "East"
            assert 0 < team.win_pct <= 1.0
            assert team.points_per_game > 0

        for team in WEST_TEAMS:
            assert team.conference == "West"
            assert 0 < team.win_pct <= 1.0
            assert team.points_per_game > 0

    def test_all_teams_have_required_fields(self):
        for team in EAST_TEAMS + WEST_TEAMS:
            assert team.id > 0
            assert team.name != ""
            assert team.abbreviation != ""
            assert team.conference in ("East", "West")
            assert team.division != ""

    def test_finished_games_have_scores(self, service):
        for game in service.get_finished_games():
            assert game.home_score is not None
            assert game.away_score is not None
            assert game.home_score != game.away_score  # No ties in basketball

    def test_upcoming_games_have_future_dates(self, service):
        now = datetime.now(timezone.utc)
        for game in service.get_upcoming_games():
            assert game.scheduled_at > now

    def test_scheduled_games_have_no_scores(self, service):
        for game in service.get_upcoming_games():
            assert game.home_score is None
            assert game.away_score is None

    def test_playoff_games_flagged(self, service):
        for game in service.get_all_games():
            if game.id.startswith("NBA-2025-PO"):
                assert game.is_playoff is True
