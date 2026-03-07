# Demo Runbook

## Local
1. `make install`
2. `make dev`
3. Open http://localhost:8000
4. Create normal/replay/delay sessions from dashboard and step through claim/challenge/execute/verify.
5. Use CLI for dedicated watermark demos focused on micromovement encoding and cross-camera hat detection.

## CLI
- Normal: `trust-before-touch run-demo --mode normal`
- Replay: `trust-before-touch run-demo --mode replay`
- Delay: `trust-before-touch run-demo --mode delay`
- Training watermark with micromovement: `trust-before-touch run-training-watermark-demo`
- Cross-camera hat watermark verification: `trust-before-touch run-cross-camera-watermark-demo`
