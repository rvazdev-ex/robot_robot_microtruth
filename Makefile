PYTHON ?= python3.10

install:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e .[dev]

install-lerobot:
	$(PYTHON) -m pip install -e .[dev,lerobot]

dev:
	uvicorn trust_before_touch.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src

format:
	ruff check --fix src tests

# --- Real-time robot control ---

teleoperate:
	trust-before-touch teleoperate --backend lerobot

teleoperate-sim:
	trust-before-touch teleoperate --backend simulation

record:
	trust-before-touch record --backend lerobot --duration 10

read-joints:
	trust-before-touch read-joints --backend lerobot

# --- PCS verification demos ---

demo:
	trust-before-touch run-demo --mode normal

attack-demo:
	trust-before-touch run-demo --mode replay
	trust-before-touch run-demo --mode delay

watermark-demo:
	trust-before-touch run-training-watermark-demo
	trust-before-touch run-cross-camera-watermark-demo
