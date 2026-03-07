PYTHON ?= python3

install:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e .[dev]

dev:
	uvicorn trust_before_touch.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src

demo:
	trust-before-touch run-demo --mode normal

attack-demo:
	trust-before-touch run-demo --mode replay
	trust-before-touch run-demo --mode delay

watermark-demo:
	trust-before-touch run-training-watermark-demo
	trust-before-touch run-cross-camera-watermark-demo

format:
	ruff check --fix src tests
