// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title CourtVisionToken
 * @notice ERC-20 utility token for the CourtVision AI platform on Polygon Amoy.
 *         CVT is used for staking, rewards, governance, and fee discounts.
 */
contract CourtVisionToken is ERC20, ERC20Burnable, Ownable, ReentrancyGuard {
    uint256 public constant MAX_SUPPLY = 100_000_000 * 1e18; // 100M CVT
    uint256 public constant REWARD_RATE = 2; // 0.02% per block

    mapping(address => uint256) public stakedBalance;
    mapping(address => uint256) public stakeTimestamp;
    mapping(address => uint256) public rewardDebt;

    uint256 public totalStaked;
    uint256 public rewardPool;
    uint256 public lastRewardBlock;
    uint256 public accRewardPerShare;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 amount);
    event RewardsDeposited(address indexed from, uint256 amount);

    error ZeroAmount();
    error InsufficientBalance();
    error NotStaked();
    error NoRewards();

    constructor() ERC20("CourtVision Token", "CVT") Ownable(msg.sender) {
        _mint(msg.sender, 50_000_000 * 1e18); // 50M to deployer
        _mint(address(this), 50_000_000 * 1e18); // 50M to reward pool
        rewardPool = 50_000_000 * 1e18;
        lastRewardBlock = block.number;
    }

    /**
     * @notice Stake CVT tokens to earn rewards and access premium predictions
     * @param amount Number of CVT tokens to stake
     */
    function stake(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        if (balanceOf(msg.sender) < amount) revert InsufficientBalance();

        _updateRewards();
        _transfer(msg.sender, address(this), amount);

        stakedBalance[msg.sender] += amount;
        stakeTimestamp[msg.sender] = block.timestamp;
        totalStaked += amount;

        // Update reward debt for this user
        rewardDebt[msg.sender] = (stakedBalance[msg.sender] * accRewardPerShare) / 1e18;

        emit Staked(msg.sender, amount);
    }

    /**
     * @notice Unstake CVT tokens and claim pending rewards
     * @param amount Number of CVT tokens to unstake
     */
    function unstake(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        if (stakedBalance[msg.sender] < amount) revert InsufficientBalance();

        _updateRewards();
        _claimRewards();

        stakedBalance[msg.sender] -= amount;
        totalStaked -= amount;
        stakeTimestamp[msg.sender] = block.timestamp;

        _transfer(address(this), msg.sender, amount);

        emit Unstaked(msg.sender, amount);
    }

    /**
     * @notice Claim accumulated staking rewards
     */
    function claimRewards() external nonReentrant {
        if (stakedBalance[msg.sender] == 0) revert NotStaked();
        _updateRewards();
        _claimRewards();
    }

    /**
     * @notice Deposit additional tokens into the reward pool
     * @param amount Number of CVT tokens to deposit
     */
    function depositRewards(uint256 amount) external onlyOwner {
        _transfer(msg.sender, address(this), amount);
        rewardPool += amount;
        emit RewardsDeposited(msg.sender, amount);
    }

    /**
     * @notice Get pending rewards for a user
     * @param user Address to check pending rewards for
     * @return Pending reward amount
     */
    function pendingRewards(address user) external view returns (uint256) {
        uint256 _accRewardPerShare = accRewardPerShare;
        if (block.number > lastRewardBlock && totalStaked > 0) {
            uint256 blocks = block.number - lastRewardBlock;
            uint256 rewards = (blocks * REWARD_RATE * totalStaked) / 10000;
            if (rewards > rewardPool) rewards = rewardPool;
            _accRewardPerShare += (rewards * 1e18) / totalStaked;
        }
        return (stakedBalance[user] * _accRewardPerShare) / 1e18 - rewardDebt[user];
    }

    /**
     * @notice Get staking info for a user
     * @param user Address to query
     * @return staked Amount staked
     * @return since Timestamp when staking started
     * @return pending Pending reward amount
     */
    function getStakingInfo(address user) external view returns (
        uint256 staked, uint256 since, uint256 pending
    ) {
        staked = stakedBalance[user];
        since = stakeTimestamp[user];
        pending = this.pendingRewards(user);
    }

    function _updateRewards() internal {
        if (block.number <= lastRewardBlock || totalStaked == 0) return;

        uint256 blocks = block.number - lastRewardBlock;
        uint256 rewards = (blocks * REWARD_RATE * totalStaked) / 10000;

        if (rewards > rewardPool) rewards = rewardPool;
        rewardPool -= rewards;
        accRewardPerShare += (rewards * 1e18) / totalStaked;
        lastRewardBlock = block.number;
    }

    function _claimRewards() internal {
        uint256 pending = (stakedBalance[msg.sender] * accRewardPerShare) / 1e18
                          - rewardDebt[msg.sender];
        if (pending == 0) revert NoRewards();

        rewardDebt[msg.sender] = (stakedBalance[msg.sender] * accRewardPerShare) / 1e18;
        _transfer(address(this), msg.sender, pending);

        emit RewardClaimed(msg.sender, pending);
    }
}
