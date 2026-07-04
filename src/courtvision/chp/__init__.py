"""Consensus Hardening Protocol (CHP) decision gate for CourtVision AI.

Gates every market position / bet through EXPLORING -> PROVISIONAL -> LOCKED
with a sanity check, a per-claim provenance record, and a human-in-the-loop
(HITL) requirement / hard block above configured thresholds.

Conceptual pattern adapted from the Rust donors ``swarmfi-executor``
(policy evaluation + notional + require-human) and ``cleanmandate``
(CHP state machine + quorum/HITL + signed audit ledger).
"""

from courtvision.chp.gate import (
    CHPGate,
    GateDecision,
    GateState,
    Policy,
    PositionRequest,
    Provenance,
    Violation,
)

__all__ = [
    "CHPGate",
    "GateDecision",
    "GateState",
    "Policy",
    "PositionRequest",
    "Provenance",
    "Violation",
]
