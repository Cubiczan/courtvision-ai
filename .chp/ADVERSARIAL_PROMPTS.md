# Adversarial Challenge Templates — courtvision-ai

## Phase 0: Foundation Challenge
When a new decision enters CHP, the adversary MUST address:
1. Why is the proposed direction wrong? (vulnerability_strike)
2. What is the system not seeing? (invalidation_conditions)
3. What is the false consensus risk?

## Domain-Specific Challenges (Blockchain / Prediction Markets)
1. What happens if the Azuro Protocol market resolution oracle reports a wrong or delayed NBA result? Settlements on Polygon are irreversible.
2. Could the Qwen LLM odds recommendations be systematically biased, and how would users detect model drift before losing funds?
3. What smart-contract failure modes exist around liquidity provision and payout — reentrancy, rounding, stuck funds on Amoy vs mainnet differences?
4. If DashScope API availability degrades mid-game, does the platform fail open (stale odds) or fail closed (no market)?
5. What is the regulatory exposure of AI-recommended sports wagering per jurisdiction, and does testnet framing actually mitigate it?

## Round 3: Implementation Drift Check
1. Does the implementation match the locked spec acceptance criteria?
2. Are operational handoffs and owner capacity accounted for?
3. Is evidence quality sufficient for the decision domain?

## Council Spawn Triggers
When confidence <85% on high-stakes decisions:
- Attacker Model 1: Challenge foundational assumptions
- Attacker Model 2: Challenge operational feasibility
- Synthesizer: Resolve contradictions and produce final recommendation
