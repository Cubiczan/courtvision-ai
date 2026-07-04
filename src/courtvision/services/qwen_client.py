"""Qwen LLM client for CourtVision AI using Alibaba Cloud DashScope."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx
from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)

# Default model
DEFAULT_MODEL = "qwen-plus"

# System prompt for NBA predictions
SYSTEM_PROMPT = """You are CourtVision AI, an expert NBA analyst and prediction engine. 
You have deep knowledge of NBA teams, players, statistics, and game dynamics. 
Your role is to analyze upcoming NBA games and provide data-driven predictions.

When analyzing a game, consider:
1. Team form and recent performance (last 10 games)
2. Home/away court advantage
3. Key player matchups and availability (injuries)
4. Head-to-head records
5. Pace of play and scoring trends
6. Rest days and schedule fatigue
7. Playoff implications and motivation
8. Advanced metrics (net rating, offensive/defensive efficiency)

Always respond with structured analysis including win probabilities, 
confidence levels, and recommended bet types. Be honest about uncertainty."""

PREDICTION_PROMPT_TEMPLATE = """Analyze the following NBA game and provide a detailed prediction:

**Home Team**: {home_team} ({home_record})
- Points per game: {home_ppg}
- Points allowed: {home_papg}
- Net rating: {home_net_rating}
- Current streak: {home_streak}

**Away Team**: {away_team} ({away_record})
- Points per game: {away_ppg}
- Points allowed: {away_papg}
- Net rating: {away_net_rating}
- Current streak: {away_streak}

**Game Context**: {context}

Provide your analysis in this exact JSON format:
{{
    "home_win_probability": <float 0.0-1.0>,
    "away_win_probability": <float 0.0-1.0>,
    "predicted_total": <float total points>,
    "over_probability": <float 0.0-1.0>,
    "predicted_winner": "<home_team or away_team>",
    "confidence": <float 0.0-1.0>,
    "factors": {{
        "team_form": <float 0-100>,
        "home_advantage": <float 0-100>,
        "player_impact": <float 0-100>,
        "matchup_history": <float 0-100>,
        "rest_advantage": <float 0-100>,
        "injury_factor": <float 0-100>,
        "market_sentiment": <float 0-100>
    }},
    "key_insights": ["<insight1>", "<insight2>", "<insight3>"],
    "risk_assessment": "<string describing risk level>",
    "recommended_bet": "<moneyline/spread/over_under>"
}}

Only return valid JSON. Do not include any text outside the JSON object."""


class QwenClient:
    """Async-capable client for Qwen LLM via DashScope."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        fallback_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.model = model

        # Primary: China region
        self.base_url = base_url or os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        # Fallback: Singapore region
        self.fallback_url = fallback_url or os.getenv(
            "DASHSCOPE_FALLBACK_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )

        # Initialize OpenAI-compatible clients only when a key is present.
        # Without a key the SDK raises at construction, which would break the
        # whole app in offline/demo/CI mode. Leaving these as None lets the
        # predict_* methods fall through to the heuristic fallback prediction.
        self.client: Optional[OpenAI] = None
        self.async_client: Optional[AsyncOpenAI] = None
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=30.0,
                )
                self.async_client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=30.0,
                )
            except Exception as e:  # noqa: BLE001 - never fail app startup on client init
                logger.warning("Could not initialize DashScope clients: %s", e)
        else:
            logger.info("No DASHSCOPE_API_KEY set; QwenClient will use heuristic fallback")

        logger.info(
            "QwenClient initialized: model=%s, base_url=%s, live=%s",
            self.model,
            self.base_url,
            self.client is not None,
        )

    def _build_prediction_messages(
        self,
        home_team: str,
        home_record: str,
        home_ppg: float,
        home_papg: float,
        home_net_rating: float,
        home_streak: str,
        away_team: str,
        away_record: str,
        away_ppg: float,
        away_papg: float,
        away_net_rating: float,
        away_streak: str,
        context: str = "",
    ) -> list[dict[str, str]]:
        """Build chat messages for a prediction request."""
        user_prompt = PREDICTION_PROMPT_TEMPLATE.format(
            home_team=home_team,
            home_record=home_record,
            home_ppg=home_ppg,
            home_papg=home_papg,
            home_net_rating=home_net_rating,
            home_streak=home_streak,
            away_team=away_team,
            away_record=away_record,
            away_ppg=away_ppg,
            away_papg=away_papg,
            away_net_rating=away_net_rating,
            away_streak=away_streak,
            context=context or "Regular season game",
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def predict_sync(
        self,
        home_team: str,
        home_record: str,
        home_ppg: float,
        home_papg: float,
        home_net_rating: float,
        home_streak: str,
        away_team: str,
        away_record: str,
        away_ppg: float,
        away_papg: float,
        away_net_rating: float,
        away_streak: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Synchronous prediction using Qwen LLM."""
        messages = self._build_prediction_messages(
            home_team, home_record, home_ppg, home_papg, home_net_rating, home_streak,
            away_team, away_record, away_ppg, away_papg, away_net_rating, away_streak,
            context,
        )
        if self.client is None:
            return self._generate_fallback_prediction(messages)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_json_response(content)
        except Exception as e:
            logger.error("Primary endpoint failed: %s", e)
            return self._fallback_predict(messages)

    async def predict_async(
        self,
        home_team: str,
        home_record: str,
        home_ppg: float,
        home_papg: float,
        home_net_rating: float,
        home_streak: str,
        away_team: str,
        away_record: str,
        away_ppg: float,
        away_papg: float,
        away_net_rating: float,
        away_streak: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Async prediction using Qwen LLM."""
        messages = self._build_prediction_messages(
            home_team, home_record, home_ppg, home_papg, home_net_rating, home_streak,
            away_team, away_record, away_ppg, away_papg, away_net_rating, away_streak,
            context,
        )
        if self.async_client is None:
            return self._generate_fallback_prediction(messages)
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_json_response(content)
        except Exception as e:
            logger.error("Async primary endpoint failed: %s", e)
            return self._fallback_predict(messages)

    def _fallback_predict(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Try the fallback endpoint when primary fails."""
        try:
            fallback_client = OpenAI(
                api_key=self.api_key,
                base_url=self.fallback_url,
                timeout=30.0,
            )
            response = fallback_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_json_response(content)
        except Exception as e:
            logger.error("Fallback endpoint also failed: %s", e)
            return self._generate_fallback_prediction(messages)

    def _generate_fallback_prediction(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Generate a heuristic-based prediction when LLM is unavailable."""
        user_msg = messages[-1]["content"] if messages else ""

        # Extract team names from the prompt
        home_team = "Home"
        away_team = "Away"
        for line in user_msg.split("\n"):
            if "Home Team" in line:
                home_team = line.split(":")[1].strip().split("(")[0].strip()
            elif "Away Team" in line:
                away_team = line.split(":")[1].strip().split("(")[0].strip()

        return {
            "home_win_probability": 0.55,
            "away_win_probability": 0.45,
            "predicted_total": 218.5,
            "over_probability": 0.50,
            "predicted_winner": home_team,
            "confidence": 0.40,
            "factors": {
                "team_form": 50.0,
                "home_advantage": 60.0,
                "player_impact": 50.0,
                "matchup_history": 50.0,
                "rest_advantage": 50.0,
                "injury_factor": 50.0,
                "market_sentiment": 50.0,
            },
            "key_insights": [
                "Home court advantage provides a slight edge",
                "Prediction generated using heuristic fallback (LLM unavailable)",
                "Consider waiting for AI-powered analysis before betting",
            ],
            "risk_assessment": "Moderate - fallback prediction with limited data",
            "recommended_bet": "moneyline",
        }

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON response from LLM, handling edge cases."""
        import json

        content = content.strip()
        # Remove markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            return {
                "home_win_probability": 0.50,
                "away_win_probability": 0.50,
                "predicted_total": 220.0,
                "over_probability": 0.50,
                "predicted_winner": "unknown",
                "confidence": 0.10,
                "factors": {
                    "team_form": 50.0,
                    "home_advantage": 50.0,
                    "player_impact": 50.0,
                    "matchup_history": 50.0,
                    "rest_advantage": 50.0,
                    "injury_factor": 50.0,
                    "market_sentiment": 50.0,
                },
                "key_insights": ["Error parsing AI response - using defaults"],
                "risk_assessment": "High - AI response parsing failed",
                "recommended_bet": "none",
            }

    def health_check(self) -> dict[str, Any]:
        """Check if the LLM service is accessible."""
        if self.client is None:
            return {
                "status": "offline",
                "model": self.model,
                "base_url": self.base_url,
                "detail": "no DASHSCOPE_API_KEY; running in heuristic/offline mode",
            }
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return {
                "status": "healthy",
                "model": self.model,
                "base_url": self.base_url,
                "response_received": bool(response.choices),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model,
                "base_url": self.base_url,
                "error": str(e),
            }
