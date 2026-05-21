"""Pydantic v2 models for NBA games, predictions, and markets."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GameStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"


class Outcome(str, Enum):
    HOME_WIN = "home_win"
    AWAY_WIN = "away_win"
    DRAW = "draw"
    OVER = "over"
    UNDER = "under"


class MarketStatus(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class PredictionTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Team(BaseModel):
    """NBA team information."""
    id: int
    name: str
    abbreviation: str
    conference: str
    division: str
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    home_record: str = "0-0"
    away_record: str = "0-0"
    streak: str = ""
    points_per_game: float = 0.0
    points_allowed: float = 0.0
    net_rating: float = 0.0


class Player(BaseModel):
    """NBA player statistics."""
    id: int
    name: str
    team_id: int
    position: str
    games_played: int = 0
    minutes_per_game: float = 0.0
    points_per_game: float = 0.0
    rebounds_per_game: float = 0.0
    assists_per_game: float = 0.0
    steals_per_game: float = 0.0
    blocks_per_game: float = 0.0
    field_goal_pct: float = 0.0
    three_point_pct: float = 0.0
    free_throw_pct: float = 0.0
    status: str = "active"


class NBAGame(BaseModel):
    """NBA game with full context for prediction."""
    id: str
    home_team: Team
    away_team: Team
    scheduled_at: datetime
    status: GameStatus = GameStatus.SCHEDULED
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: str = ""
    broadcast: str = ""
    season: str = "2024-25"
    is_playoff: bool = False
    playoff_round: Optional[str] = None

    @property
    def display_name(self) -> str:
        return f"{self.away_team.abbreviation} @ {self.home_team.abbreviation}"


class PredictionFactors(BaseModel):
    """AI analysis factors for a prediction."""
    team_form: float = Field(description="Team recent form score (0-100)", ge=0, le=100)
    home_advantage: float = Field(description="Home court advantage factor (0-100)", ge=0, le=100)
    player_impact: float = Field(description="Key player impact score (0-100)", ge=0, le=100)
    matchup_history: float = Field(description="Historical matchup factor (0-100)", ge=0, le=100)
    rest_advantage: float = Field(description="Rest days advantage factor (0-100)", ge=0, le=100)
    injury_factor: float = Field(description="Injury impact factor (0-100)", ge=0, le=100)
    market_sentiment: float = Field(description="Betting market sentiment (0-100)", ge=0, le=100)


class Prediction(BaseModel):
    """AI-generated prediction for an NBA game."""
    game_id: str
    home_team: str
    away_team: str
    predicted_winner: str
    confidence: float = Field(description="Confidence level 0-1", ge=0.0, le=1.0)
    home_win_probability: float = Field(description="Home win probability 0-1", ge=0.0, le=1.0)
    away_win_probability: float = Field(description="Away win probability 0-1", ge=0.0, le=1.0)
    predicted_total: float = Field(description="Predicted total points", ge=100.0, le=300.0)
    over_probability: float = Field(description="Over probability 0-1", ge=0.0, le=1.0)
    factors: PredictionFactors
    key_insights: list[str] = Field(default_factory=list)
    risk_assessment: str = ""
    recommended_bet: str = ""
    model_version: str = "courtvision-v1.0"
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("confidence", "home_win_probability", "away_win_probability", "over_probability")
    @classmethod
    def validate_probability(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Probability must be between 0 and 1")
        return round(v, 4)


class Market(BaseModel):
    """On-chain prediction market."""
    market_id: int
    game_id: str
    home_team: str
    away_team: str
    status: MarketStatus
    home_odds: float
    away_odds: float
    total_liquidity: float
    home_pool: float = 0.0
    away_pool: float = 0.0
    scheduled_tipoff: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    chain_id: int = 80002
    protocol: str = "azuro"


class Bet(BaseModel):
    """User bet on a prediction market."""
    id: str
    market_id: int
    user_address: str
    outcome: Outcome
    amount: float
    odds_at_bet: float
    potential_payout: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"


class PredictorStats(BaseModel):
    """User prediction statistics and tier."""
    user_address: str
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    current_streak: int = 0
    best_streak: int = 0
    tier: PredictionTier = PredictionTier.BRONZE
    pending_rewards: float = 0.0
    total_rewards_claimed: float = 0.0


class LeaderboardEntry(BaseModel):
    """Leaderboard entry for top predictors."""
    rank: int
    user_address: str
    accuracy: float
    total_predictions: int
    correct_predictions: int
    best_streak: int
    tier: PredictionTier


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    chain: str = "polygon-amoy"
    protocol: str = "azuro"
    uptime_seconds: float = 0.0
    games_analyzed: int = 0
    predictions_generated: int = 0
