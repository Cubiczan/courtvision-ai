"""Tests for Qwen LLM client."""

import json
import pytest

from courtvision.services.qwen_client import (
    DEFAULT_MODEL,
    QwenClient,
    SYSTEM_PROMPT,
)


class TestQwenClient:
    """Tests for QwenClient."""

    @pytest.fixture
    def client(self):
        return QwenClient(api_key="test-key", model="qwen-plus")

    def test_initialization(self, client):
        assert client.model == "qwen-plus"
        assert client.api_key == "test-key"
        assert "dashscope" in client.base_url

    def test_default_model(self):
        assert DEFAULT_MODEL == "qwen-plus"

    def test_system_prompt_exists(self):
        assert len(SYSTEM_PROMPT) > 100
        assert "NBA" in SYSTEM_PROMPT
        assert "prediction" in SYSTEM_PROMPT.lower()

    def test_build_prediction_messages(self, client):
        messages = client._build_prediction_messages(
            home_team="Boston Celtics", home_record="64-18",
            home_ppg=120.6, home_papg=109.2, home_net_rating=11.4, home_streak="W3",
            away_team="New York Knicks", away_record="50-32",
            away_ppg=112.3, away_papg=108.7, away_net_rating=3.6, away_streak="L1",
            context="Playoff Game 1",
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Boston Celtics" in messages[1]["content"]
        assert "New York Knicks" in messages[1]["content"]
        assert "Playoff Game 1" in messages[1]["content"]

    def test_build_prediction_messages_no_context(self, client):
        messages = client._build_prediction_messages(
            home_team="A", home_record="50-32", home_ppg=110.0, home_papg=105.0,
            home_net_rating=5.0, home_streak="W2",
            away_team="B", away_record="45-37", away_ppg=108.0, away_papg=107.0,
            away_net_rating=1.0, away_streak="L3",
        )
        assert "Regular season game" in messages[1]["content"]

    def test_parse_json_response_valid(self, client):
        raw = json.dumps({
            "home_win_probability": 0.65,
            "away_win_probability": 0.35,
            "predicted_total": 218.5,
            "over_probability": 0.55,
            "predicted_winner": "Boston Celtics",
            "confidence": 0.72,
            "factors": {
                "team_form": 75.0, "home_advantage": 65.0,
                "player_impact": 80.0, "matchup_history": 55.0,
                "rest_advantage": 50.0, "injury_factor": 40.0,
                "market_sentiment": 60.0,
            },
            "key_insights": ["Home advantage"],
            "risk_assessment": "Low",
            "recommended_bet": "moneyline",
        })
        result = client._parse_json_response(raw)
        assert result["home_win_probability"] == 0.65
        assert result["predicted_winner"] == "Boston Celtics"

    def test_parse_json_response_with_code_fence(self, client):
        raw = '```json\n{"home_win_probability": 0.60}\n```'
        result = client._parse_json_response(raw)
        assert result["home_win_probability"] == 0.60

    def test_parse_json_response_invalid(self, client):
        result = client._parse_json_response("not json at all")
        assert result["confidence"] == 0.10
        assert "parsing" in result["key_insights"][0].lower()

    def test_parse_json_response_empty(self, client):
        result = client._parse_json_response("")
        assert result["confidence"] == 0.10

    def test_generate_fallback_prediction(self, client):
        messages = [
            {"role": "system", "content": "You are an NBA analyst."},
            {"role": "user", "content": "Home Team: Boston Celtics (64-18)\nAway Team: New York Knicks (50-32)"},
        ]
        result = client._generate_fallback_prediction(messages)
        assert "home_win_probability" in result
        assert "away_win_probability" in result
        assert 0 <= result["confidence"] <= 1
        assert result["factors"]["team_form"] == 50.0
        assert len(result["key_insights"]) >= 1

    def test_health_check_format(self, client):
        # We can't actually call the API without a real key, but we can test the format
        assert hasattr(client, "health_check")
        assert callable(client.health_check)

    def test_system_prompt_keywords(self):
        keywords = ["NBA", "team", "player", "prediction", "bet types"]
        for kw in keywords:
            assert kw.lower() in SYSTEM_PROMPT.lower()
