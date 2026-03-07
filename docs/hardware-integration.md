# Hardware Integration (LeRobot + SO-101)

Use `hardware/lerobot_so101_stub.py` as the integration point.

## Mapping plan
- `SO101LeaderLeRobotAdapter.generate_challenge`: map challenge intent to leader arm pose trajectory generation.
- `SO101ProverLeRobotAdapter.execute_challenge`: execute generated challenge over LeRobot motion API.
- `SO101VerifierLeRobotAdapter.observe_execution`: gather joint/pose/current telemetry and compute observation metrics.
- `SO101CameraLeRobotAdapter.capture_frame`: capture + process verifier camera frames.

## Contract
All adapters implement `hardware/interfaces.py` protocols to keep the protocol/scoring layers unchanged between simulation and real hardware.
