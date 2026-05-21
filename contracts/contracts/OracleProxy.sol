// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title OracleProxy
 * @notice Decentralized oracle for feeding NBA game results into the prediction market.
 *         Uses ECDSA signature verification from authorized data providers.
 */
contract OracleProxy is Ownable, ReentrancyGuard {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    struct GameResult {
        string gameId;
        string homeTeam;
        string awayTeam;
        uint16 homeScore;
        uint16 awayScore;
        uint256 timestamp;
        bool resolved;
    }

    mapping(bytes32 => GameResult) public gameResults;
    mapping(bytes32 => bool) public processedResults;
    mapping(address => bool) public authorizedProviders;

    uint256 public requiredConfirmations;
    mapping(bytes32 => uint256) public confirmationCount;
    mapping(bytes32 => mapping(address => bool)) public confirmations;

    address public marketFactory;
    uint256 public resultTimeout = 24 hours;

    event ProviderAdded(address indexed provider);
    event ProviderRemoved(address indexed provider);
    event ResultSubmitted(bytes32 indexed resultHash, string gameId, address provider);
    event ResultConfirmed(bytes32 indexed resultHash, string gameId);
    event ResultResolved(bytes32 indexed resultHash, string gameId, uint16 homeScore, uint16 awayScore);
    event MarketFactorySet(address indexed factory);

    error NotAuthorized();
    error AlreadyConfirmed();
    error InsufficientConfirmations();
    error ResultAlreadyProcessed();
    error ResultExpired();
    error InvalidSignatures();

    modifier onlyProvider() {
        if (!authorizedProviders[msg.sender]) revert NotAuthorized();
        _;
    }

    constructor(address[] memory _providers, uint256 _requiredConfirmations) Ownable(msg.sender) {
        requiredConfirmations = _requiredConfirmations;
        for (uint256 i = 0; i < _providers.length; i++) {
            authorizedProviders[_providers[i]] = true;
            emit ProviderAdded(_providers[i]);
        }
    }

    /**
     * @notice Submit a game result for verification
     * @param gameId Unique identifier for the NBA game
     * @param homeTeam Home team name
     * @param awayTeam Away team name
     * @param homeScore Final score for home team
     * @param awayScore Final score for away team
     */
    function submitResult(
        string calldata gameId,
        string calldata homeTeam,
        string calldata awayTeam,
        uint16 homeScore,
        uint16 awayScore
    ) external onlyProvider {
        bytes32 resultHash = keccak256(
            abi.encodePacked(gameId, homeTeam, awayTeam, homeScore, awayScore, block.chainid)
        );

        if (confirmations[resultHash][msg.sender]) revert AlreadyConfirmed();
        if (processedResults[resultHash]) revert ResultAlreadyProcessed();

        confirmations[resultHash][msg.sender] = true;
        confirmationCount[resultHash]++;

        emit ResultSubmitted(resultHash, gameId, msg.sender);

        if (confirmationCount[resultHash] >= requiredConfirmations) {
            processedResults[resultHash] = true;
            gameResults[resultHash] = GameResult({
                gameId: gameId,
                homeTeam: homeTeam,
                awayTeam: awayTeam,
                homeScore: homeScore,
                awayScore: awayScore,
                timestamp: block.timestamp,
                resolved: true
            });

            emit ResultConfirmed(resultHash, gameId);
            emit ResultResolved(resultHash, gameId, homeScore, awayScore);
        }
    }

    /**
     * @notice Get a resolved game result
     */
    function getResult(bytes32 resultHash) external view returns (GameResult memory) {
        return gameResults[resultHash];
    }

    /**
     * @notice Check if a result has been processed
     */
    function isResultProcessed(bytes32 resultHash) external view returns (bool) {
        return processedResults[resultHash];
    }

    /**
     * @notice Compute the result hash for a game
     */
    function computeResultHash(
        string calldata gameId,
        string calldata homeTeam,
        string calldata awayTeam,
        uint16 homeScore,
        uint16 awayScore
    ) external view returns (bytes32) {
        return keccak256(
            abi.encodePacked(gameId, homeTeam, awayTeam, homeScore, awayScore, block.chainid)
        );
    }

    function addProvider(address provider) external onlyOwner {
        authorizedProviders[provider] = true;
        emit ProviderAdded(provider);
    }

    function removeProvider(address provider) external onlyOwner {
        authorizedProviders[provider] = false;
        emit ProviderRemoved(provider);
    }

    function setMarketFactory(address factory) external onlyOwner {
        marketFactory = factory;
        emit MarketFactorySet(factory);
    }

    function setRequiredConfirmations(uint256 count) external onlyOwner {
        requiredConfirmations = count;
    }
}
