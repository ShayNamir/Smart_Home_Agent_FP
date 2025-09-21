# Smart Home AI Agent Research Project Makefile

.PHONY: help install install-dev test test-unit test-integration lint format clean run-demo run-arch-bench run-model-bench setup-ollama

# Default target
help:
	@echo "Smart Home AI Agent Research Project"
	@echo "===================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black and isort"
	@echo "  clean            Clean up temporary files"
	@echo "  run-demo         Run interactive demo"
	@echo "  run-arch-bench   Run architecture benchmark"
	@echo "  run-model-bench  Run model benchmark"
	@echo "  setup-ollama     Setup Ollama models"
	@echo ""

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Testing targets
test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m "unit"

test-integration:
	pytest tests/ -v -m "integration"

test-coverage:
	pytest tests/ --cov=agent_runner --cov=core --cov=Arch --cov-report=html --cov-report=term

# Code quality targets
lint:
	flake8 agent_runner.py core/ Arch/ architecture_benchmark/ benchmark_models/ tests/
	mypy agent_runner.py core/ Arch/ architecture_benchmark/ benchmark_models/

format:
	black agent_runner.py core/ Arch/ architecture_benchmark/ benchmark_models/ tests/
	isort agent_runner.py core/ Arch/ architecture_benchmark/ benchmark_models/ tests/

# Cleanup targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Run targets
run-demo:
	python main.py

run-arch-bench:
	cd architecture_benchmark && python arch_benchmark.py

run-model-bench:
	cd benchmark_models && python benchmark_runner.py

# Setup targets
setup-ollama:
	@echo "Setting up Ollama models..."
	ollama pull phi3:mini
	ollama pull llama3.2
	ollama pull mistral
	ollama pull qwen3:4b
	ollama pull gemma3:4b
	ollama pull deepseek-r1:1.5b
	@echo "Ollama models setup complete!"

# Development targets
dev-setup: install-dev setup-ollama
	@echo "Development environment setup complete!"

# Benchmark targets
benchmark-quick:
	cd architecture_benchmark && python arch_benchmark.py
	@echo "Choose: micro profile, core architectures"

benchmark-full:
	cd architecture_benchmark && python arch_benchmark.py
	@echo "Choose: long profile, all architectures"

model-benchmark-quick:
	cd benchmark_models && python benchmark_runner.py
	@echo "Choose: micro profile, 2 models"

model-benchmark-full:
	cd benchmark_models && python benchmark_runner.py
	@echo "Choose: long profile, all models"

# Documentation targets
docs:
	@echo "Generating documentation..."
	@echo "Documentation is in README.md and individual module docstrings"

# Release targets
check-release:
	python -m build --check

build:
	python -m build

# Docker targets (if needed)
docker-build:
	docker build -t smart-home-ai-agent .

docker-run:
	docker run -it smart-home-ai-agent

# Help for specific targets
help-install:
	@echo "Installation targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  dev-setup    - Complete development setup"

help-test:
	@echo "Testing targets:"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage    - Run tests with coverage report"

help-benchmark:
	@echo "Benchmark targets:"
	@echo "  benchmark-quick        - Quick architecture benchmark"
	@echo "  benchmark-full         - Full architecture benchmark"
	@echo "  model-benchmark-quick  - Quick model benchmark"
	@echo "  model-benchmark-full   - Full model benchmark"

help-run:
	@echo "Run targets:"
	@echo "  run-demo         - Run interactive demo"
	@echo "  run-arch-bench   - Run architecture benchmark"
	@echo "  run-model-bench  - Run model benchmark"
