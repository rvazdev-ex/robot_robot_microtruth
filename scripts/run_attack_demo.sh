#!/usr/bin/env bash
set -euo pipefail
trust-before-touch run-demo --mode replay
trust-before-touch run-demo --mode delay
