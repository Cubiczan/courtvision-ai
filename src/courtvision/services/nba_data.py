"""NBA data service with demo playoff data for CourtVision AI."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from courtvision.models.nba import (
    GameStatus,
    NBAGame,
    Player,
    Team,
)

logger = logging.getLogger(__name__)

# --- 2025 NBA Playoff Teams Demo Data ---

EAST_TEAMS = [
    Team(id=1, name="Boston Celtics", abbreviation="BOS", conference="East", division="Atlantic",
         wins=64, losses=18, win_pct=0.780, home_record="37-4", away_record="27-14",
         streak="W3", points_per_game=120.6, points_allowed=109.2, net_rating=11.4),
    Team(id=2, name="New York Knicks", abbreviation="NYK", conference="East", division="Atlantic",
         wins=50, losses=32, win_pct=0.610, home_record="29-12", away_record="21-20",
         streak="W1", points_per_game=112.3, points_allowed=108.7, net_rating=3.6),
    Team(id=3, name="Cleveland Cavaliers", abbreviation="CLE", conference="East", division="Central",
         wins=64, losses=18, win_pct=0.780, home_record="35-6", away_record="29-12",
         streak="W5", points_per_game=115.8, points_allowed=106.3, net_rating=9.5),
    Team(id=4, name="Indiana Pacers", abbreviation="IND", conference="East", division="Central",
         wins=47, losses=35, win_pct=0.573, home_record="28-13", away_record="19-22",
         streak="L1", points_per_game=118.4, points_allowed=115.2, net_rating=3.2),
    Team(id=5, name="Milwaukee Bucks", abbreviation="MIL", conference="East", division="Central",
         wins=49, losses=33, win_pct=0.597, home_record="30-11", away_record="19-22",
         streak="W2", points_per_game=116.1, points_allowed=112.5, net_rating=3.6),
    Team(id=6, name="Orlando Magic", abbreviation="ORL", conference="East", division="Southeast",
         wins=47, losses=35, win_pct=0.573, home_record="29-12", away_record="18-23",
         streak="L2", points_per_game=106.8, points_allowed=103.1, net_rating=3.7),
    Team(id=7, name="Miami Heat", abbreviation="MIA", conference="East", division="Southeast",
         wins=46, losses=36, win_pct=0.561, home_record="26-15", away_record="20-21",
         streak="W1", points_per_game=110.2, points_allowed=108.9, net_rating=1.3),
    Team(id=8, name="Detroit Pistons", abbreviation="DET", conference="East", division="Central",
         wins=36, losses=46, win_pct=0.439, home_record="23-18", away_record="13-28",
         streak="L3", points_per_game=107.4, points_allowed=110.8, net_rating=-3.4),
]

WEST_TEAMS = [
    Team(id=9, name="Oklahoma City Thunder", abbreviation="OKC", conference="West", division="Northwest",
         wins=68, losses=14, win_pct=0.829, home_record="38-3", away_record="30-11",
         streak="W7", points_per_game=120.1, points_allowed=104.8, net_rating=15.3),
    Team(id=10, name="Denver Nuggets", abbreviation="DEN", conference="West", division="Northwest",
         wins=57, losses=25, win_pct=0.695, home_record="34-7", away_record="23-18",
         streak="W2", points_per_game=115.7, points_allowed=110.2, net_rating=5.5),
    Team(id=11, name="Minnesota Timberwolves", abbreviation="MIN", conference="West", division="Northwest",
         wins=56, losses=26, win_pct=0.683, home_record="33-8", away_record="23-18",
         streak="L1", points_per_game=110.4, points_allowed=106.1, net_rating=4.3),
    Team(id=12, name="Los Angeles Lakers", abbreviation="LAL", conference="West", division="Pacific",
         wins=47, losses=35, win_pct=0.573, home_record="28-13", away_record="19-22",
         streak="W4", points_per_game=112.8, points_allowed=109.6, net_rating=3.2),
    Team(id=13, name="Memphis Grizzlies", abbreviation="MEM", conference="West", division="Southwest",
         wins=49, losses=33, win_pct=0.597, home_record="30-11", away_record="19-22",
         streak="W1", points_per_game=114.6, points_allowed=111.3, net_rating=3.3),
    Team(id=14, name="Golden State Warriors", abbreviation="GSW", conference="West", division="Pacific",
         wins=48, losses=34, win_pct=0.585, home_record="29-12", away_record="19-22",
         streak="L1", points_per_game=116.5, points_allowed=112.1, net_rating=4.4),
    Team(id=15, name="Houston Rockets", abbreviation="HOU", conference="West", division="Southwest",
         wins=52, losses=30, win_pct=0.634, home_record="31-10", away_record="21-20",
         streak="W3", points_per_game=109.8, points_allowed=105.2, net_rating=4.6),
    Team(id=16, name="Los Angeles Clippers", abbreviation="LAC", conference="West", division="Pacific",
         wins=43, losses=39, win_pct=0.524, home_record="26-15", away_record="17-24",
         streak="L2", points_per_game=107.9, points_allowed=108.4, net_rating=-0.5),
]

ALL_TEAMS = {t.id: t for t in EAST_TEAMS + WEST_TEAMS}

# --- Demo Playoff Games ---

def _generate_playoff_games() -> list[NBAGame]:
    """Generate 2025 NBA Playoff first-round games as demo data."""
    now = datetime.now(timezone.utc)
    games: list[NBAGame] = []

    # Eastern Conference - Round 1 matchups
    east_matchups = [
        (1, 8, "Eastern Conference First Round - Game 1"),
        (2, 7, "Eastern Conference First Round - Game 2"),
        (3, 6, "Eastern Conference First Round - Game 3"),
        (4, 5, "Eastern Conference First Round - Game 4"),
    ]

    # Western Conference - Round 1 matchups
    west_matchups = [
        (9, 16, "Western Conference First Round - Game 1"),
        (10, 15, "Western Conference First Round - Game 2"),
        (11, 14, "Western Conference First Round - Game 3"),
        (12, 13, "Western Conference First Round - Game 4"),
    ]

    for i, (home_id, away_id, context) in enumerate(east_matchups + west_matchups):
        tipoff = now + timedelta(hours=24 * (i + 1))
        game = NBAGame(
            id=f"NBA-2025-PO-G{i+1:03d}",
            home_team=ALL_TEAMS[home_id],
            away_team=ALL_TEAMS[away_id],
            scheduled_at=tipoff,
            status=GameStatus.SCHEDULED,
            venue=f"{ALL_TEAMS[home_id].name} Arena",
            is_playoff=True,
            playoff_round="First Round",
        )
        games.append(game)

    # Add some "recently finished" games for history
    finished_games = [
        NBAGame(
            id="NBA-2025-PO-G101",
            home_team=ALL_TEAMS[1],
            away_team=ALL_TEAMS[8],
            scheduled_at=now - timedelta(hours=6),
            status=GameStatus.FINISHED,
            home_score=112,
            away_score=98,
            is_playoff=True,
            playoff_round="First Round",
        ),
        NBAGame(
            id="NBA-2025-PO-G102",
            home_team=ALL_TEAMS[9],
            away_team=ALL_TEAMS[16],
            scheduled_at=now - timedelta(hours=3),
            status=GameStatus.FINISHED,
            home_score=105,
            away_score=99,
            is_playoff=True,
            playoff_round="First Round",
        ),
    ]
    games.extend(finished_games)

    # Add a live game
    live_game = NBAGame(
        id="NBA-2025-PO-G201",
        home_team=ALL_TEAMS[3],
        away_team=ALL_TEAMS[6],
        scheduled_at=now - timedelta(minutes=90),
        status=GameStatus.LIVE,
        home_score=87,
        away_score=82,
        is_playoff=True,
        playoff_round="First Round",
    )
    games.append(live_game)

    return games


# Cache the demo games
PLAYOFF_GAMES = _generate_playoff_games()

# --- Key players for each team ---
KEY_PLAYERS: dict[int, list[Player]] = {
    1: [Player(id=101, name="Jayson Tatum", team_id=1, position="SF", games_played=74,
               points_per_game=27.4, rebounds_per_game=8.7, assists_per_game=5.5,
               field_goal_pct=0.463, three_point_pct=0.376)],
    3: [Player(id=103, name="Donovan Mitchell", team_id=3, position="SG", games_played=65,
               points_per_game=26.6, rebounds_per_game=5.1, assists_per_game=6.1,
               field_goal_pct=0.462, three_point_pct=0.382)],
    9: [Player(id=109, name="Shai Gilgeous-Alexander", team_id=9, position="PG", games_played=78,
               points_per_game=32.5, rebounds_per_game=5.5, assists_per_game=6.3,
               field_goal_pct=0.535, three_point_pct=0.353)],
    10: [Player(id=110, name="Nikola Jokic", team_id=10, position="C", games_played=70,
                points_per_game=26.4, rebounds_per_game=12.4, assists_per_game=9.0,
                field_goal_pct=0.583, three_point_pct=0.354)],
}


class NBADataService:
    """Service for accessing NBA game and player data."""

    def __init__(self) -> None:
        self.games = PLAYOFF_GAMES
        self.teams = ALL_TEAMS
        self.players = KEY_PLAYERS

    def get_upcoming_games(self, limit: int = 10) -> list[NBAGame]:
        """Get scheduled upcoming NBA games."""
        now = datetime.now(timezone.utc)
        return [
            g for g in self.games
            if g.status == GameStatus.SCHEDULED and g.scheduled_at > now
        ][:limit]

    def get_live_games(self) -> list[NBAGame]:
        """Get currently live NBA games."""
        return [g for g in self.games if g.status == GameStatus.LIVE]

    def get_finished_games(self, limit: int = 10) -> list[NBAGame]:
        """Get recently finished games."""
        return [g for g in self.games if g.status == GameStatus.FINISHED][:limit]

    def get_game_by_id(self, game_id: str) -> Optional[NBAGame]:
        """Get a specific game by ID."""
        for g in self.games:
            if g.id == game_id:
                return g
        return None

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get a team by ID."""
        return self.teams.get(team_id)

    def get_team_players(self, team_id: int) -> list[Player]:
        """Get players for a team."""
        return self.players.get(team_id, [])

    def get_playoff_teams(self) -> dict[str, list[Team]]:
        """Get all playoff teams grouped by conference."""
        return {
            "east": [t for t in EAST_TEAMS],
            "west": [t for t in WEST_TEAMS],
        }

    def get_game_context(self, game: NBAGame) -> str:
        """Generate context string for a game (for LLM prediction)."""
        context_parts = []

        if game.is_playoff:
            context_parts.append(f"{game.playoff_round} - {game.home_team.name} vs {game.away_team.name}")

        context_parts.append(f"Venue: {game.venue}")
        context_parts.append(f"Broadcast: {game.broadcast}")

        # Check key players
        home_players = self.get_team_players(game.home_team.id)
        if home_players:
            best = max(home_players, key=lambda p: p.points_per_game)
            context_parts.append(f"Home key player: {best.name} ({best.points_per_game} PPG)")

        away_players = self.get_team_players(game.away_team.id)
        if away_players:
            best = max(away_players, key=lambda p: p.points_per_game)
            context_parts.append(f"Away key player: {best.name} ({best.points_per_game} PPG)")

        return ". ".join(context_parts)

    def get_all_games(self) -> list[NBAGame]:
        """Get all games (for testing)."""
        return self.games

    def add_game(self, game: NBAGame) -> None:
        """Add a game to the service (for testing)."""
        self.games.append(game)
