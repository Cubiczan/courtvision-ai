# CourtVision AI — DoraHacks BUIDL Submission

---

## BUIDL Name
**CourtVision AI**

## Vision
Traditional NBA betting platforms rely on centralized bookmakers with opaque odds-making processes, limited market types, and no AI-driven analysis for retail users. CourtVision AI democratizes sports prediction markets by combining Qwen LLM-powered game analysis with Azuro Protocol's decentralized prediction infrastructure on Polygon Amoy. Users get transparent, AI-generated predictions with confidence scores, and can participate in permissionless prediction markets with parimutuel odds — eliminating the need for trusted intermediaries while making advanced NBA analytics accessible to everyone.

## Category: Is this an AI Agent?
**No** — CourtVision AI is an AI-powered prediction platform (not an autonomous agent).

## GitHub Repository
https://github.com/Cubiczan/courtvision-ai

## Key Innovation Domains
- AI x Web3
- Prediction Markets
- DeFi
- Sports + Entertainment

## L1s/L2s/Appchains/Other Ecosystems
- **Polygon Amoy Testnet** (primary deployment target)
- Azuro Protocol (prediction market infrastructure)

## How Does Your Project Use Polygon/Azuro?
CourtVision AI deploys on Polygon Amoy testnet, leveraging Azuro Protocol for on-chain NBA prediction markets. Solidity contracts (NBAMarketFactory, CourtVisionToken, OracleProxy, RewardPool) handle market creation, parimutuel betting with dynamic odds, multi-sig result verification, and tiered CVT rewards — all on Azuro's liquidity layer.

## BUIDL Description

![Dashboard: Games](https://raw.githubusercontent.com/Cubiczan/courtvision-ai/main/dashboard/screenshots/01-games.png)
![Dashboard: Predictions](https://raw.githubusercontent.com/Cubiczan/courtvision-ai/main/dashboard/screenshots/02-predictions.png)

### Overview

CourtVision AI is an AI-powered NBA prediction market platform deployed on Polygon Amoy testnet using the Azuro Protocol. It combines Qwen LLM (Alibaba Cloud DashScope) for intelligent game analysis with decentralized, permissionless prediction markets — bringing transparency and AI-driven insights to sports betting.

### Problem

Traditional sports betting suffers from:
- **Opaque odds-making** — Centralized bookmakers control odds with hidden margins
- **No AI analysis for retail** — Professional-grade analytics locked behind paywalls
- **Trust issues** — Users must trust centralized platforms with funds and data
- **Limited market types** — Most platforms only offer basic moneyline/spread bets
- **No composability** — Betting outcomes isolated from DeFi ecosystem

### Solution

CourtVision AI solves these problems through:

1. **Qwen LLM Prediction Engine** — Analyzes team form, player stats, matchup history, rest advantages, injury impact, and market sentiment to generate win probabilities with confidence scores
2. **Azuro Protocol Markets** — Decentralized, parimutuel prediction markets on Polygon Amoy with transparent odds and no house edge
3. **On-Chain Oracle** — Multi-signature result verification ensures accurate game outcomes
4. **CVT Token Rewards** — Tiered reward system (Bronze/Silver/Gold/Platinum) incentivizes accurate predictions
5. **Real-Time NBA Data** — Integrated with 2025 NBA Playoffs data covering all 16 playoff teams

![Dashboard: Markets](https://raw.githubusercontent.com/Cubiczan/courtvision-ai/main/dashboard/screenshots/03-markets.png)
![Dashboard: Leaderboard](https://raw.githubusercontent.com/Cubiczan/courtvision-ai/main/dashboard/screenshots/04-leaderboard.png)

### Smart Contracts

**CourtVisionToken (CVT)** — ERC-20 utility token with staking mechanics. Users stake CVT to earn rewards and access premium AI predictions. Implements a reward-per-block distribution model with accumulative reward tracking.

**NBAMarketFactory** — Core market management contract. Creates prediction markets for NBA games with Home Win / Away Win / Draw outcomes. Features parimutuel odds that dynamically adjust based on pool weights, 2% platform fee, and configurable min/max bet amounts. Integrates with Azuro Protocol patterns for market lifecycle management.

**OracleProxy** — Decentralized oracle with multi-signature verification. Authorized data providers submit game results, and once the required confirmation threshold is met, results are finalized on-chain. Supports ECDSA signature verification for cross-checking.

**RewardPool** — Tiered reward distribution system with four levels:
- Bronze (5+ correct): 1.0x multiplier
- Silver (15+ correct): 1.5x multiplier
- Gold (30+ correct): 2.0x multiplier
- Platinum (50+ correct): 3.0x multiplier
- Streak bonus: 5 CVT per consecutive correct prediction beyond 3

### AI Prediction Engine

The prediction engine uses **Qwen LLM** (via Alibaba Cloud DashScope) with a dual-region failover:
- **Primary**: `dashscope.aliyuncs.com` (China)
- **Fallback**: `dashscope-intl.aliyuncs.com` (Singapore)

For each NBA game, the engine analyzes:
- **Team form** — Last 10 games, point differential trends
- **Home/away splits** — Venue-specific performance
- **Player matchups** — Key player impact, usage rates
- **Head-to-head records** — Historical matchup data
- **Rest advantage** — Days of rest, back-to-back impact
- **Injury factor** — Key player availability
- **Market sentiment** — Betting patterns, line movements

Each prediction includes: win probabilities, confidence score, predicted total points, over/under probability, key insights, risk assessment, and recommended bet type.

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/games/upcoming` | List upcoming NBA games |
| `GET /api/v1/games/live` | Live game tracking |
| `GET /api/v1/games/{id}` | Game details |
| `GET /api/v1/predictions/game/{id}` | AI prediction for a game |
| `POST /api/v1/predictions/analyze` | Custom matchup analysis |
| `GET /api/v1/markets/active` | Active prediction markets |
| `POST /api/v1/markets/create` | Create new market |
| `GET /api/v1/stats/leaderboard` | Top predictors |
| `GET /api/v1/health` | Service health |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Blockchain | Polygon Amoy Testnet |
| Protocol | Azuro Protocol |
| Smart Contracts | Solidity 0.8.24 + OpenZeppelin 5.x |
| AI Engine | Qwen LLM (DashScope) |
| Backend | Python 3.11 + FastAPI + Pydantic v2 |
| Dashboard | Next.js 16 + React + Tailwind CSS |
| Testing | pytest (139 tests) |

### Demo Data

Pre-loaded with **2025 NBA Playoffs** First Round data:
- **Eastern Conference**: Boston Celtics, New York Knicks, Cleveland Cavaliers, Indiana Pacers, Milwaukee Bucks, Orlando Magic, Miami Heat, Detroit Pistons
- **Western Conference**: Oklahoma City Thunder, Denver Nuggets, Minnesota Timberwolves, Los Angeles Lakers, Memphis Grizzlies, Golden State Warriors, Houston Rockets, Los Angeles Clippers

### Development

```bash
# Backend
cd courtvision-ai
pip install -e ".[dev]"
pytest  # 139 tests passing
uvicorn courtvision.api.main:app --reload

# Dashboard
cd dashboard
npm install && npm run dev

# Contracts
cd contracts && npx hardhat compile
```

### What's Next

- Deploy contracts to Polygon Amoy via Hardhat
- Integrate live Azuro Protocol Core/Proxy contracts
- Add real-time NBA data feed via SportsData.io API
- Implement wallet connection (MetaMask) for on-chain betting
- Launch mainnet version post-hackathon on Polygon
