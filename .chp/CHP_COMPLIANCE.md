# CHP Compliance — courtvision-ai

## Hardening Status: CHAP-v1 APPLIED
## Applied: 2026-07-03
## CHP Version: cognitive-mesh-orchestrator 0.1.0

### Checklist
- [x] .chp/STATE_MACHINE.md deployed
- [x] .chp/R0_CONFIG.yaml configured for Blockchain / Prediction Markets
- [x] .chp/ADVERSARIAL_PROMPTS.md with domain challenges
- [x] .chp/CHP_COMPLIANCE.md tracking enabled
- [x] CI/CD workflow with CHP gates

### Domain Configuration
- Category: Blockchain / Prediction Markets
- Foundation Threshold: 85
- CFO Accuracy Guard: DISABLED
- R0 Worth_it: True

### Audit Trail
All CHP sessions are logged in .chp_registry.json with:
- Decision ID, session status, foundation score
- Devil's advocate rounds and findings
- Third-party validation results
- State snapshots at each round boundary
