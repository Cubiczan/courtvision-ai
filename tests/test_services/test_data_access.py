"""Tests for the three-tier data-access layer (live -> cache -> mock)."""

import time

import pytest

from courtvision.services.data_access import (
    DataAccessLayer,
    is_offline,
)


class TestOfflineDetection:
    def test_no_key_means_offline(self, monkeypatch):
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        for flag in ("COURTVISION_OFFLINE", "COURTVISION_MOCK", "OFFLINE", "MOCK"):
            monkeypatch.delenv(flag, raising=False)
        assert is_offline() is True

    def test_key_present_means_online(self, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
        for flag in ("COURTVISION_OFFLINE", "COURTVISION_MOCK", "OFFLINE", "MOCK"):
            monkeypatch.delenv(flag, raising=False)
        assert is_offline() is False

    def test_mock_flag_forces_offline_even_with_key(self, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
        monkeypatch.setenv("MOCK", "1")
        assert is_offline() is True


class TestDataAccessTiers:
    @pytest.mark.asyncio
    async def test_returns_mock_when_no_key(self, monkeypatch, tmp_path):
        # No key -> offline -> no cache -> embedded mock.
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
        for flag in ("COURTVISION_OFFLINE", "COURTVISION_MOCK", "OFFLINE", "MOCK"):
            monkeypatch.delenv(flag, raising=False)

        dal = DataAccessLayer(cache_dir=tmp_path)
        result = await dal.get_prediction("Boston Celtics", "New York Knicks")

        assert result["source"] == "mock"
        assert result["predicted_winner"] == "Boston Celtics"
        assert 0.0 <= result["confidence"] <= 1.0
        assert "factors" in result

    @pytest.mark.asyncio
    async def test_cache_tier_served_before_mock(self, tmp_path):
        # Force offline so the live tier is skipped, seed the cache, expect cache.
        dal = DataAccessLayer(cache_dir=tmp_path, offline=True)
        dal._write_cache(
            "Boston_Celtics__New_York_Knicks",
            {"predicted_winner": "Boston Celtics", "confidence": 0.9},
        )
        result = await dal.get_prediction("Boston Celtics", "New York Knicks")
        assert result["source"] == "cache"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_expired_cache_falls_through_to_mock(self, tmp_path):
        dal = DataAccessLayer(cache_dir=tmp_path, offline=True, cache_ttl_seconds=1)
        dal._write_cache("A__B", {"predicted_winner": "A"})
        # Age the cache past its TTL.
        path = dal._cache_path("A__B")
        import json

        payload = json.loads(path.read_text())
        payload["_cached_at"] = time.time() - 10
        path.write_text(json.dumps(payload))

        result = await dal.get_prediction("A", "B")
        assert result["source"] == "mock"

    @pytest.mark.asyncio
    async def test_live_tier_used_and_cached_when_online(self, tmp_path):
        class FakeQwen:
            async def predict_async(self, home_team, away_team, **kw):
                return {"predicted_winner": home_team, "confidence": 0.77}

        dal = DataAccessLayer(qwen_client=FakeQwen(), cache_dir=tmp_path, offline=False)
        result = await dal.get_prediction("Lakers", "Clippers")
        assert result["source"] == "live"
        assert result["confidence"] == 0.77
        # Live result should have been written to the cache.
        cached = dal._read_cache("Lakers__Clippers")
        assert cached is not None

    @pytest.mark.asyncio
    async def test_live_failure_falls_back_to_mock(self, tmp_path):
        class BrokenQwen:
            async def predict_async(self, home_team, away_team, **kw):
                raise RuntimeError("network down")

        dal = DataAccessLayer(qwen_client=BrokenQwen(), cache_dir=tmp_path, offline=False)
        result = await dal.get_prediction("Lakers", "Clippers")
        assert result["source"] == "mock"
