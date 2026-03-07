# Threat Model

Covered attack simulations:
- **Replay attack**: stale trajectory/signature replay. Marked via `replay_signature_match` and severe score penalty.
- **Delay attack**: induced timing jitter/lag. Marked via `delay_flag` and score penalty.

Out-of-scope:
- Hardware tampering
- Side-channel attacks
- Sensor spoofing with adversarial image generation
