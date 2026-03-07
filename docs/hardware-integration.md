# Hardware Integration (LeRobot + SO-101)

Use `hardware/lerobot_so101_stub.py` as the integration point.

## Mapping plan
- `SO101LeaderLeRobotAdapter.generate_challenge`: map challenge intent to leader arm pose trajectory generation.
- `SO101ProverLeRobotAdapter.execute_challenge`: execute generated challenge over LeRobot motion API.
- `SO101VerifierLeRobotAdapter.observe_execution`: gather joint/pose/current telemetry and compute observation metrics.
- `SO101CameraLeRobotAdapter.capture_frame`: capture + process verifier camera frames.

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

