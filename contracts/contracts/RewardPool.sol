// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title RewardPool
 * @notice Manages reward distribution for accurate NBA predictions.
 *         Implements a tiered reward structure based on prediction accuracy.
 */
contract RewardPool is Ownable, ReentrancyGuard {

    struct Predictor {
        uint256 totalPredictions;
        uint256 correctPredictions;
        uint256 currentStreak;
        uint256 bestStreak;
        uint256 totalRewardsClaimed;
        uint256 tier; // 0=Bronze, 1=Silver, 2=Gold, 3=Platinum
    }

    mapping(address => Predictor) public predictors;
    address[] public predictorAddresses;

    IERC20 public rewardToken;

    uint256 public constant BRONZE_THRESHOLD = 5;
    uint256 public constant SILVER_THRESHOLD = 15;
    uint256 public constant GOLD_THRESHOLD = 30;
    uint256 public constant PLATINUM_THRESHOLD = 50;

    uint256 public baseReward = 10 * 1e18; // 10 CVT base reward
    uint256 public totalRewardsDistributed;
    uint256 public poolBalance;

    mapping(uint256 => uint256) public tierMultipliers;

    event PredictionRecorded(address indexed predictor, bool correct, uint256 newStreak);
    event RewardClaimed(address indexed predictor, uint256 amount, uint256 tier);
    event Deposited(address indexed from, uint256 amount);
    event TierUpgraded(address indexed predictor, uint256 oldTier, uint256 newTier);

    error NotRegistered();
    error NoRewardsAvailable();
    error ZeroDeposit();

    constructor(address _rewardToken) Ownable(msg.sender) {
        rewardToken = IERC20(_rewardToken);
        tierMultipliers[0] = 100;  // 1.0x Bronze
        tierMultipliers[1] = 150;  // 1.5x Silver
        tierMultipliers[2] = 200;  // 2.0x Gold
        tierMultipliers[3] = 300;  // 3.0x Platinum
    }

    /**
     * @notice Record a prediction result
     */
    function recordPrediction(address predictor, bool correct) external onlyOwner {
        Predictor storage pred = predictors[predictor];
        if (pred.totalPredictions == 0) predictorAddresses.push(predictor);

        pred.totalPredictions++;
        if (correct) {
            pred.correctPredictions++;
            pred.currentStreak++;
            if (pred.currentStreak > pred.bestStreak) pred.bestStreak = pred.currentStreak;

            uint256 oldTier = pred.tier;
            if (pred.correctPredictions >= PLATINUM_THRESHOLD) pred.tier = 3;
            else if (pred.correctPredictions >= GOLD_THRESHOLD) pred.tier = 2;
            else if (pred.correctPredictions >= SILVER_THRESHOLD) pred.tier = 1;
            else pred.tier = 0;

            if (pred.tier > oldTier) emit TierUpgraded(predictor, oldTier, pred.tier);
        } else {
            pred.currentStreak = 0;
        }
        emit PredictionRecorded(predictor, correct, pred.currentStreak);
    }

    /**
     * @notice Calculate pending reward for a predictor
     */
    function calculateReward(address predictor) public view returns (uint256) {
        Predictor storage pred = predictors[predictor];
        if (pred.correctPredictions == 0) return 0;
        uint256 multiplier = tierMultipliers[pred.tier];
        uint256 streakBonus = pred.currentStreak > 3 ? pred.currentStreak * 5 : 0;
        return ((baseReward * multiplier) / 100) + streakBonus * 1e18;
    }

    /**
     * @notice Claim accumulated rewards
     */
    function claimReward() external nonReentrant {
        uint256 reward = calculateReward(msg.sender);
        if (reward == 0) revert NoRewardsAvailable();
        if (poolBalance < reward) revert NoRewardsAvailable();

        Predictor storage pred = predictors[msg.sender];
        pred.totalRewardsClaimed += reward;
        pred.correctPredictions = 0;
        pred.currentStreak = 0;
        poolBalance -= reward;
        totalRewardsDistributed += reward;

        rewardToken.transfer(msg.sender, reward);
        emit RewardClaimed(msg.sender, reward, pred.tier);
    }

    function deposit(uint256 amount) external {
        if (amount == 0) revert ZeroDeposit();
        rewardToken.transferFrom(msg.sender, address(this), amount);
        poolBalance += amount;
        emit Deposited(msg.sender, amount);
    }

    function getPredictorStats(address predictor) external view returns (
        uint256 totalPredictions,
        uint256 correctPredictions,
        uint256 accuracy,
        uint256 currentStreak,
        uint256 bestStreak,
        uint256 tier,
        uint256 pendingReward
    ) {
        Predictor storage pred = predictors[predictor];
        accuracy = pred.totalPredictions > 0
            ? (pred.correctPredictions * 10000) / pred.totalPredictions : 0;
        return (
            pred.totalPredictions, pred.correctPredictions, accuracy,
            pred.currentStreak, pred.bestStreak, pred.tier, calculateReward(predictor)
        );
    }

    function getPredictorCount() external view returns (uint256) {
        return predictorAddresses.length;
    }

    function setBaseReward(uint256 reward) external onlyOwner {
        baseReward = reward;
    }
}
