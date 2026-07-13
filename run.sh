#!/usr/bin/env bash
set -euo pipefail

uv sync
uv run flask run --reload
