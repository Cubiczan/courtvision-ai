"""Azuro Protocol integration service for CourtVision AI."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from courtvision.chp.gate import CHPGate, PositionRequest
from courtvision.models.nba import Market, MarketStatus

logger = logging.getLogger(__name__)

# Azuro Protocol contract addresses on Polygon Amoy
AZURO_CORE_ADDRESS = os.getenv("AZURO_CORE_ADDRESS", "0x0000000000000000000000000000000000000000")
AZURO_PROXY_ADDRESS = os.getenv("AZURO_PROXY_ADDRESS", "0x0000000000000000000000000000000000000000")
POLYGON_AMOY_CHAIN_ID = 80002


class AzuroService:
    """Service for interacting with Azuro Protocol on Polygon Amoy."""

    def __init__(
        self,
        core_address: Optional[str] = None,
        proxy_address: Optional[str] = None,
        rpc_url: Optional[str] = None,
        chp_gate: Optional[CHPGate] = None,
    ) -> None:
        self.core_address = core_address or AZURO_CORE_ADDRESS
        self.proxy_address = proxy_address or AZURO_PROXY_ADDRESS
        self.rpc_url = rpc_url or os.getenv(
            "POLYGON_AMOY_RPC", "https://rpc-amoy.polygon.technology"
        )
        self._markets: dict[int, Market] = {}
        self._market_counter = 0
        # CHP decision gate: every position/bet is gated before it is committed.
        self.chp_gate = chp_gate or CHPGate()

        logger.info(
            "AzuroService initialized: chain_id=%d, core=%s, proxy=%s",
            POLYGON_AMOY_CHAIN_ID,
            self.core_address,
            self.proxy_address,
        )

    def create_market(
        self,
        game_id: str,
        home_team: str,
        away_team: str,
        scheduled_tipoff: datetime,
        home_odds: float = 1.90,
        away_odds: float = 1.90,
    ) -> Market:
        """Create a new prediction market via Azuro Protocol.

        In production, this would call AzuroProxy.createMarket() on-chain.
        For demo purposes, we simulate the market creation locally.
        """
        self._market_counter += 1
        market = Market(
            market_id=self._market_counter,
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            status=MarketStatus.ACTIVE,
            home_odds=home_odds,
            away_odds=away_odds,
            total_liquidity=0.0,
            scheduled_tipoff=scheduled_tipoff,
            chain_id=POLYGON_AMOY_CHAIN_ID,
            protocol="azuro",
        )
        self._markets[market.market_id] = market
        logger.info("Created market %d for game %s", market.market_id, game_id)
        return market

    def get_market(self, market_id: int) -> Optional[Market]:
        """Get a market by ID."""
        return self._markets.get(market_id)

    def get_active_markets(self) -> list[Market]:
        """Get all active markets."""
        return [
            m for m in self._markets.values()
            if m.status == MarketStatus.ACTIVE
        ]

    def lock_market(self, market_id: int) -> bool:
        """Lock a market (before game starts)."""
        market = self._markets.get(market_id)
        if not market or market.status != MarketStatus.ACTIVE:
            return False
        market.status = MarketStatus.LOCKED
        logger.info("Locked market %d", market_id)
        return True

    def resolve_market(self, market_id: int, home_score: int, away_score: int) -> bool:
        """Resolve a market after game completion."""
        market = self._markets.get(market_id)
        if not market or market.status == MarketStatus.RESOLVED:
            return False
        market.status = MarketStatus.RESOLVED
        logger.info(
            "Resolved market %d: %s %d - %d %s",
            market_id, market.home_team, home_score, away_score, market.away_team,
        )
        return True

    def simulate_bet(
        self,
        market_id: int,
        outcome: str,
        amount: float,
        confidence: float = 1.0,
        user_address: str = "0x0000000000000000000000000000000000000000",
        chp_approved: bool = False,
    ) -> dict[str, Any]:
        """Simulate placing a bet (demo mode), gated by the CHP decision gate.

        Every position is evaluated by the CHP gate before it is committed:
        - Below the HITL threshold and passing sanity checks -> committed (LOCKED).
        - At/above the HITL threshold -> NOT committed; ``hitl_required`` is
          returned so the caller can route it to a human approval queue and
          re-call with ``chp_approved=True`` once approved.
        - Any sanity/policy violation -> NOT committed; ``blocked`` is returned.
        """
        market = self._markets.get(market_id)
        if not market:
            return {"error": "Market not found"}

        # --- CHP gate: gate the position before committing anything ---
        odds = market.home_odds if outcome == "home_win" else market.away_odds
        request = PositionRequest(
            market_id=market_id,
            outcome=outcome,
            notional=amount,
            odds=odds,
            confidence=confidence,
            market_protocol=market.protocol,
            chain="polygon-amoy",
            user_address=user_address,
        )
        if chp_approved:
            decision = self.chp_gate.approve(request)
        else:
            decision = self.chp_gate.evaluate(request)
        if not decision.allowed:
            logger.info(
                "CHP gate did not authorize bet on market %d: %s (%s)",
                market_id, decision.state.value, decision.reason,
            )
            return {
                "market_id": market_id,
                "outcome": outcome,
                "amount": amount,
                "chp_state": decision.state.value,
                "committed": False,
                "hitl_required": decision.requires_human,
                "blocked": bool(decision.violations),
                "reason": decision.reason,
                "provenance": decision.provenance.to_dict(),
            }

        if outcome == "home_win":
            odds = market.home_odds
            market.home_pool += amount
        else:
            odds = market.away_odds
            market.away_pool += amount

        market.total_liquidity += amount

        # Recalculate odds (parimutuel style)
        total = market.home_pool + market.away_pool
        if market.home_pool > 0:
            market.home_odds = round(total / market.home_pool, 2)
        if market.away_pool > 0:
            market.away_odds = round(total / market.away_pool, 2)

        potential_payout = round(amount * odds, 2)

        return {
            "market_id": market_id,
            "outcome": outcome,
            "amount": amount,
            "odds": odds,
            "potential_payout": potential_payout,
            "new_home_odds": market.home_odds,
            "new_away_odds": market.away_odds,
            "total_liquidity": market.total_liquidity,
            "committed": True,
            "chp_state": decision.state.value,
            "provenance": decision.provenance.to_dict(),
        }

    def get_market_stats(self) -> dict[str, Any]:
        """Get aggregate market statistics."""
        markets = list(self._markets.values())
        active = [m for m in markets if m.status == MarketStatus.ACTIVE]
        resolved = [m for m in markets if m.status == MarketStatus.RESOLVED]
        total_liquidity = sum(m.total_liquidity for m in markets)

        return {
            "total_markets": len(markets),
            "active_markets": len(active),
            "resolved_markets": len(resolved),
            "total_liquidity": total_liquidity,
            "chain_id": POLYGON_AMOY_CHAIN_ID,
            "protocol": "azuro",
        }

    async def get_on_chain_data(self) -> dict[str, Any]:
        """Fetch on-chain data from Polygon Amoy via RPC (demo)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get latest block number
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1,
                }
                response = await client.post(self.rpc_url, json=payload)
                data = response.json()

                return {
                    "chain_id": f"0x{POLYGON_AMOY_CHAIN_ID:04x}",
                    "latest_block": data.get("result", "0x0"),
                    "rpc_status": "connected",
                }
        except Exception as e:
            logger.warning("Failed to connect to Polygon Amoy RPC: %s", e)
            return {
                "chain_id": f"0x{POLYGON_AMOY_CHAIN_ID:04x}",
                "latest_block": "0x0",
                "rpc_status": f"disconnected: {e}",
            }
