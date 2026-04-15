SHELL := /bin/bash

.PHONY: help proto test lint

help:
	@echo "Targets:"
	@echo "  proto  - generate protobuf stubs via buf"
	@echo "  test   - run pytest"
	@echo "  lint   - (placeholder) run ruff"

proto:
	buf mod update
	buf generate

test:
	python -m pytest -q

lint:
	@echo "ruff not wired yet (install ruff and add config if desired)"
