"use client";

import { useState } from "react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Game {
  id: number;
  round: string;
  gameNum: number;
  teamAway: { abbr: string; city: string; name: string; record: string; seed: number };
  teamHome: { abbr: string; city: string; name: string; record: string; seed: number };
  date: string;
  time: string;
  status: "upcoming" | "live" | "completed";
  seriesScore: string;
}

interface Prediction {
  id: number;
  game: string;
  model: string;
  predictedWinner: string;
  winProb: number;
  confidence: number;
  predictedSpread: string;
  predictedOULine: string;
  predictedOU: "Over" | "Under";
  keyFactors: string[];
  lastUpdated: string;
}

interface Market {
  id: number;
  game: string;
  question: string;
  yesPrice: number;
  noPrice: number;
  volume24h: number;
  liquidity: number;
  totalTraders: number;
  endDate: string;
  status: "active" | "resolved";
  resolution: string | null;
}

interface LeaderboardEntry {
  rank: number;
  address: string;
  displayName: string;
  accuracy: number;
  totalPredictions: number;
  profitLoss: number;
  streak: number;
  tier: "Bronze" | "Silver" | "Gold" | "Platinum";
  avatar: string;
}

// ─── Demo Data ───────────────────────────────────────────────────────────────

const games: Game[] = [
  {
    id: 1, round: "First Round", gameNum: 1,
    teamAway: { abbr: "DET", city: "Detroit", name: "Pistons", record: "36-46", seed: 7 },
    teamHome: { abbr: "BOS", city: "Boston", name: "Celtics", record: "64-18", seed: 2 },
    date: "Apr 19", time: "7:00 PM ET", status: "upcoming", seriesScore: "0–0"
  },
  {
    id: 2, round: "First Round", gameNum: 1,
    teamAway: { abbr: "MIA", city: "Miami", name: "Heat", record: "41-41", seed: 8 },
    teamHome: { abbr: "NYK", city: "New York", name: "Knicks", record: "50-32", seed: 3 },
    date: "Apr 19", time: "7:30 PM ET", status: "live", seriesScore: "0–0"
  },
  {
    id: 3, round: "First Round", gameNum: 1,
    teamAway: { abbr: "ORL", city: "Orlando", name: "Magic", record: "47-35", seed: 5 },
    teamHome: { abbr: "CLE", city: "Cleveland", name: "Cavaliers", record: "64-18", seed: 1 },
    date: "Apr 20", time: "3:30 PM ET", status: "upcoming", seriesScore: "0–0"
  },
  {
    id: 4, round: "First Round", gameNum: 1,
    teamAway: { abbr: "MIL", city: "Milwaukee", name: "Bucks", record: "42-40", seed: 6 },
    teamHome: { abbr: "IND", city: "Indiana", name: "Pacers", record: "47-35", seed: 4 },
    date: "Apr 20", time: "6:00 PM ET", status: "upcoming", seriesScore: "0–0"
  },
  {
    id: 5, round: "First Round", gameNum: 1,
    teamAway: { abbr: "LAC", city: "Los Angeles", name: "Clippers", record: "40-42", seed: 8 },
    teamHome: { abbr: "OKC", city: "Oklahoma City", name: "Thunder", record: "57-25", seed: 1 },
    date: "Apr 19", time: "9:30 PM ET", status: "live", seriesScore: "0–0"
  },
  {
    id: 6, round: "First Round", gameNum: 1,
    teamAway: { abbr: "HOU", city: "Houston", name: "Rockets", record: "52-30", seed: 4 },
    teamHome: { abbr: "DEN", city: "Denver", name: "Nuggets", record: "53-29", seed: 3 },
    date: "Apr 20", time: "8:00 PM ET", status: "upcoming", seriesScore: "0–0"
  },
  {
    id: 7, round: "First Round", gameNum: 1,
    teamAway: { abbr: "GSW", city: "Golden State", name: "Warriors", record: "47-35", seed: 5 },
    teamHome: { abbr: "MIN", city: "Minnesota", name: "Timberwolves", record: "56-26", seed: 2 },
    date: "Apr 19", time: "8:00 PM ET", status: "completed", seriesScore: "MIN 1–0"
  },
  {
    id: 8, round: "First Round", gameNum: 1,
    teamAway: { abbr: "MEM", city: "Memphis", name: "Grizzlies", record: "49-33", seed: 6 },
    teamHome: { abbr: "LAL", city: "Los Angeles", name: "Lakers", record: "47-35", seed: 3 },
    date: "Apr 20", time: "10:30 PM ET", status: "upcoming", seriesScore: "0–0"
  },
];

const predictions: Prediction[] = [
  {
    id: 1, game: "BOS vs DET", model: "CourtVision v3.2",
    predictedWinner: "BOS", winProb: 92, confidence: 96,
    predictedSpread: "BOS -11.5", predictedOULine: "214.5", predictedOU: "Under",
    keyFactors: ["Celtics 1st in defense rating", "Pistons 28th in offensive efficiency", "BOS 38-3 at home", "DET 2–8 vs top-5 teams"],
    lastUpdated: "2 min ago"
  },
  {
    id: 2, game: "NYK vs MIA", model: "CourtVision v3.2",
    predictedWinner: "NYK", winProb: 71, confidence: 78,
    predictedSpread: "NYK -4.5", predictedOULine: "198.5", predictedOU: "Under",
    keyFactors: ["Knicks 2nd in pace adjustment defense", "Miami 3rd worst bench scoring", "MSG home-court edge", "Brunson averaging 28.7 PPG"],
    lastUpdated: "5 min ago"
  },
  {
    id: 3, game: "CLE vs ORL", model: "CourtVision v3.2",
    predictedWinner: "CLE", winProb: 66, confidence: 72,
    predictedSpread: "CLE -5.5", predictedOULine: "206.0", predictedOU: "Over",
    keyFactors: ["Cavs top-3 in 3PT efficiency", "Orlando struggles from deep", "Mitchell playoff experience", "CLE won 3 of 4 reg. season"],
    lastUpdated: "8 min ago"
  },
  {
    id: 4, game: "OKC vs LAC", model: "CourtVision v3.2",
    predictedWinner: "OKC", winProb: 88, confidence: 91,
    predictedSpread: "OKC -9.0", predictedOULine: "210.5", predictedOU: "Under",
    keyFactors: ["Sengun dominant inside", "Thunder #1 net rating", "Clippers without Kawhi", "OKC 35-6 at home"],
    lastUpdated: "12 min ago"
  },
  {
    id: 5, game: "DEN vs HOU", model: "CourtVision v3.2",
    predictedWinner: "DEN", winProb: 58, confidence: 62,
    predictedSpread: "DEN -2.0", predictedOULine: "218.5", predictedOU: "Over",
    keyFactors: ["Jokić MVP-caliber season", "Rockets strong defense", "Closest matchup of Round 1", "DEN altitude advantage"],
    lastUpdated: "15 min ago"
  },
  {
    id: 6, game: "LAL vs MEM", model: "CourtVision v3.2",
    predictedWinner: "LAL", winProb: 61, confidence: 65,
    predictedSpread: "LAL -3.0", predictedOULine: "222.0", predictedOU: "Over",
    keyFactors: ["LeBron playoff mode activated", "Lakers improved interior defense", "Morant questionable (ankle)", "LAL 12–3 last 15 games"],
    lastUpdated: "18 min ago"
  },
];

const markets: Market[] = [
  { id: 1, game: "BOS vs DET", question: "Will Celtics win by 10+?", yesPrice: 0.72, noPrice: 0.28, volume24h: 142500, liquidity: 89000, totalTraders: 1847, endDate: "Apr 19, 10:00 PM", status: "active", resolution: null },
  { id: 2, game: "NYK vs MIA", question: "Will Jalen Brunson score 25+?", yesPrice: 0.64, noPrice: 0.36, volume24h: 98300, liquidity: 67000, totalTraders: 1203, endDate: "Apr 19, 10:00 PM", status: "active", resolution: null },
  { id: 3, game: "OKC vs LAC", question: "Will Thunder win Game 1?", yesPrice: 0.87, noPrice: 0.13, volume24h: 210000, liquidity: 125000, totalTraders: 2534, endDate: "Apr 19, 11:30 PM", status: "active", resolution: null },
  { id: 4, game: "CLE vs ORL", question: "Will total points go Over 206?", yesPrice: 0.53, noPrice: 0.47, volume24h: 76400, liquidity: 45000, totalTraders: 892, endDate: "Apr 20, 7:00 PM", status: "active", resolution: null },
  { id: 5, game: "DEN vs HOU", question: "Will Jokić record a triple-double?", yesPrice: 0.41, noPrice: 0.59, volume24h: 156000, liquidity: 95000, totalTraders: 1678, endDate: "Apr 20, 10:00 PM", status: "active", resolution: null },
  { id: 6, game: "LAL vs MEM", question: "Will LeBron score 30+ points?", yesPrice: 0.38, noPrice: 0.62, volume24h: 189000, liquidity: 110000, totalTraders: 2105, endDate: "Apr 20, 12:30 AM", status: "active", resolution: null },
  { id: 7, game: "IND vs MIL", question: "Will Pacers win Game 1?", yesPrice: 0.58, noPrice: 0.42, volume24h: 54200, liquidity: 32000, totalTraders: 654, endDate: "Apr 20, 8:00 PM", status: "active", resolution: null },
  { id: 8, game: "MIN vs GSW", question: "Will Timberwolves cover -5.5?", yesPrice: 0.55, noPrice: 0.45, volume24h: 87800, liquidity: 51000, totalTraders: 1023, endDate: "Apr 19, 11:00 PM", status: "resolved", resolution: "Yes" },
];

const leaderboard: LeaderboardEntry[] = [
  { rank: 1, address: "0x7a3b...f1e2", displayName: "AlphaOracle", accuracy: 94.2, totalPredictions: 312, profitLoss: 12.84, streak: 18, tier: "Platinum", avatar: "👑" },
  { rank: 2, address: "0x2c8d...a4b3", displayName: "SwishCapital", accuracy: 91.7, totalPredictions: 287, profitLoss: 9.56, streak: 14, tier: "Platinum", avatar: "💎" },
  { rank: 3, address: "0x9f1e...c7d8", displayName: "HoopsWhale", accuracy: 89.3, totalPredictions: 256, profitLoss: 7.23, streak: 11, tier: "Gold", avatar: "🐋" },
  { rank: 4, address: "0x4b6a...e2f9", displayName: "CourtKing", accuracy: 87.1, totalPredictions: 198, profitLoss: 5.89, streak: 9, tier: "Gold", avatar: "🏀" },
  { rank: 5, address: "0xd3c7...b1a5", displayName: "StatNerd_42", accuracy: 85.4, totalPredictions: 421, profitLoss: 4.12, streak: 7, tier: "Gold", avatar: "📊" },
  { rank: 6, address: "0x1e5f...d9c2", displayName: "ThreePointDAO", accuracy: 82.8, totalPredictions: 176, profitLoss: 3.45, streak: 5, tier: "Silver", avatar: "🎯" },
  { rank: 7, address: "0x8a2b...f3e7", displayName: "BuzzerBet", accuracy: 80.1, totalPredictions: 234, profitLoss: 2.18, streak: 4, tier: "Silver", avatar: "🔔" },
  { rank: 8, address: "0x6c4d...a8b1", displayName: "PaintProtector", accuracy: 78.6, totalPredictions: 167, profitLoss: 1.52, streak: 3, tier: "Silver", avatar: "🛡️" },
  { rank: 9, address: "0xf2e9...c4d6", displayName: "FastBreakFi", accuracy: 75.3, totalPredictions: 142, profitLoss: 0.87, streak: 2, tier: "Bronze", avatar: "⚡" },
  { rank: 10, address: "0x3d1a...e5b8", displayName: "RookieDegens", accuracy: 72.0, totalPredictions: 98, profitLoss: -0.34, streak: 1, tier: "Bronze", avatar: "🆕" },
];

// ─── Tab type ────────────────────────────────────────────────────────────────

type Tab = "games" | "predictions" | "markets" | "leaderboard";

// ─── Components ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: Game["status"] }) {
  if (status === "live")
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 pulse-dot" />
        LIVE
      </span>
    );
  if (status === "completed")
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/15 text-slate-400 border border-slate-500/20">
        FINAL
      </span>
    );
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/15 text-purple-400 border border-purple-500/20">
      UPCOMING
    </span>
  );
}

function ConfidenceBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-2 bg-slate-700/50 rounded-full overflow-hidden">
      <div
        className={`confidence-bar-fill h-full rounded-full ${color}`}
        style={{ width: `${value}%` }}
      />
    </div>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const styles: Record<string, string> = {
    Platinum: "bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-purple-300 border-purple-500/30",
    Gold: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
    Silver: "bg-slate-400/15 text-slate-300 border-slate-400/30",
    Bronze: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${styles[tier] || styles.Bronze}`}>
      {tier}
    </span>
  );
}

// ─── Tab Panels ──────────────────────────────────────────────────────────────

function GamesTab() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">NBA 2025 Playoffs — First Round</h2>
          <p className="text-sm text-slate-400 mt-1">8 Game 1 matchups · Updated in real-time</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-red-500 pulse-dot" />
          2 Live
        </div>
      </div>

      <div className="grid gap-3">
        {games.map((game) => (
          <div
            key={game.id}
            className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 hover:border-[#334155] transition-all glow-purple"
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Left: Matchup */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={game.status} />
                    <span className="text-xs text-slate-500 font-mono">GAME {game.gameNum}</span>
                  </div>
                  <span className="text-xs text-slate-500">{game.date} · {game.time}</span>
                </div>

                <div className="flex items-center gap-4">
                  {/* Away Team */}
                  <div className="flex-1 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#1e293b] flex items-center justify-center text-sm font-bold text-slate-300 border border-slate-700">
                      {game.teamAway.abbr}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">{game.teamAway.city}</span>
                        <span className="text-xs text-slate-500">#{game.teamAway.seed}</span>
                      </div>
                      <span className="text-xs text-slate-400">{game.teamAway.name} · {game.teamAway.record}</span>
                    </div>
                  </div>

                  <div className="flex flex-col items-center px-2">
                    <span className="text-xs text-slate-500 mb-1">VS</span>
                    <span className="text-xs text-slate-400 font-mono">{game.seriesScore}</span>
                  </div>

                  {/* Home Team */}
                  <div className="flex-1 flex items-center gap-3 justify-end">
                    <div className="text-right">
                      <div className="flex items-center gap-2 justify-end">
                        <span className="text-xs text-slate-500">#{game.teamHome.seed}</span>
                        <span className="text-sm font-semibold text-white">{game.teamHome.city}</span>
                      </div>
                      <span className="text-xs text-slate-400">{game.teamHome.name} · {game.teamHome.record}</span>
                    </div>
                    <div className="w-10 h-10 rounded-lg bg-[#1e293b] flex items-center justify-center text-sm font-bold text-white border border-purple-500/30">
                      {game.teamHome.abbr}
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: Action */}
              <div className="flex flex-col items-end gap-2 lg:min-w-[160px]">
                <button className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white text-sm font-semibold hover:opacity-90 transition-opacity shadow-lg shadow-purple-500/10 w-full lg:w-auto">
                  View Prediction
                </button>
                <button className="px-4 py-2 rounded-lg bg-[#1e293b] border border-[#334155] text-slate-300 text-sm font-medium hover:bg-[#1e293b] hover:border-[#475569] transition-all w-full lg:w-auto">
                  Trade on Market
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PredictionsTab() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">AI Predictions</h2>
          <p className="text-sm text-slate-400 mt-1">Powered by CourtVision v3.2 · Updated every 60 seconds</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20">
          <span className="w-2 h-2 rounded-full bg-green-500 pulse-dot" />
          <span className="text-xs text-green-400 font-medium">Model Online</span>
        </div>
      </div>

      <div className="grid gap-4">
        {predictions.map((pred) => (
          <div
            key={pred.id}
            className="bg-[#111827] border border-[#1e293b] rounded-xl p-5 hover:border-[#334155] transition-all"
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#8B5CF6]/20 to-[#3B82F6]/20 border border-purple-500/20 flex items-center justify-center">
                  <span className="text-lg font-bold text-white">{pred.predictedWinner}</span>
                </div>
                <div>
                  <h3 className="font-bold text-white">{pred.game}</h3>
                  <span className="text-xs text-slate-400">{pred.model} · {pred.lastUpdated}</span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">{pred.winProb}%</div>
                  <div className="text-[10px] uppercase tracking-wider text-slate-400">Win Probability</div>
                </div>
              </div>
            </div>

            {/* Confidence + Spread + O/U */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <div className="bg-[#0f172a] rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400 uppercase tracking-wider">Confidence</span>
                  <span className={`text-sm font-bold ${pred.confidence >= 85 ? "text-green-400" : pred.confidence >= 70 ? "text-yellow-400" : "text-orange-400"}`}>
                    {pred.confidence}%
                  </span>
                </div>
                <ConfidenceBar
                  value={pred.confidence}
                  color={pred.confidence >= 85 ? "bg-gradient-to-r from-green-500 to-emerald-400" : pred.confidence >= 70 ? "bg-gradient-to-r from-yellow-500 to-amber-400" : "bg-gradient-to-r from-orange-500 to-amber-500"}
                />
              </div>
              <div className="bg-[#0f172a] rounded-lg p-3 text-center">
                <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Spread</div>
                <div className="text-lg font-bold text-white">{pred.predictedSpread}</div>
              </div>
              <div className="bg-[#0f172a] rounded-lg p-3 text-center">
                <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Over/Under</div>
                <div className="text-lg font-bold text-white">{pred.predictedOULine}</div>
                <span className={`text-xs font-medium ${pred.predictedOU === "Over" ? "text-green-400" : "text-red-400"}`}>
                  {pred.predictedOU}
                </span>
              </div>
            </div>

            {/* Key Factors */}
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Key Factors</div>
              <div className="flex flex-wrap gap-2">
                {pred.keyFactors.map((factor, i) => (
                  <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/50 text-xs text-slate-300">
                    <span className="w-1 h-1 rounded-full bg-purple-400" />
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketsTab() {
  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Prediction Markets</h2>
          <p className="text-sm text-slate-400 mt-1">Live markets on Polygon Amoy · Smart Contract Verified</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
            <svg className="w-3.5 h-3.5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-xs text-purple-400 font-medium">Polygon Amoy</span>
          </div>
          <div className="text-right">
            <div className="text-sm font-bold text-white">$1.02M</div>
            <div className="text-[10px] text-slate-400">Total Liquidity</div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-2">
        {[
          { label: "Active Markets", value: "7", icon: "📊", change: "+2 today" },
          { label: "24h Volume", value: "$1.01M", icon: "📈", change: "+34%" },
          { label: "Total Traders", value: "12,066", icon: "👥", change: "+421 today" },
          { label: "Avg. Resolution", value: "~2.4h", icon: "⏱️", change: "95% on time" },
        ].map((stat, i) => (
          <div key={i} className="bg-[#111827] border border-[#1e293b] rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg">{stat.icon}</span>
              <span className="text-[10px] text-green-400 font-medium">{stat.change}</span>
            </div>
            <div className="text-lg font-bold text-white">{stat.value}</div>
            <div className="text-xs text-slate-400">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-3">
        {markets.map((market) => (
          <div
            key={market.id}
            className={`bg-[#111827] border rounded-xl p-5 transition-all ${market.status === "resolved" ? "border-slate-600/50 opacity-70" : "border-[#1e293b] hover:border-[#334155]"}`}
          >
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Left */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">{market.game}</span>
                  {market.status === "active" && (
                    <span className="flex items-center gap-1 text-[10px] text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">
                      <span className="w-1 h-1 rounded-full bg-green-500 pulse-dot" />
                      ACTIVE
                    </span>
                  )}
                  {market.status === "resolved" && (
                    <span className="text-[10px] text-slate-400 bg-slate-500/10 px-2 py-0.5 rounded-full">
                      RESOLVED — {market.resolution}
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-white mb-1">{market.question}</h3>
                <div className="text-xs text-slate-500">Ends: {market.endDate} · {market.totalTraders.toLocaleString()} traders</div>
              </div>

              {/* Center: Odds */}
              <div className="flex items-center gap-6 lg:min-w-[280px]">
                <div className="text-center flex-1">
                  <div className="text-xs text-green-400 uppercase tracking-wider mb-1">Yes</div>
                  <div className="text-2xl font-bold text-green-400">{(market.yesPrice * 100).toFixed(0)}¢</div>
                  <ConfidenceBar value={market.yesPrice * 100} color="bg-gradient-to-r from-green-500 to-emerald-400" />
                </div>
                <div className="w-px h-10 bg-slate-700" />
                <div className="text-center flex-1">
                  <div className="text-xs text-red-400 uppercase tracking-wider mb-1">No</div>
                  <div className="text-2xl font-bold text-red-400">{(market.noPrice * 100).toFixed(0)}¢</div>
                  <ConfidenceBar value={market.noPrice * 100} color="bg-gradient-to-r from-red-500 to-rose-400" />
                </div>
              </div>

              {/* Right: Volume + Liquidity */}
              <div className="flex flex-col items-end gap-2 lg:min-w-[140px]">
                <div className="text-right">
                  <div className="text-sm font-bold text-white">${(market.volume24h / 1000).toFixed(0)}K</div>
                  <div className="text-[10px] text-slate-400">24h Volume</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-purple-400">${(market.liquidity / 1000).toFixed(0)}K</div>
                  <div className="text-[10px] text-slate-400">Liquidity</div>
                </div>
                {market.status === "active" && (
                  <button className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white text-sm font-semibold hover:opacity-90 transition-opacity shadow-lg shadow-purple-500/10 w-full lg:w-auto mt-1">
                    Place Bet
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LeaderboardTab() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Top Predictors</h2>
          <p className="text-sm text-slate-400 mt-1">Season leaderboard · Updated after every game resolution</p>
        </div>
        <div className="text-xs text-slate-400 bg-[#111827] border border-[#1e293b] px-3 py-1.5 rounded-lg">
          Season 2024–25
        </div>
      </div>

      {/* Tier Legend */}
      <div className="flex flex-wrap gap-3 mb-2">
        {[
          { tier: "Platinum", range: "90%+", color: "border-purple-500/30 bg-purple-500/5", textColor: "text-purple-300" },
          { tier: "Gold", range: "85%+", color: "border-yellow-500/30 bg-yellow-500/5", textColor: "text-yellow-300" },
          { tier: "Silver", range: "75%+", color: "border-slate-400/30 bg-slate-400/5", textColor: "text-slate-300" },
          { tier: "Bronze", range: "<75%", color: "border-orange-500/30 bg-orange-500/5", textColor: "text-orange-300" },
        ].map((t) => (
          <div key={t.tier} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs ${t.color} ${t.textColor}`}>
            <TierBadge tier={t.tier} />
            <span className="text-slate-400">{t.range}</span>
          </div>
        ))}
      </div>

      {/* Top 3 Podium */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-2">
        {[leaderboard[1], leaderboard[0], leaderboard[2]].map((entry) => {
          const isFirst = entry.rank === 1;
          return (
            <div
              key={entry.rank}
              className={`bg-[#111827] border rounded-xl p-5 text-center transition-all ${isFirst ? "border-purple-500/40 glow-purple" : "border-[#1e293b]"}`}
            >
              <div className="text-3xl mb-2">{entry.avatar}</div>
              <div className="text-xs text-slate-500 mb-1">#{entry.rank}</div>
              <div className="text-lg font-bold text-white mb-0.5">{entry.displayName}</div>
              <div className="text-xs text-slate-500 font-mono mb-3">{entry.address}</div>
              <TierBadge tier={entry.tier} />
              {isFirst && (
                <div className="mt-3 pt-3 border-t border-purple-500/20">
                  <span className="text-xs text-purple-400 font-medium">🏆 #1 Overall Predictor</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Rest of leaderboard table */}
      <div className="bg-[#111827] border border-[#1e293b] rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 gap-2 px-4 py-3 text-xs text-slate-500 uppercase tracking-wider border-b border-[#1e293b] font-semibold">
          <div className="col-span-1">Rank</div>
          <div className="col-span-3">Predictor</div>
          <div className="col-span-2 text-center">Accuracy</div>
          <div className="col-span-2 text-center">Picks</div>
          <div className="col-span-2 text-center">P&L (MATIC)</div>
          <div className="col-span-2 text-center">Streak</div>
        </div>
        {leaderboard.map((entry) => (
          <div
            key={entry.rank}
            className={`grid grid-cols-12 gap-2 px-4 py-3 items-center border-b border-[#1e293b]/50 last:border-0 hover:bg-[#0f172a] transition-colors ${entry.rank <= 3 ? "bg-[#0f172a]/50" : ""}`}
          >
            <div className="col-span-1">
              <span className={`text-sm font-bold ${entry.rank <= 3 ? "text-purple-400" : "text-slate-400"}`}>
                #{entry.rank}
              </span>
            </div>
            <div className="col-span-3 flex items-center gap-2">
              <span className="text-base">{entry.avatar}</span>
              <div>
                <div className="text-sm font-semibold text-white">{entry.displayName}</div>
                <div className="text-[10px] text-slate-500 font-mono">{entry.address}</div>
              </div>
            </div>
            <div className="col-span-2 text-center">
              <span className={`text-sm font-bold ${entry.accuracy >= 90 ? "text-green-400" : entry.accuracy >= 80 ? "text-blue-400" : "text-yellow-400"}`}>
                {entry.accuracy}%
              </span>
            </div>
            <div className="col-span-2 text-center text-sm text-slate-300">
              {entry.totalPredictions}
            </div>
            <div className="col-span-2 text-center">
              <span className={`text-sm font-bold ${entry.profitLoss >= 0 ? "text-green-400" : "text-red-400"}`}>
                {entry.profitLoss >= 0 ? "+" : ""}{entry.profitLoss.toFixed(2)}
              </span>
            </div>
            <div className="col-span-2 text-center">
              <span className="inline-flex items-center gap-1 text-sm">
                🔥 {entry.streak}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("games");

  const tabs: { key: Tab; label: string; icon: string; count?: number }[] = [
    { key: "games", label: "Games", icon: "🏀" },
    { key: "predictions", label: "Predictions", icon: "🤖" },
    { key: "markets", label: "Markets", icon: "📊", count: 7 },
    { key: "leaderboard", label: "Leaderboard", icon: "🏆" },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a1a]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0a0a1a]/80 backdrop-blur-xl border-b border-[#1e293b]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#8B5CF6] to-[#3B82F6] flex items-center justify-center shadow-lg shadow-purple-500/20">
                <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10" />
                  <path d="M2 12h20" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-bold gradient-text leading-tight">CourtVision AI</h1>
                <p className="text-[10px] text-slate-500 leading-tight">NBA Prediction Market · Polygon Amoy</p>
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-[#111827] border border-[#1e293b] px-3 py-1.5 rounded-lg">
                <span className="w-2 h-2 rounded-full bg-green-500 pulse-dot" />
                Polygon Amoy
              </div>
              <div className="hidden sm:flex items-center gap-2 text-xs bg-[#111827] border border-[#1e293b] px-3 py-1.5 rounded-lg">
                <span className="text-slate-400">MATIC</span>
                <span className="text-purple-400 font-semibold">0.85</span>
              </div>
              <button className="w-9 h-9 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] flex items-center justify-center text-white text-sm font-bold hover:opacity-90 transition-opacity">
                0x...
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-[#0a0a1a] border-b border-[#1e293b]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-0">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors relative ${
                  activeTab === tab.key
                    ? "text-purple-400 tab-active"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                    activeTab === tab.key
                      ? "bg-purple-500/20 text-purple-300"
                      : "bg-slate-800 text-slate-400"
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {activeTab === "games" && <GamesTab />}
          {activeTab === "predictions" && <PredictionsTab />}
          {activeTab === "markets" && <MarketsTab />}
          {activeTab === "leaderboard" && <LeaderboardTab />}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1e293b] bg-[#0a0a1a]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
            <span>© 2025 CourtVision AI · Built on Polygon Amoy · All rights reserved</span>
            <div className="flex items-center gap-4">
              <span className="hover:text-slate-300 cursor-pointer">Terms</span>
              <span className="hover:text-slate-300 cursor-pointer">Privacy</span>
              <span className="hover:text-slate-300 cursor-pointer">Docs</span>
              <span className="hover:text-slate-300 cursor-pointer">GitHub</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
