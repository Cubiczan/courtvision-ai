"""CHP decision gate: gates market positions through EXPLORING -> PROVISIONAL -> LOCKED.

Every position/bet must pass through :meth:`CHPGate.evaluate` before it is
committed. The gate:

1. Loads ``policy.yaml`` (max notional per position, daily cap, hitl_threshold,
   allowed markets/chains/outcomes, sanity bounds). Missing/broken file ->
   a SAFE default policy so the app is never left ungated.
2. Runs a sanity / adversarial review (allowlists, odds band, confidence floor,
   notional limits, rolling daily cap).
3. Advances a state machine:
     EXPLORING  -> initial disclosure of the request
     BLOCKED    -> a hard policy violation (sanity check failed)
     HITL_REQUIRED -> notional >= hitl_threshold, needs human approval
     PROVISIONAL   -> passed sanity + below HITL threshold, ready to lock
     LOCKED     -> committed (auto below threshold, or after human approval)
4. Emits a per-decision :class:`Provenance` record (content-hashed, append-only
   in-memory ledger) so every committed claim is auditable.

The design mirrors the Rust donors' policy engines but is written in idiomatic
Python (dataclasses, Enum, pydantic-free) to match this repo.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default location of the policy file: repo-root/policy.yaml.
# gate.py lives at src/courtvision/chp/gate.py -> parents[3] is the repo root.
_DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[3] / "policy.yaml"


class GateState(str, Enum):
    """CHP position lifecycle states."""

    EXPLORING = "exploring"
    PROVISIONAL = "provisional"
    HITL_REQUIRED = "hitl_required"
    LOCKED = "locked"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Policy:
    """Loaded CHP gate policy. See ``policy.yaml`` for field documentation."""

    version: str = "1.0"
    max_notional_per_position: float = 500.0
    daily_cap: float = 2500.0
    hitl_threshold: float = 250.0
    min_confidence: float = 0.55
    min_odds: float = 1.01
    max_odds: float = 100.0
    allowed_markets: tuple[str, ...] = ("azuro",)
    allowed_chains: tuple[str, ...] = ("polygon-amoy", "polygon")
    allowed_outcomes: tuple[str, ...] = ("home_win", "away_win", "over", "under")
    source: str = "default"

    @classmethod
    def default(cls) -> "Policy":
        """Safe conservative default used when no policy file is present."""
        return cls(source="default")

    @classmethod
    def load(cls, path: Optional[os.PathLike[str] | str] = None) -> "Policy":
        """Load policy from YAML. Falls back to :meth:`default` on any problem.

        Non-breaking by design: a missing file, unreadable file, or missing
        PyYAML never raises — it logs and returns the safe default.
        """
        p = Path(path) if path is not None else _DEFAULT_POLICY_PATH
        if not p.exists():
            logger.info("CHP policy file not found at %s; using safe default policy", p)
            return cls.default()
        try:
            import yaml  # local import so PyYAML stays an optional dependency

            data = yaml.safe_load(p.read_text()) or {}
        except Exception as e:  # noqa: BLE001 - never let policy loading crash the app
            logger.warning("Failed to load CHP policy from %s (%s); using safe default", p, e)
            return cls.default()

        def _tuple(key: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
            val = data.get(key)
            if isinstance(val, (list, tuple)) and val:
                return tuple(str(x) for x in val)
            return fallback

        d = cls.default()
        try:
            return cls(
                version=str(data.get("version", d.version)),
                max_notional_per_position=float(
                    data.get("max_notional_per_position", d.max_notional_per_position)
                ),
                daily_cap=float(data.get("daily_cap", d.daily_cap)),
                hitl_threshold=float(data.get("hitl_threshold", d.hitl_threshold)),
                min_confidence=float(data.get("min_confidence", d.min_confidence)),
                min_odds=float(data.get("min_odds", d.min_odds)),
                max_odds=float(data.get("max_odds", d.max_odds)),
                allowed_markets=_tuple("allowed_markets", d.allowed_markets),
                allowed_chains=_tuple("allowed_chains", d.allowed_chains),
                allowed_outcomes=_tuple("allowed_outcomes", d.allowed_outcomes),
                source=str(p),
            )
        except (TypeError, ValueError) as e:
            logger.warning("Malformed CHP policy values in %s (%s); using safe default", p, e)
            return cls.default()


@dataclass(frozen=True)
class PositionRequest:
    """A proposed market position / bet awaiting CHP evaluation."""

    market_id: int
    outcome: str
    notional: float
    odds: float
    confidence: float = 1.0
    market_protocol: str = "azuro"
    chain: str = "polygon-amoy"
    user_address: str = "0x0000000000000000000000000000000000000000"
    rationale: str = ""


@dataclass(frozen=True)
class Violation:
    """A single sanity / policy violation."""

    rule_id: str
    message: str


@dataclass(frozen=True)
class Provenance:
    """Content-hashed audit record for one gate decision (per-claim provenance)."""

    decision_id: str
    timestamp: str
    market_id: int
    outcome: str
    notional: float
    state: GateState
    allowed: bool
    requires_human: bool
    violations: tuple[Violation, ...]
    content_hash: str
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "market_id": self.market_id,
            "outcome": self.outcome,
            "notional": self.notional,
            "state": self.state.value,
            "allowed": self.allowed,
            "requires_human": self.requires_human,
            "violations": [{"rule_id": v.rule_id, "message": v.message} for v in self.violations],
            "content_hash": self.content_hash,
            "rationale": self.rationale,
        }


@dataclass
class GateDecision:
    """Outcome of a CHP gate evaluation."""

    state: GateState
    allowed: bool
    requires_human: bool
    violations: tuple[Violation, ...]
    provenance: Provenance

    @property
    def is_locked(self) -> bool:
        return self.state == GateState.LOCKED

    @property
    def reason(self) -> str:
        if self.violations:
            return "; ".join(v.message for v in self.violations)
        if self.requires_human:
            return "human approval required above HITL threshold"
        if self.allowed:
            return "auto-approved under CHP thresholds"
        return "not approved"


class CHPGate:
    """Consensus Hardening Protocol gate for committing market positions.

    Usage::

        gate = CHPGate()  # loads policy.yaml, or safe default
        decision = gate.evaluate(PositionRequest(...))
        if decision.is_locked:
            azuro.simulate_bet(...)          # safe to commit
        elif decision.requires_human:
            ...                              # route to HITL approval queue
        else:
            ...                              # blocked by sanity check

    After a human approves a HITL decision, call
    :meth:`approve` to advance it to LOCKED.
    """

    def __init__(
        self,
        policy: Optional[Policy] = None,
        policy_path: Optional[os.PathLike[str] | str] = None,
    ) -> None:
        self.policy = policy or Policy.load(policy_path)
        # rolling daily-cap accounting: {utc_date_str: committed_notional}
        self._daily_committed: dict[str, float] = {}
        # append-only in-memory provenance ledger
        self._ledger: list[Provenance] = []
        logger.info(
            "CHPGate initialized: policy_source=%s max_notional=%.2f hitl=%.2f daily_cap=%.2f",
            self.policy.source,
            self.policy.max_notional_per_position,
            self.policy.hitl_threshold,
            self.policy.daily_cap,
        )

    # -- public API ---------------------------------------------------------

    def evaluate(self, request: PositionRequest) -> GateDecision:
        """Gate a position request: EXPLORING -> (BLOCKED | HITL_REQUIRED | LOCKED)."""
        # State: EXPLORING (initial disclosure)
        violations = self._sanity_check(request)

        if violations:
            return self._finalize(request, GateState.BLOCKED, allowed=False,
                                  requires_human=False, violations=violations)

        # Passed sanity -> PROVISIONAL. Decide HITL vs auto-lock by notional.
        requires_human = request.notional >= self.policy.hitl_threshold
        if requires_human:
            # Above threshold: block pending explicit human approval.
            return self._finalize(request, GateState.HITL_REQUIRED, allowed=False,
                                  requires_human=True, violations=())

        # Below threshold and sane -> auto-lock (commit the daily cap now).
        self._commit_daily(request.notional)
        return self._finalize(request, GateState.LOCKED, allowed=True,
                              requires_human=False, violations=())

    def approve(self, request: PositionRequest, approver: str = "human") -> GateDecision:
        """Advance a HITL-required position to LOCKED after human approval.

        Re-runs the sanity check (approval cannot bypass hard policy violations),
        then commits against the daily cap and emits a fresh provenance record.
        """
        violations = self._sanity_check(request)
        if violations:
            return self._finalize(request, GateState.BLOCKED, allowed=False,
                                  requires_human=False, violations=violations,
                                  rationale=f"approval by {approver} rejected: policy violation")
        self._commit_daily(request.notional)
        return self._finalize(request, GateState.LOCKED, allowed=True,
                              requires_human=False, violations=(),
                              rationale=f"human-approved by {approver}")

    @property
    def ledger(self) -> tuple[Provenance, ...]:
        """Immutable view of the append-only provenance ledger."""
        return tuple(self._ledger)

    def daily_committed(self, day: Optional[str] = None) -> float:
        """Total notional committed on ``day`` (UTC date, default today)."""
        return self._daily_committed.get(day or self._today(), 0.0)

    # -- internals ----------------------------------------------------------

    def _sanity_check(self, r: PositionRequest) -> tuple[Violation, ...]:
        """Adversarial review: hard bounds that must never be violated."""
        v: list[Violation] = []

        if r.notional <= 0:
            v.append(Violation("notional-positive", f"notional {r.notional} must be > 0"))
        if r.notional > self.policy.max_notional_per_position:
            v.append(Violation(
                "max-notional",
                f"notional {r.notional:.2f} exceeds max per position "
                f"{self.policy.max_notional_per_position:.2f}",
            ))

        projected = self.daily_committed() + max(r.notional, 0.0)
        if projected > self.policy.daily_cap:
            v.append(Violation(
                "daily-cap",
                f"projected daily notional {projected:.2f} exceeds cap "
                f"{self.policy.daily_cap:.2f}",
            ))

        if r.confidence < self.policy.min_confidence:
            v.append(Violation(
                "min-confidence",
                f"confidence {r.confidence:.2f} below minimum "
                f"{self.policy.min_confidence:.2f}",
            ))

        if not (self.policy.min_odds <= r.odds <= self.policy.max_odds):
            v.append(Violation(
                "odds-band",
                f"odds {r.odds} outside sane band "
                f"[{self.policy.min_odds}, {self.policy.max_odds}]",
            ))

        if r.market_protocol.lower() not in {m.lower() for m in self.policy.allowed_markets}:
            v.append(Violation(
                "market-allowlist",
                f"market '{r.market_protocol}' not in allowlist "
                f"{list(self.policy.allowed_markets)}",
            ))

        if r.chain.lower() not in {c.lower() for c in self.policy.allowed_chains}:
            v.append(Violation(
                "chain-allowlist",
                f"chain '{r.chain}' not in allowlist {list(self.policy.allowed_chains)}",
            ))

        if r.outcome.lower() not in {o.lower() for o in self.policy.allowed_outcomes}:
            v.append(Violation(
                "outcome-allowlist",
                f"outcome '{r.outcome}' not in allowlist {list(self.policy.allowed_outcomes)}",
            ))

        return tuple(v)

    def _finalize(
        self,
        request: PositionRequest,
        state: GateState,
        *,
        allowed: bool,
        requires_human: bool,
        violations: tuple[Violation, ...],
        rationale: str = "",
    ) -> GateDecision:
        prov = self._record(request, state, allowed, requires_human, violations, rationale)
        decision = GateDecision(
            state=state,
            allowed=allowed,
            requires_human=requires_human,
            violations=violations,
            provenance=prov,
        )
        logger.info(
            "CHP decision market=%s outcome=%s notional=%.2f -> %s (%s)",
            request.market_id, request.outcome, request.notional,
            state.value, decision.reason,
        )
        return decision

    def _record(
        self,
        request: PositionRequest,
        state: GateState,
        allowed: bool,
        requires_human: bool,
        violations: tuple[Violation, ...],
        rationale: str,
    ) -> Provenance:
        timestamp = datetime.now(timezone.utc).isoformat()
        canonical = {
            "market_id": request.market_id,
            "outcome": request.outcome,
            "notional": request.notional,
            "odds": request.odds,
            "confidence": request.confidence,
            "market_protocol": request.market_protocol,
            "chain": request.chain,
            "user_address": request.user_address,
            "state": state.value,
            "allowed": allowed,
            "requires_human": requires_human,
            "violations": [v.rule_id for v in violations],
            "timestamp": timestamp,
        }
        content_hash = hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode("utf-8")
        ).hexdigest()
        decision_id = f"chp-{int(time.time() * 1000)}-{content_hash[:8]}"
        prov = Provenance(
            decision_id=decision_id,
            timestamp=timestamp,
            market_id=request.market_id,
            outcome=request.outcome,
            notional=request.notional,
            state=state,
            allowed=allowed,
            requires_human=requires_human,
            violations=violations,
            content_hash=content_hash,
            rationale=rationale or request.rationale,
        )
        self._ledger.append(prov)
        return prov

    def _commit_daily(self, notional: float) -> None:
        day = self._today()
        self._daily_committed[day] = self._daily_committed.get(day, 0.0) + max(notional, 0.0)

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
