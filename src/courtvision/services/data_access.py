"""Three-tier data-access layer for CourtVision AI predictions.

Resolves an NBA prediction through three tiers, in order:

    1. LIVE   - call the Qwen LLM (Alibaba DashScope) when a key is configured.
    2. CACHE  - return a fresh entry from the local on-disk prediction cache.
    3. MOCK   - return an embedded synthetic prediction (no network, no key).

This mirrors the JS donors ``finance-cockpit`` and ``market-radar`` which do
``live-proxy -> storage-cache -> embedded-mock`` so the app demos and passes CI
with ZERO API keys.

Offline/mock behaviour is triggered by any of:
  * env ``COURTVISION_OFFLINE`` / ``COURTVISION_MOCK`` / ``OFFLINE`` / ``MOCK``
    set to a truthy value ("1", "true", "yes", "on"), or
  * no ``DASHSCOPE_API_KEY`` present (auto-detect).

Each returned prediction dict carries a ``source`` field ("live" | "cache" |
"mock") so callers/tests can see which tier answered.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Local cache location (overridable via env). Kept out of the source tree.
_DEFAULT_CACHE_DIR = Path(
    os.getenv("COURTVISION_CACHE_DIR", Path.home() / ".cache" / "courtvision")
)
_CACHE_TTL_SECONDS = int(os.getenv("COURTVISION_CACHE_TTL", "3600"))  # 1 hour

_TRUTHY = {"1", "true", "yes", "on", "y"}


def _is_truthy(val: Optional[str]) -> bool:
    return bool(val) and val.strip().lower() in _TRUTHY


def is_offline() -> bool:
    """Return True when the app should run without live credentials.

    True if an OFFLINE/MOCK flag is set, or if no DASHSCOPE_API_KEY is present
    (auto-detect). This is what lets ``pytest`` and a local demo run key-free.
    """
    if any(
        _is_truthy(os.getenv(flag))
        for flag in ("COURTVISION_OFFLINE", "COURTVISION_MOCK", "OFFLINE", "MOCK")
    ):
        return True
    return not bool(os.getenv("DASHSCOPE_API_KEY", "").strip())


def _embedded_mock_prediction(home_team: str, away_team: str) -> dict[str, Any]:
    """Deterministic synthetic prediction used as the last-resort tier.

    Slightly biased toward the home team (home-court advantage) but honest about
    being a synthetic/offline result via ``confidence`` and ``key_insights``.
    """
    return {
        "home_win_probability": 0.56,
        "away_win_probability": 0.44,
        "predicted_total": 219.5,
        "over_probability": 0.51,
        "predicted_winner": home_team,
        "confidence": 0.45,
        "factors": {
            "team_form": 55.0,
            "home_advantage": 62.0,
            "player_impact": 52.0,
            "matchup_history": 50.0,
            "rest_advantage": 50.0,
            "injury_factor": 50.0,
            "market_sentiment": 50.0,
        },
        "key_insights": [
            f"{home_team} favored at home over {away_team} (synthetic model)",
            "Offline/mock mode: no live LLM call was made",
            "Confidence intentionally capped for synthetic predictions",
        ],
        "risk_assessment": "Moderate - synthetic offline prediction",
        "recommended_bet": "moneyline",
        "source": "mock",
    }


class DataAccessLayer:
    """Three-tier resolver: live LLM -> local cache -> embedded mock.

    Parameters
    ----------
    qwen_client:
        Optional pre-built ``QwenClient``. Only constructed/used when a key is
        present and offline mode is off.
    cache_dir:
        Directory for the on-disk prediction cache (JSON files).
    offline:
        Force offline mode. ``None`` (default) auto-detects via :func:`is_offline`.
    """

    def __init__(
        self,
        qwen_client: Optional[Any] = None,
        cache_dir: Optional[os.PathLike[str] | str] = None,
        offline: Optional[bool] = None,
        cache_ttl_seconds: int = _CACHE_TTL_SECONDS,
    ) -> None:
        self._qwen = qwen_client
        self.cache_dir = Path(cache_dir) if cache_dir is not None else _DEFAULT_CACHE_DIR
        self._forced_offline = offline
        self.cache_ttl_seconds = cache_ttl_seconds

    # -- tier selection -----------------------------------------------------

    @property
    def offline(self) -> bool:
        if self._forced_offline is not None:
            return self._forced_offline
        return is_offline()

    def _get_qwen(self) -> Optional[Any]:
        """Lazily build a QwenClient only when we intend to make a live call."""
        if self._qwen is not None:
            return self._qwen
        try:
            from courtvision.services.qwen_client import QwenClient

            self._qwen = QwenClient()
            return self._qwen
        except Exception as e:  # noqa: BLE001 - never break the fallback chain
            logger.warning("Could not initialize QwenClient: %s", e)
            return None

    # -- public API ---------------------------------------------------------

    async def get_prediction(
        self,
        home_team: str,
        away_team: str,
        cache_key: Optional[str] = None,
        **qwen_kwargs: Any,
    ) -> dict[str, Any]:
        """Resolve a prediction via live -> cache -> mock, returning the first hit.

        ``qwen_kwargs`` are forwarded to ``QwenClient.predict_async`` on the live
        tier (e.g. records, ppg, streaks, context).
        """
        key = cache_key or f"{home_team}__{away_team}".replace(" ", "_")

        # Tier 1: live LLM (only when online and a key is available)
        if not self.offline:
            client = self._get_qwen()
            if client is not None:
                try:
                    result = await client.predict_async(
                        home_team=home_team, away_team=away_team, **qwen_kwargs
                    )
                    result.setdefault("source", "live")
                    self._write_cache(key, result)
                    return result
                except Exception as e:  # noqa: BLE001
                    logger.warning("Live LLM tier failed (%s); falling back to cache/mock", e)

        # Tier 2: local cache
        cached = self._read_cache(key)
        if cached is not None:
            cached["source"] = "cache"
            return cached

        # Tier 3: embedded synthetic mock
        logger.info("Serving embedded mock prediction for %s vs %s", home_team, away_team)
        return _embedded_mock_prediction(home_team, away_team)

    # -- on-disk cache ------------------------------------------------------

    def _cache_path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, key: str) -> Optional[dict[str, Any]]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
        except Exception as e:  # noqa: BLE001
            logger.warning("Cache read failed for %s: %s", key, e)
            return None
        if time.time() - float(payload.get("_cached_at", 0)) > self.cache_ttl_seconds:
            return None
        data = payload.get("data")
        return dict(data) if isinstance(data, dict) else None

    def _write_cache(self, key: str, data: dict[str, Any]) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_path(key).write_text(
                json.dumps({"_cached_at": time.time(), "data": data})
            )
        except Exception as e:  # noqa: BLE001 - cache write is best-effort
            logger.debug("Cache write skipped for %s: %s", key, e)
