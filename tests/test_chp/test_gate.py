"""Tests for the CHP decision gate."""

import pytest

from courtvision.chp.gate import (
    CHPGate,
    GateState,
    Policy,
    PositionRequest,
)


@pytest.fixture
def policy():
    # Explicit policy so tests do not depend on the on-disk policy.yaml.
    return Policy(
        max_notional_per_position=500.0,
        daily_cap=2500.0,
        hitl_threshold=250.0,
        min_confidence=0.55,
        min_odds=1.01,
        max_odds=100.0,
        allowed_markets=("azuro",),
        allowed_chains=("polygon-amoy", "polygon"),
        allowed_outcomes=("home_win", "away_win", "over", "under"),
    )


@pytest.fixture
def gate(policy):
    return CHPGate(policy=policy)


def _req(**kw):
    base = dict(
        market_id=1,
        outcome="home_win",
        notional=100.0,
        odds=1.90,
        confidence=0.8,
        market_protocol="azuro",
        chain="polygon-amoy",
    )
    base.update(kw)
    return PositionRequest(**base)


class TestUnderThreshold:
    def test_under_threshold_position_passes_and_locks(self, gate):
        decision = gate.evaluate(_req(notional=100.0))
        assert decision.allowed is True
        assert decision.requires_human is False
        assert decision.state == GateState.LOCKED
        assert decision.is_locked

    def test_under_threshold_commits_daily_notional(self, gate):
        gate.evaluate(_req(notional=100.0))
        assert gate.daily_committed() == 100.0

    def test_provenance_recorded_for_each_decision(self, gate):
        gate.evaluate(_req(notional=100.0))
        gate.evaluate(_req(notional=120.0))
        assert len(gate.ledger) == 2
        for prov in gate.ledger:
            assert prov.content_hash
            assert prov.decision_id.startswith("chp-")


class TestOverThreshold:
    def test_over_threshold_requires_hitl_and_does_not_commit(self, gate):
        decision = gate.evaluate(_req(notional=300.0))
        assert decision.allowed is False
        assert decision.requires_human is True
        assert decision.state == GateState.HITL_REQUIRED
        # Not committed against the daily cap until a human approves.
        assert gate.daily_committed() == 0.0

    def test_hitl_position_locks_after_human_approval(self, gate):
        req = _req(notional=300.0)
        pending = gate.evaluate(req)
        assert pending.requires_human is True

        approved = gate.approve(req, approver="ops-lead")
        assert approved.allowed is True
        assert approved.state == GateState.LOCKED
        assert gate.daily_committed() == 300.0

    def test_at_threshold_boundary_requires_hitl(self, gate):
        decision = gate.evaluate(_req(notional=250.0))
        assert decision.requires_human is True
        assert decision.state == GateState.HITL_REQUIRED


class TestSanityChecks:
    def test_over_max_notional_is_blocked(self, gate):
        decision = gate.evaluate(_req(notional=1000.0))
        assert decision.allowed is False
        assert decision.state == GateState.BLOCKED
        assert any(v.rule_id == "max-notional" for v in decision.violations)

    def test_low_confidence_is_blocked(self, gate):
        decision = gate.evaluate(_req(notional=100.0, confidence=0.10))
        assert decision.state == GateState.BLOCKED
        assert any(v.rule_id == "min-confidence" for v in decision.violations)

    def test_disallowed_market_is_blocked(self, gate):
        decision = gate.evaluate(_req(market_protocol="polymarket"))
        assert decision.state == GateState.BLOCKED
        assert any(v.rule_id == "market-allowlist" for v in decision.violations)

    def test_odds_out_of_band_is_blocked(self, gate):
        decision = gate.evaluate(_req(odds=500.0))
        assert decision.state == GateState.BLOCKED
        assert any(v.rule_id == "odds-band" for v in decision.violations)

    def test_daily_cap_enforced_across_positions(self, gate):
        # 12 x 200 = 2400 (ok, all below HITL? 200 < 250 so they auto-lock)
        for _ in range(12):
            d = gate.evaluate(_req(notional=200.0))
            assert d.is_locked
        assert gate.daily_committed() == 2400.0
        # Next 200 would push to 2600 > 2500 cap -> blocked.
        over = gate.evaluate(_req(notional=200.0))
        assert over.state == GateState.BLOCKED
        assert any(v.rule_id == "daily-cap" for v in over.violations)

    def test_approval_cannot_bypass_sanity_violation(self, gate):
        req = _req(notional=1000.0)  # over max notional
        decision = gate.approve(req, approver="rogue")
        assert decision.allowed is False
        assert decision.state == GateState.BLOCKED


class TestPolicyLoading:
    def test_missing_policy_file_uses_safe_default(self, tmp_path):
        missing = tmp_path / "nope.yaml"
        p = Policy.load(missing)
        assert p.source == "default"
        assert p.max_notional_per_position == 500.0

    def test_loads_policy_from_yaml(self, tmp_path):
        f = tmp_path / "policy.yaml"
        f.write_text(
            "version: '1.0'\n"
            "max_notional_per_position: 42.0\n"
            "hitl_threshold: 20.0\n"
            "daily_cap: 100.0\n"
            "allowed_markets:\n  - azuro\n"
        )
        p = Policy.load(f)
        assert p.max_notional_per_position == 42.0
        assert p.hitl_threshold == 20.0
        assert str(f) in p.source

    def test_repo_policy_yaml_is_valid(self):
        # The shipped policy.yaml at repo root should load cleanly.
        p = Policy.load()
        assert p.max_notional_per_position > 0
        assert p.hitl_threshold > 0
        assert "azuro" in p.allowed_markets
