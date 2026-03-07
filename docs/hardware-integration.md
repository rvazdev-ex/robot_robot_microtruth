# Hardware Integration (LeRobot + SO-101)

Use `hardware/lerobot_so101_stub.py` and `hardware/factory.py` as runtime integration points.

## Runtime backend selection
- `runtime_backend=simulation` (default): deterministic simulation adapters.
- `runtime_backend=lerobot`: LeRobot-backed adapter set for real SO-101 execution.

Set via environment variable:
- `TBT_RUNTIME_BACKEND=simulation|lerobot`

## Adapter responsibilities
- `SO101LeaderLeRobotAdapter.generate_challenge`: challenge generation and LeRobot runtime availability checks.
- `SO101ProverLeRobotAdapter.execute_challenge`: execute generated challenge over LeRobot motion transport.
- `SO101VerifierLeRobotAdapter.observe_execution`: collect runtime/camera-derived telemetry.
- `SO101CameraLeRobotAdapter.capture_frame`: retrieve camera observations for verification.

## Contract
All adapters implement `hardware/interfaces.py` protocols to keep the protocol/scoring layers unchanged between simulation and real hardware.

## Default hardware mapping
Use the HuggingFace LeRobot adapters with the following default device mapping:

- Leader arm: `/dev/ttyACM1`
- Follower arm (with camera): `/dev/ttyACM0`
- Follower arm (without camera): `/dev/ttyACM2`
- Camera device: `/dev/video2`

These defaults are exposed as config fields and environment variables:
`TBT_LEROBOT_LEADER_ARM_PORT`, `TBT_LEROBOT_FOLLOWER_WITH_CAMERA_PORT`,
`TBT_LEROBOT_FOLLOWER_WITHOUT_CAMERA_PORT`, and `TBT_LEROBOT_CAMERA_DEVICE`.
