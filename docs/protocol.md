# Protocol

1. Prover sends claim (`claim_received`).
2. Leader issues randomized challenge (`challenge_issued`).
3. Prover executes (`executing`).
4. Verifier observes (`verifying`) via camera + telemetry mock.
5. Trust score computed with configured weights.
6. Verdict decides `passed` or `failed`.
