# Architecture

Core modules:
- `protocol/session_manager.py`: orchestrates PCS workflow
- `state_machine.py`: transition validation
- `simulation/engine.py`: deterministic simulated telemetry
- `scoring/trust.py`: trust score and verdict logic
- `api/app.py`: REST/WebSocket/dashboard endpoints
- `persistence/repository.py`: SQLite session + event storage
- `hardware/*`: LeRobot-oriented interfaces/adapters
