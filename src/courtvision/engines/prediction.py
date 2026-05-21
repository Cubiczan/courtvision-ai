"""AI prediction engine that combines Qwen LLM analysis with market data."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from courtvision.models.nba import (
    NBAGame,
    Prediction,
    PredictionFactors,
)
from courtvision.services.nba_data import NBADataService
from courtvision.services.qwen_client import QwenClient

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Combines Qwen LLM analysis with NBA data for game predictions."""

    def __init__(
        self,
        qwen_client: Optional[QwenClient] = None,
        nba_data: Optional[NBADataService] = None,
    ) -> None:
        self.qwen = qwen_client or QwenClient()
        self.nba = nba_data or NBADataService()
        self._prediction_cache: dict[str, Prediction] = {}
        self._total_generated = 0

    async def predict_game(self, game: NBAGame) -> Prediction:
        """Generate an AI prediction for an NBA game."""
        # Check cache first
        if game.id in self._prediction_cache:
            cached = self._prediction_cache[game.id]
            # Refresh if cached prediction is older than 1 hour
            age = (datetime.utcnow() - cached.generated_at).total_seconds()
            if age < 3600:
                return cached

        # Get game context
        context = self.nba.get_game_context(game)

        # Call Qwen LLM
        llm_result = await self.qwen.predict_async(
            home_team=game.home_team.name,
            home_record=f"{game.home_team.wins}-{game.home_team.losses}",
            home_ppg=game.home_team.points_per_game,
            home_papg=game.home_team.points_allowed,
            home_net_rating=game.home_team.net_rating,
            home_streak=game.home_team.streak,
            away_team=game.away_team.name,
            away_record=f"{game.away_team.wins}-{game.away_team.losses}",
            away_ppg=game.away_team.points_per_game,
            away_papg=game.away_team.points_allowed,
            away_net_rating=game.away_team.net_rating,
            away_streak=game.away_team.streak,
            context=context,
        )

        # Build prediction
        factors = PredictionFactors(**llm_result.get("factors", {}))
        prediction = Prediction(
            game_id=game.id,
            home_team=game.home_team.name,
            away_team=game.away_team.name,
            predicted_winner=llm_result.get("predicted_winner", game.home_team.name),
            confidence=float(llm_result.get("confidence", 0.5)),
            home_win_probability=float(llm_result.get("home_win_probability", 0.5)),
            away_win_probability=float(llm_result.get("away_win_probability", 0.5)),
            predicted_total=float(llm_result.get("predicted_total", 220.0)),
            over_probability=float(llm_result.get("over_probability", 0.5)),
            factors=factors,
            key_insights=llm_result.get("key_insights", []),
            risk_assessment=llm_result.get("risk_assessment", "Unknown"),
            recommended_bet=llm_result.get("recommended_bet", "none"),
        )

        # Cache and return
        self._prediction_cache[game.id] = prediction
        self._total_generated += 1

        logger.info(
            "Prediction for %s: %s wins with %.1f%% confidence",
            game.display_name,
            prediction.predicted_winner,
            prediction.confidence * 100,
        )

        return prediction

    def predict_game_sync(self, game: NBAGame) -> Prediction:
        """Synchronous version of predict_game."""
        if game.id in self._prediction_cache:
            return self._prediction_cache[game.id]

        context = self.nba.get_game_context(game)
        llm_result = self.qwen.predict_sync(
            home_team=game.home_team.name,
            home_record=f"{game.home_team.wins}-{game.home_team.losses}",
            home_ppg=game.home_team.points_per_game,
            home_papg=game.home_team.points_allowed,
            home_net_rating=game.home_team.net_rating,
            home_streak=game.home_team.streak,
            away_team=game.away_team.name,
            away_record=f"{game.away_team.wins}-{game.away_team.losses}",
            away_ppg=game.away_team.points_per_game,
            away_papg=game.away_team.points_allowed,
            away_net_rating=game.away_team.net_rating,
            away_streak=game.away_team.streak,
            context=context,
        )

        factors = PredictionFactors(**llm_result.get("factors", {}))
        prediction = Prediction(
            game_id=game.id,
            home_team=game.home_team.name,
            away_team=game.away_team.name,
            predicted_winner=llm_result.get("predicted_winner", game.home_team.name),
            confidence=float(llm_result.get("confidence", 0.5)),
            home_win_probability=float(llm_result.get("home_win_probability", 0.5)),
            away_win_probability=float(llm_result.get("away_win_probability", 0.5)),
            predicted_total=float(llm_result.get("predicted_total", 220.0)),
            over_probability=float(llm_result.get("over_probability", 0.5)),
            factors=factors,
            key_insights=llm_result.get("key_insights", []),
            risk_assessment=llm_result.get("risk_assessment", "Unknown"),
            recommended_bet=llm_result.get("recommended_bet", "none"),
        )

        self._prediction_cache[game.id] = prediction
        self._total_generated += 1
        return prediction

    def get_cached_prediction(self, game_id: str) -> Optional[Prediction]:
        """Get a cached prediction if available."""
        return self._prediction_cache.get(game_id)

    def get_stats(self) -> dict[str, int]:
        """Get prediction engine statistics."""
        return {
            "total_predictions_generated": self._total_generated,
            "cached_predictions": len(self._prediction_cache),
        }
