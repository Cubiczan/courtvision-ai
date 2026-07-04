# CourtVision AI

## AI-Powered NBA Prediction Market on Polygon

CourtVision AI is a decentralized NBA prediction market platform built on **Polygon Amoy testnet** using the **Azuro Protocol**. It leverages **Qwen LLM** (Alibaba Cloud DashScope) to deliver AI-driven game analysis, player performance forecasting, and intelligent odds recommendations — all on-chain.

---

## Overview

Traditional sports prediction platforms rely on centralized bookmakers with opaque odds-making processes. CourtVision AI solves this by combining:

- **Azuro Protocol** — Decentralized, permissionless prediction market infrastructure on Polygon
- **Qwen LLM** — Advanced AI analysis of NBA player stats, team trends, and game context
- **Smart Contracts** — Automated market creation, liquidity provision, and result resolution on Polygon Amoy

Users can browse upcoming NBA games, view AI-generated predictions with confidence scores, place bets on outcomes via Azuro-powered prediction markets, and earn rewards for accurate forecasts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CourtVision Dashboard                  │
│              (Next.js / React / Tailwind CSS)            │
├─────────────────────────────────────────────────────────┤
│                   FastAPI Backend                         │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────┐    │
│  │ NBA Game │  │ Qwen LLM   │  │ Azuro Protocol    │    │
│  │ Engine   │  │ Prediction │  │ Market Integration │    │
│  │          │  │ Engine     │  │                   │    │
│  └──────────┘  └────────────┘  └───────────────────┘    │
├─────────────────────────────────────────────────────────┤
│              Polygon Amoy Testnet                         │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────┐    │
│  │ NBAMarket│  │ CourtVision│  │ OracleProxy       │    │
│  │ Factory  │  │ Token (CVT)│  │ (Result Feed)     │    │
│  └──────────┘  └────────────┘  └───────────────────┘    │
│                   Azuro Protocol                          │
└─────────────────────────────────────────────────────────┘
```

---

## Smart Contracts

### NBAMarketFactory.sol
Creates and manages prediction markets for NBA games on Polygon Amoy. Each market corresponds to a specific NBA game with predefined outcomes (e.g., Team A Win / Team B Win / Over-Under). Integrates with Azuro's Core contract to register markets and manage liquidity pools.

### CourtVisionToken.sol (CVT)
ERC-20 utility token on Polygon Amoy. CVT is used for:
- Staking to access premium AI predictions
- Rewarding users who provide accurate game outcome data
- Governance votes on platform parameters
- Fee discounts on market participation

### OracleProxy.sol
Decentralized oracle contract that receives game results from authorized data providers and resolves Azuro prediction markets. Uses a multi-signature verification pattern to ensure result accuracy before payout distribution.

### RewardPool.sol
Manages the reward distribution system. Users who stake CVT and correctly predict game outcomes receive proportional rewards from the pool. Implements a tiered reward structure based on prediction accuracy streaks.

---

## AI Prediction Engine

The prediction engine uses **Qwen LLM** via Alibaba Cloud DashScope to analyze:

- **Player Statistics** — Scoring averages, shooting percentages, usage rates, recent form
- **Team Performance** — Win-loss records, home/away splits, net ratings, pace metrics
- **Matchup Analysis** — Historical head-to-head data, positional advantages, coaching strategies
- **Contextual Factors** — Injuries, rest days, playoff implications, back-to-back games
- **Market Sentiment** — Current betting patterns, line movements, sharp money indicators

Each prediction includes:
- **Win probability** with confidence interval
- **Key factors** influencing the prediction
- **Risk assessment** (upset probability, variance indicators)
- **Recommended bet type** (moneyline, spread, over/under)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/games/upcoming` | List upcoming NBA games with AI predictions |
| `GET` | `/api/v1/games/{game_id}` | Detailed game analysis with full prediction |
| `GET` | `/api/v1/games/live` | Live game tracking and in-play predictions |
| `GET` | `/api/v1/markets/active` | Active prediction markets on Polygon |
| `GET` | `/api/v1/markets/{market_id}` | Market details with odds and liquidity |
| `POST` | `/api/v1/markets/create` | Create a new prediction market (admin) |
| `POST` | `/api/v1/predictions/analyze` | Get AI prediction for a specific matchup |
| `GET` | `/api/v1/predictions/history` | User prediction history and accuracy |
| `GET` | `/api/v1/stats/leaderboard` | Top predictors leaderboard |
| `GET` | `/api/v1/health` | Service health check |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Blockchain** | Polygon Amoy Testnet |
| **Prediction Protocol** | Azuro Protocol |
| **Smart Contracts** | Solidity 0.8.24 + OpenZeppelin 5.x |
| **AI Engine** | Qwen LLM (DashScope) |
| **Backend** | Python 3.11 + FastAPI + Pydantic v2 |
| **Dashboard** | Next.js 16 + React + Tailwind CSS |
| **Data** | NBA API, On-chain data |
| **Testing** | pytest (82+ tests) |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Hardhat (for contracts)
- Polygon Amoy wallet with test MATIC

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/courtvision-ai.git
cd courtvision-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest

# Start the server
uvicorn courtvision.api.main:app --host 0.0.0.0 --port 8000
```

### Smart Contracts Setup

```bash
cd contracts
npm install

# Compile contracts
npx hardhat compile

# Deploy to Polygon Amoy
npx hardhat run scripts/deploy-amoy.js --network amoy
```

### Dashboard Setup

```bash
cd dashboard
npm install
npm run dev
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=courtvision --cov-report=term-missing

# Run specific test categories
pytest tests/test_api/
pytest tests/test_engines/
pytest tests/test_models/
```

---

## Polygon Amoy Deployment

CourtVision AI is deployed on Polygon Amoy testnet (Chain ID: 80002). Key contract addresses are configured in the environment variables.

### Azuro Protocol Integration
- Markets are created via Azuro's Core contract
- Liquidity is managed through Azuro's pool system
- Results are resolved using Azuro's resolution mechanism
- CVT rewards are distributed after market resolution

---

## NBA Playoffs 2025 Demo Data

The platform includes pre-loaded data for the 2025 NBA Playoffs:
- **Eastern Conference**: Boston Celtics, New York Knicks, Cleveland Cavaliers, Indiana Pacers, Milwaukee Bucks, Orlando Magic, Miami Heat, Detroit Pistons
- **Western Conference**: Oklahoma City Thunder, Denver Nuggets, Minnesota Timberwolves, Los Angeles Lakers, Memphis Grizzlies, Golden State Warriors, Houston Rockets, Los Angeles Clippers

---

## Decision Governance (CHP gate)

Every market position / bet is routed through a runtime **CHP decision gate**
before it is committed on-chain. This is the executable counterpart to the
CHP governance docs in `.chp/` — the pattern is adapted from the Rust
`swarmfi-executor` and `cleanmandate` policy engines.

**Policy** lives in [`policy.yaml`](policy.yaml) at the repo root:

| Field | Meaning |
|-------|---------|
| `max_notional_per_position` | Hard cap on a single position's notional |
| `daily_cap` | Cumulative committed notional allowed per UTC day |
| `hitl_threshold` | Positions at/above this notional need human approval |
| `min_confidence`, `min_odds`, `max_odds` | Sanity/adversarial bounds |
| `allowed_markets`, `allowed_chains`, `allowed_outcomes` | Allowlists |

If `policy.yaml` is missing or malformed, the gate falls back to a **safe
default policy** — the app is never left ungated (non-breaking).

**State machine** (`src/courtvision/chp/gate.py`):

```
EXPLORING ──sanity check──▶ BLOCKED           (policy/sanity violation, not committed)
          │
          └──passes──▶ PROVISIONAL ─┬─ notional < hitl_threshold ─▶ LOCKED  (auto-committed)
                                    └─ notional ≥ hitl_threshold ─▶ HITL_REQUIRED (awaits human)
HITL_REQUIRED ──gate.approve()──▶ LOCKED       (committed after human approval)
```

Each decision emits a content-hashed **provenance record** (per-claim audit
trail) appended to `CHPGate.ledger`.

The gate is wired into `AzuroService.simulate_bet(...)`, which now refuses to
mutate market liquidity unless the CHP gate returns `LOCKED`:

```python
from courtvision.services.azuro_service import AzuroService

azuro = AzuroService()                       # loads policy.yaml (or safe default)
azuro.create_market("G1", "A", "B", tipoff)

# Under threshold -> auto-committed
azuro.simulate_bet(1, "home_win", 100.0, confidence=0.8)   # committed=True, chp_state="locked"

# Over threshold -> blocked pending human approval
r = azuro.simulate_bet(1, "home_win", 400.0, confidence=0.8)  # hitl_required=True, committed=False
# ...after a human approves:
azuro.simulate_bet(1, "home_win", 400.0, confidence=0.8, chp_approved=True)  # committed=True
```

---

## Offline / mock mode

CourtVision AI runs — and its test suite passes — with **zero API keys**.
Prediction data resolves through a three-tier fallback
(`src/courtvision/services/data_access.py`), adapted from the
`finance-cockpit` / `market-radar` `live -> cache -> mock` pattern:

1. **Live** — call the Qwen LLM (Alibaba DashScope) when `DASHSCOPE_API_KEY` is set.
2. **Cache** — return a fresh entry from the local on-disk prediction cache.
3. **Mock** — return an embedded synthetic prediction (no network, no key).

Offline/mock mode is used automatically when **no key is present**, or when any
of these env flags is truthy: `COURTVISION_OFFLINE`, `COURTVISION_MOCK`,
`OFFLINE`, `MOCK`.

```bash
# Run the whole test suite with no credentials:
pytest

# Force mock mode even if a key happens to be set:
MOCK=1 uvicorn courtvision.api.main:app --port 8000
```

Every prediction dict carries a `source` field (`"live"` | `"cache"` | `"mock"`)
so callers and tests can see which tier answered. `QwenClient` no longer raises
at construction when a key is absent — it degrades to a heuristic fallback.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Built for the **NBA Prediction Market Hackathon** on DoraHacks.
Powered by **Polygon**, **Azuro Protocol**, and **Qwen LLM**.

---

## CHP Governance

This repository is hardened with the [Consensus Hardening Protocol (CHP)](https://codeberg.org/cubiczan/consensus-hardening-protocol), Cubiczan's decision-governance layer for multi-agent AI systems.

### Protocol Layers
- **R0 Gate**: All decisions must pass Solvable, Scoped, Valid, Worth_it checks
- **Foundation Disclosure**: 1-3 weakest assumptions, 1-2 invalidation conditions, 1 key vulnerability
- **Adversarial Layer**: Mandatory devil's advocate at Phase 0 and Round 3
- **State Machine**: EXPLORING → PROVISIONAL → PROVISIONAL_LOCK → LOCKED
- **Third-Party Validation**: Independent CONFIRM/REJECT before lock

### Domain Configuration
- **Category**: Blockchain / DeFi
- **Foundation Threshold**: 85
- **CFO Accuracy Guard**: Disabled

### Compliance Artifacts
| File | Purpose |
|------|---------|
| `.chp/STATE_MACHINE.md` | Decision state transitions |
| `.chp/R0_CONFIG.yaml` | Domain-calibrated thresholds |
| `.chp/ADVERSARIAL_PROMPTS.md` | Standardized challenge templates |
| `.chp/CHP_COMPLIANCE.md` | Compliance tracking & audit trail |

### CHP Version
cognitive-mesh-orchestrator 0.1.0 | [Protocol Docs](https://codeberg.org/cubiczan/consensus-hardening-protocol)

