"""Integration tests: AzuroService bets are gated by the CHP gate."""

from datetime import datetime, timezone

import pytest

from courtvision.chp.gate import CHPGate, Policy
from courtvision.services.azuro_service import AzuroService


@pytest.fixture
def azuro():
    # Deterministic policy so the test does not depend on repo policy.yaml.
    policy = Policy(
        max_notional_per_position=500.0,
        daily_cap=2500.0,
        hitl_threshold=250.0,
        min_confidence=0.55,
    )
    return AzuroService(chp_gate=CHPGate(policy=policy))


def _market(azuro):
    return azuro.create_market(
        "G1", "A", "B", datetime(2025, 5, 15, tzinfo=timezone.utc), 1.90, 1.90
    )


def test_under_threshold_bet_commits(azuro):
    m = _market(azuro)
    result = azuro.simulate_bet(m.market_id, "home_win", 100.0, confidence=0.8)
    assert result["committed"] is True
    assert result["chp_state"] == "locked"
    assert result["total_liquidity"] == 100.0
    assert "provenance" in result


def test_over_threshold_bet_requires_hitl_and_is_not_committed(azuro):
    m = _market(azuro)
    result = azuro.simulate_bet(m.market_id, "home_win", 400.0, confidence=0.8)
    assert result["committed"] is False
    assert result["hitl_required"] is True
    assert result["chp_state"] == "hitl_required"
    # Liquidity must be untouched since nothing was committed.
    assert azuro.get_market(m.market_id).total_liquidity == 0.0


def test_over_threshold_bet_commits_after_approval(azuro):
    m = _market(azuro)
    blocked = azuro.simulate_bet(m.market_id, "home_win", 400.0, confidence=0.8)
    assert blocked["hitl_required"] is True

    approved = azuro.simulate_bet(
        m.market_id, "home_win", 400.0, confidence=0.8, chp_approved=True
    )
    assert approved["committed"] is True
    assert approved["chp_state"] == "locked"
    assert azuro.get_market(m.market_id).total_liquidity == 400.0


def test_low_confidence_bet_is_blocked(azuro):
    m = _market(azuro)
    result = azuro.simulate_bet(m.market_id, "home_win", 100.0, confidence=0.1)
    assert result["committed"] is False
    assert result["blocked"] is True
    assert result["chp_state"] == "blocked"
