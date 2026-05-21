// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./CourtVisionToken.sol";
import "./OracleProxy.sol";

/**
 * @title NBAMarketFactory
 * @notice Creates and manages NBA prediction markets on Polygon Amoy.
 *         Integrates with Azuro Protocol patterns for market creation,
 *         liquidity provision, and result resolution.
 */
contract NBAMarketFactory is Ownable, ReentrancyGuard {

    enum Outcome { HomeWin, AwayWin, Draw }
    enum MarketStatus { Created, Active, Locked, Resolved, Cancelled }

    struct Market {
        string gameId;
        string homeTeam;
        string awayTeam;
        uint256 scheduledTipoff;
        Outcome winningOutcome;
        MarketStatus status;
        uint256 totalLiquidity;
        uint256 homeOdds;
        uint256 awayOdds;
        mapping(Outcome => uint256) outcomePool;
        mapping(address => mapping(Outcome => uint256)) userBets;
        mapping(address => bool) hasBet;
    }

    mapping(uint256 => Market) public markets;
    uint256 public marketCount;
    uint256 public platformFee = 200; // 2% fee (scaled by 10000)
    uint256 public minBet = 0.01 ether;
    uint256 public maxBet = 100 ether;

    CourtVisionToken public cvtToken;
    OracleProxy public oracle;
    IERC20 public bettingToken;

    uint256[] public activeMarketIds;

    address public azuroCore;
    address public azuroProxy;

    event MarketCreated(uint256 indexed marketId, string gameId, string homeTeam, string awayTeam);
    event BetPlaced(uint256 indexed marketId, address indexed user, Outcome outcome, uint256 amount);
    event MarketLocked(uint256 indexed marketId);
    event MarketResolved(uint256 indexed marketId, Outcome winningOutcome, uint16 homeScore, uint16 awayScore);
    event PayoutClaimed(uint256 indexed marketId, address indexed user, uint256 amount);

    error MarketNotFound();
    error MarketNotActive();
    error MarketAlreadyResolved();
    error InvalidBetAmount();
    error InsufficientAllowance();
    error NoWinnings();

    modifier marketExists(uint256 marketId) {
        if (marketId == 0 || marketId > marketCount) revert MarketNotFound();
        _;
    }

    constructor(
        address _cvtToken,
        address _oracle,
        address _bettingToken
    ) Ownable(msg.sender) {
        cvtToken = CourtVisionToken(_cvtToken);
        oracle = OracleProxy(_oracle);
        bettingToken = IERC20(_bettingToken);
    }

    /**
     * @notice Create a new prediction market for an NBA game
     * @return marketId The ID of the newly created market
     */
    function createMarket(
        string calldata gameId,
        string calldata homeTeam,
        string calldata awayTeam,
        uint256 scheduledTipoff,
        uint256 homeOdds,
        uint256 awayOdds
    ) external onlyOwner returns (uint256) {
        marketCount++;
        uint256 marketId = marketCount;

        Market storage market = markets[marketId];
        market.gameId = gameId;
        market.homeTeam = homeTeam;
        market.awayTeam = awayTeam;
        market.scheduledTipoff = scheduledTipoff;
        market.status = MarketStatus.Active;
        market.homeOdds = homeOdds;
        market.awayOdds = awayOdds;

        activeMarketIds.push(marketId);

        emit MarketCreated(marketId, gameId, homeTeam, awayTeam);
        return marketId;
    }

    /**
     * @notice Place a bet on a market outcome
     */
    function placeBet(
        uint256 marketId,
        Outcome outcome,
        uint256 amount
    ) external nonReentrant marketExists(marketId) {
        Market storage market = markets[marketId];
        if (market.status != MarketStatus.Active) revert MarketNotActive();
        if (amount < minBet || amount > maxBet) revert InvalidBetAmount();

        uint256 fee = (amount * platformFee) / 10000;
        uint256 netAmount = amount - fee;

        bool success = bettingToken.transferFrom(msg.sender, address(this), amount);
        if (!success) revert InsufficientAllowance();

        market.outcomePool[outcome] += netAmount;
        market.totalLiquidity += netAmount;
        market.userBets[msg.sender][outcome] += netAmount;
        market.hasBet[msg.sender] = true;

        _recalculateOdds(marketId);

        emit BetPlaced(marketId, msg.sender, outcome, amount);
    }

    /**
     * @notice Lock a market (called before game starts)
     */
    function lockMarket(uint256 marketId) external onlyOwner marketExists(marketId) {
        Market storage market = markets[marketId];
        if (market.status != MarketStatus.Active) revert MarketNotActive();
        market.status = MarketStatus.Locked;
        emit MarketLocked(marketId);
    }

    /**
     * @notice Resolve a market using oracle data
     */
    function resolveMarket(
        uint256 marketId,
        uint16 homeScore,
        uint16 awayScore
    ) external onlyOwner marketExists(marketId) {
        Market storage market = markets[marketId];
        if (market.status == MarketStatus.Resolved) revert MarketAlreadyResolved();

        Outcome winningOutcome;
        if (homeScore > awayScore) {
            winningOutcome = Outcome.HomeWin;
        } else if (awayScore > homeScore) {
            winningOutcome = Outcome.AwayWin;
        } else {
            winningOutcome = Outcome.Draw;
        }

        market.winningOutcome = winningOutcome;
        market.status = MarketStatus.Resolved;
        _removeActiveMarket(marketId);

        emit MarketResolved(marketId, winningOutcome, homeScore, awayScore);
    }

    /**
     * @notice Claim winnings from a resolved market
     */
    function claimPayout(uint256 marketId) external nonReentrant marketExists(marketId) {
        Market storage market = markets[marketId];
        if (market.status != MarketStatus.Resolved) revert MarketNotActive();
        if (!market.hasBet[msg.sender]) revert NoWinnings();

        uint256 userBet = market.userBets[msg.sender][market.winningOutcome];
        if (userBet == 0) revert NoWinnings();

        uint256 totalWinningPool = market.outcomePool[market.winningOutcome];
        uint256 payout = (userBet * market.totalLiquidity) / totalWinningPool;

        market.userBets[msg.sender][market.winningOutcome] = 0;
        bettingToken.transfer(msg.sender, payout);

        emit PayoutClaimed(marketId, msg.sender, payout);
    }

    /**
     * @notice Get market details
     */
    function getMarket(uint256 marketId) external view marketExists(marketId) returns (
        string memory gameId,
        string memory homeTeam,
        string memory awayTeam,
        uint256 scheduledTipoff,
        MarketStatus status,
        uint256 totalLiquidity,
        uint256 homeOdds,
        uint256 awayOdds,
        Outcome winningOutcome
    ) {
        Market storage market = markets[marketId];
        return (
            market.gameId, market.homeTeam, market.awayTeam,
            market.scheduledTipoff, market.status, market.totalLiquidity,
            market.homeOdds, market.awayOdds, market.winningOutcome
        );
    }

    function getUserBet(uint256 marketId, address user, Outcome outcome)
        external view marketExists(marketId) returns (uint256)
    {
        return markets[marketId].userBets[user][outcome];
    }

    function getOutcomePool(uint256 marketId, Outcome outcome)
        external view marketExists(marketId) returns (uint256)
    {
        return markets[marketId].outcomePool[outcome];
    }

    function getActiveMarkets() external view returns (uint256[] memory) {
        return activeMarketIds;
    }

    function getActiveMarketCount() external view returns (uint256) {
        return activeMarketIds.length;
    }

    function _recalculateOdds(uint256 marketId) internal {
        Market storage market = markets[marketId];
        uint256 homePool = market.outcomePool[Outcome.HomeWin];
        uint256 awayPool = market.outcomePool[Outcome.AwayWin];
        uint256 totalPool = homePool + awayPool;
        if (totalPool == 0) return;
        if (homePool > 0) market.homeOdds = (totalPool * 1e18) / homePool;
        if (awayPool > 0) market.awayOdds = (totalPool * 1e18) / awayPool;
    }

    function _removeActiveMarket(uint256 marketId) internal {
        for (uint256 i = 0; i < activeMarketIds.length; i++) {
            if (activeMarketIds[i] == marketId) {
                activeMarketIds[i] = activeMarketIds[activeMarketIds.length - 1];
                activeMarketIds.pop();
                break;
            }
        }
    }

    function setPlatformFee(uint256 fee) external onlyOwner { platformFee = fee; }
    function setMinMaxBet(uint256 _minBet, uint256 _maxBet) external onlyOwner {
        minBet = _minBet;
        maxBet = _maxBet;
    }
    function setAzuroAddresses(address _azuroCore, address _azuroProxy) external onlyOwner {
        azuroCore = _azuroCore;
        azuroProxy = _azuroProxy;
    }
}
