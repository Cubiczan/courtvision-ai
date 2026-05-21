"""FastAPI routes for CourtVision AI backend."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from courtvision.engines.prediction import PredictionEngine
from courtvision.models.nba import (
    GameStatus,
    HealthResponse,
    LeaderboardEntry,
    MarketStatus,
    NBAGame,
    Prediction,
    PredictionTier,
    PredictorStats,
)
from courtvision.services.azuro_service import AzuroService
from courtvision.services.nba_data import NBADataService

logger = logging.getLogger(__name__)

# --- Router ---

router = APIRouter(prefix="/api/v1", tags=["CourtVision AI"])

# --- Service instances (singleton per request via dependency injection) ---

_nba_data: Optional[NBADataService] = None
_azuro_service: Optional[AzuroService] = None
_prediction_engine: Optional[PredictionEngine] = None
_start_time = time.time()


def get_nba_data() -> NBADataService:
    global _nba_data
    if _nba_data is None:
        _nba_data = NBADataService()
    return _nba_data


def get_azuro_service() -> AzuroService:
    global _azuro_service
    if _azuro_service is None:
        _azuro_service = AzuroService()
    return _azuro_service


def get_prediction_engine() -> PredictionEngine:
    global _prediction_engine
    if _prediction_engine is None:
        _prediction_engine = PredictionEngine(
            nba_data=get_nba_data(),
        )
    return _prediction_engine


# --- Health ---

@router.get("/health", response_model=HealthResponse)
async def health_check(
    engine: PredictionEngine = Depends(get_prediction_engine),
):
    """Check service health and uptime."""
    stats = engine.get_stats()
    return HealthResponse(
        uptime_seconds=round(time.time() - _start_time, 2),
        games_analyzed=stats["cached_predictions"],
        predictions_generated=stats["total_predictions_generated"],
    )


# --- Games ---

@router.get("/games/upcoming", response_model=list[NBAGame])
async def get_upcoming_games(
    limit: int = Query(default=10, ge=1, le=50),
    nba: NBADataService = Depends(get_nba_data),
):
    """List upcoming NBA games with schedule info."""
    games = nba.get_upcoming_games(limit=limit)
    if not games:
        raise HTTPException(status_code=404, detail="No upcoming games found")
    return games


@router.get("/games/live", response_model=list[NBAGame])
async def get_live_games(
    nba: NBADataService = Depends(get_nba_data),
):
    """Get currently live NBA games."""
    games = nba.get_live_games()
    return games


@router.get("/games/finished", response_model=list[NBAGame])
async def get_finished_games(
    limit: int = Query(default=10, ge=1, le=50),
    nba: NBADataService = Depends(get_nba_data),
):
    """Get recently finished games."""
    return nba.get_finished_games(limit=limit)


@router.get("/games/{game_id}", response_model=NBAGame)
async def get_game(
    game_id: str,
    nba: NBADataService = Depends(get_nba_data),
):
    """Get detailed game information."""
    game = nba.get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    return game


# --- Predictions ---

@router.get("/predictions/game/{game_id}", response_model=Prediction)
async def get_game_prediction(
    game_id: str,
    nba: NBADataService = Depends(get_nba_data),
    engine: PredictionEngine = Depends(get_prediction_engine),
):
    """Get AI prediction for a specific game."""
    game = nba.get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    try:
        prediction = await engine.predict_game(game)
        return prediction
    except Exception as e:
        logger.error("Failed to generate prediction for game %s: %s", game_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction generation failed: {e}",
        )


@router.post("/predictions/analyze", response_model=Prediction)
async def analyze_matchup(
    engine: PredictionEngine = Depends(get_prediction_engine),
    nba: NBADataService = Depends(get_nba_data),
    home_team_id: int = Query(..., description="Home team ID"),
    away_team_id: int = Query(..., description="Away team ID"),
    context: str = Query(default="", description="Additional context"),
):
    """Get AI prediction for a custom matchup."""
    home = nba.get_team_by_id(home_team_id)
    away = nba.get_team_by_id(away_team_id)

    if not home:
        raise HTTPException(status_code=404, detail=f"Home team {home_team_id} not found")
    if not away:
        raise HTTPException(status_code=404, detail=f"Away team {away_team_id} not found")

    game = NBAGame(
        id=f"CUSTOM-{home_team_id}-{away_team_id}",
        home_team=home,
        away_team=away,
        scheduled_at=datetime.now(timezone.utc),
        is_playoff=False,
    )

    try:
        return await engine.predict_game(game)
    except Exception as e:
        logger.error("Failed to analyze matchup: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


# --- Markets ---

@router.get("/markets/active")
async def get_active_markets(
    azuro: AzuroService = Depends(get_azuro_service),
):
    """Get all active prediction markets on Polygon Amoy."""
    markets = azuro.get_active_markets()
    return {
        "markets": markets,
        "count": len(markets),
    }


@router.get("/markets/stats")
async def get_market_stats(
    azuro: AzuroService = Depends(get_azuro_service),
):
    """Get aggregate market statistics."""
    return azuro.get_market_stats()


@router.get("/markets/{market_id}")
async def get_market(
    market_id: int,
    azuro: AzuroService = Depends(get_azuro_service),
):
    """Get market details with odds and liquidity."""
    market = azuro.get_market(market_id)
    if not market:
        raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
    return market


@router.post("/markets/create")
async def create_market(
    azuro: AzuroService = Depends(get_azuro_service),
    nba: NBADataService = Depends(get_nba_data),
    game_id: str = Query(..., description="NBA game ID"),
):
    """Create a prediction market for an NBA game (admin)."""
    game = nba.get_game_by_id(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    market = azuro.create_market(
        game_id=game.id,
        home_team=game.home_team.name,
        away_team=game.away_team.name,
        scheduled_tipoff=game.scheduled_at,
    )
    return market


# --- Leaderboard ---

@router.get("/stats/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(limit: int = Query(default=10, ge=1, le=100)):
    """Get top predictors leaderboard (demo)."""
    # Demo leaderboard data
    demo_entries = [
        LeaderboardEntry(
            rank=1,
            user_address="0x1234...abcd",
            accuracy=0.72,
            total_predictions=45,
            correct_predictions=32,
            best_streak=8,
            tier=PredictionTier.GOLD,
        ),
        LeaderboardEntry(
            rank=2,
            user_address="0x5678...efgh",
            accuracy=0.68,
            total_predictions=38,
            correct_predictions=26,
            best_streak=6,
            tier=PredictionTier.SILVER,
        ),
        LeaderboardEntry(
            rank=3,
            user_address="0x9abc...ijkl",
            accuracy=0.65,
            total_predictions=52,
            correct_predictions=34,
            best_streak=5,
            tier=PredictionTier.GOLD,
        ),
        LeaderboardEntry(
            rank=4,
            user_address="0xdef0...mnop",
            accuracy=0.61,
            total_predictions=28,
            correct_predictions=17,
            best_streak=4,
            tier=PredictionTier.SILVER,
        ),
        LeaderboardEntry(
            rank=5,
            user_address="0x1111...2222",
            accuracy=0.58,
            total_predictions=60,
            correct_predictions=35,
            best_streak=7,
            tier=PredictionTier.PLATINUM,
        ),
    ]
    return demo_entries[:limit]


# --- Prediction History ---

@router.get("/predictions/history")
async def get_prediction_history(
    limit: int = Query(default=10, ge=1, le=50),
    engine: PredictionEngine = Depends(get_prediction_engine),
):
    """Get recent predictions (demo)."""
    return {
        "predictions": list(engine._prediction_cache.values())[-limit:],
        "total": len(engine._prediction_cache),
    }
