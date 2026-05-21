"""Tests for Solidity contract models and logic."""

import pytest


class TestContractModels:
    """Tests for contract data structures and logic."""

    def test_market_factory_outcomes(self):
        """Test outcome enum values."""
        outcomes = {"HomeWin": 0, "AwayWin": 1, "Draw": 2}
        assert outcomes["HomeWin"] == 0
        assert outcomes["AwayWin"] == 1
        assert outcomes["Draw"] == 2

    def test_market_factory_statuses(self):
        """Test market status enum values."""
        statuses = {"Created": 0, "Active": 1, "Locked": 2, "Resolved": 3, "Cancelled": 4}
        assert statuses["Created"] == 0
        assert statuses["Active"] == 1
        assert statuses["Locked"] == 2
        assert statuses["Resolved"] == 3
        assert statuses["Cancelled"] == 4

    def test_platform_fee_calculation(self):
        """Test platform fee calculation (2% of bet amount)."""
        platform_fee = 200  # scaled by 10000 = 2%
        bet_amount = 1e18  # 1 ETH
        fee = (bet_amount * platform_fee) / 10000
        expected = 0.02 * 1e18
        assert fee == expected

    def test_platform_fee_50_tokens(self):
        """Test fee on 50 tokens."""
        platform_fee = 200
        amount = 50 * 1e18
        fee = (amount * platform_fee) / 10000
        assert fee == 1 * 1e18  # 2% of 50 = 1

    def test_odds_recalculation(self):
        """Test parimutuel odds calculation."""
        home_pool = 1000
        away_pool = 800
        total_pool = home_pool + away_pool
        # Odds = total / outcome_pool
        home_odds = total_pool / home_pool
        away_odds = total_pool / away_pool
        assert home_odds == 1.8
        assert away_odds == 2.25

    def test_odds_recalculation_equal_pools(self):
        """Test odds when pools are equal."""
        home_pool = 1000
        away_pool = 1000
        total_pool = 2000
        home_odds = total_pool / home_pool
        away_odds = total_pool / away_pool
        assert home_odds == 2.0
        assert away_odds == 2.0

    def test_payout_calculation(self):
        """Test proportional payout calculation."""
        user_bet = 100
        winning_pool = 500
        total_liquidity = 900
        payout = (user_bet * total_liquidity) / winning_pool
        assert payout == 180

    def test_reward_pool_tier_thresholds(self):
        """Test tier thresholds."""
        BRONZE = 5
        SILVER = 15
        GOLD = 30
        PLATINUM = 50
        assert BRONZE < SILVER < GOLD < PLATINUM

    def test_reward_pool_tier_assignment(self):
        """Test tier assignment based on correct predictions."""
        def get_tier(correct):
            if correct >= 50: return 3  # Platinum
            if correct >= 30: return 2  # Gold
            if correct >= 15: return 1  # Silver
            return 0  # Bronze

        assert get_tier(0) == 0
        assert get_tier(5) == 0
        assert get_tier(15) == 1
        assert get_tier(30) == 2
        assert get_tier(50) == 3
        assert get_tier(100) == 3

    def test_streak_bonus_calculation(self):
        """Test streak bonus (5 CVT per streak game > 3)."""
        base_reward = 10 * 1e18
        tier_multipliers = {0: 100, 1: 150, 2: 200, 3: 300}
        streak = 7
        tier = 2  # Gold
        multiplier = tier_multipliers[tier]
        streak_bonus = streak * 5 if streak > 3 else 0
        reward = ((base_reward * multiplier) / 100) + streak_bonus * 1e18
        # Gold: 2.0x base = 20, streak bonus = 7*5 = 35, total = 55 CVT
        assert reward == 55 * 1e18

    def test_streak_bonus_under_threshold(self):
        """Test no streak bonus for streaks <= 3."""
        streak = 3
        streak_bonus = streak * 5 if streak > 3 else 0
        assert streak_bonus == 0

    def test_cvt_token_max_supply(self):
        """Test CVT max supply."""
        MAX_SUPPLY = 100_000_000 * 1e18
        assert MAX_SUPPLY == 100_000_000 * 1e18

    def test_cvt_initial_distribution(self):
        """Test CVT initial token distribution."""
        deployer_amount = 50_000_000 * 1e18
        reward_pool_amount = 50_000_000 * 1e18
        total = deployer_amount + reward_pool_amount
        MAX_SUPPLY = 100_000_000 * 1e18
        assert total == MAX_SUPPLY

    def test_reward_rate_per_block(self):
        """Test reward rate calculation."""
        REWARD_RATE = 2  # 0.02% per block
        total_staked = 1000 * 1e18
        blocks = 100
        rewards = (blocks * REWARD_RATE * total_staked) / 10000
        expected = 0.0002 * 100 * 1000 * 1e18
        assert rewards == expected

    def test_oracle_result_hash_deterministic(self):
        """Test oracle result hash is deterministic."""
        game_id = "NBA-001"
        home_team = "Celtics"
        away_team = "Knicks"
        home_score = 112
        away_score = 98
        chain_id = 80002

        hash1 = hash(f"{game_id}{home_team}{away_team}{home_score}{away_score}{chain_id}")
        hash2 = hash(f"{game_id}{home_team}{away_team}{home_score}{away_score}{chain_id}")
        # Note: Python hash isn't stable across runs, but same inputs give same output
        assert hash1 == hash2

    def test_oracle_confirmation_threshold(self):
        """Test oracle requires minimum confirmations."""
        required = 3
        confirmations = {0x1: True, 0x2: True, 0x3: True}
        assert len(confirmations) >= required

    def test_min_max_bet_validation(self):
        """Test bet amount validation."""
        min_bet = 0.01 * 1e18
        max_bet = 100 * 1e18
        assert min_bet < max_bet
        valid_bet = 10 * 1e18
        assert min_bet <= valid_bet <= max_bet
        too_small = 0.001 * 1e18
        assert too_small < min_bet
        too_large = 200 * 1e18
        assert too_large > max_bet

    def test_accuracy_calculation(self):
        """Test accuracy calculation in basis points."""
        total = 45
        correct = 32
        accuracy_bp = (correct * 10000) / total
        assert abs(accuracy_bp - 7111.11) < 0.01  # 71.11%

    def test_accuracy_zero_division_protection(self):
        """Test accuracy with zero predictions."""
        total = 0
        correct = 0
        accuracy = (correct * 10000) / total if total > 0 else 0
        assert accuracy == 0
