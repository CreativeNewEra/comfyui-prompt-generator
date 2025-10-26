# ComfyUI Prompt Generator - Makefile
# Common development tasks for easy project management

# Detect operating system
ifeq ($(OS),Windows_NT)
	PYTHON := python
	VENV_BIN := venv/Scripts
	RM := del /Q /F
	RMDIR := rmdir /S /Q
	MKDIR := mkdir
else
	PYTHON := python3
	VENV_BIN := venv/bin
	RM := rm -f
	RMDIR := rm -rf
	MKDIR := mkdir -p
endif

# Virtual environment paths
VENV := venv
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Color output for better readability
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target - show help
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)ComfyUI Prompt Generator - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  1. make install         # Set up the project"
	@echo "  2. make setup-ollama    # Get Ollama instructions"
	@echo "  3. make run             # Start the application"
	@echo ""

.PHONY: install
install: ## Create virtual environment and install all dependencies
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(BLUE)Upgrading pip...$(NC)"
	$(VENV_PIP) install --upgrade pip
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(VENV_PIP) install -r requirements.txt
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(VENV_PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Installation complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Copy .env.example to .env and configure"
	@echo "  2. Make sure Ollama is installed and running"
	@echo "  3. Run 'make run' to start the application"

.PHONY: install-prod
install-prod: ## Install only production dependencies
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(BLUE)Upgrading pip...$(NC)"
	$(VENV_PIP) install --upgrade pip
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(VENV_PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Production installation complete!$(NC)"

.PHONY: install-dev
install-dev: ## Install only development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(VENV_PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Development dependencies installed!$(NC)"

.PHONY: run
run: ## Run the Flask application in development mode
	@echo "$(BLUE)Starting ComfyUI Prompt Generator...$(NC)"
	@echo "$(YELLOW)Make sure Ollama is running: ollama serve$(NC)"
	@echo ""
	$(VENV_PYTHON) prompt_generator.py

.PHONY: test
test: ## Run the test suite with pytest
	@echo "$(BLUE)Running tests...$(NC)"
	$(VENV_BIN)/pytest -v --tb=short
	@echo "$(GREEN)✓ Tests complete!$(NC)"

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(VENV_BIN)/pytest -v --cov=prompt_generator --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

.PHONY: lint
lint: ## Run flake8 linting on the codebase
	@echo "$(BLUE)Running flake8 linting...$(NC)"
	$(VENV_BIN)/flake8 prompt_generator.py tests/
	@echo "$(GREEN)✓ Linting complete - no issues found!$(NC)"

.PHONY: lint-all
lint-all: ## Run comprehensive linting (strict mode)
	@echo "$(BLUE)Running strict linting...$(NC)"
	$(VENV_BIN)/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(VENV_BIN)/flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
	@echo "$(GREEN)✓ Comprehensive linting complete!$(NC)"

.PHONY: format
format: ## Format code using black and isort
        @echo "$(BLUE)Formatting code with isort...$(NC)"
        $(VENV_BIN)/isort prompt_generator.py tests/
        @echo "$(BLUE)Formatting code with black...$(NC)"
        $(VENV_BIN)/black prompt_generator.py tests/
        @echo "$(GREEN)✓ Formatting complete!$(NC)"

.PHONY: format-check
format-check: ## Check code formatting with black and isort
        @echo "$(BLUE)Checking import order with isort...$(NC)"
        $(VENV_BIN)/isort --check-only --diff prompt_generator.py tests/
        @echo "$(BLUE)Checking code style with black...$(NC)"
        $(VENV_BIN)/black --check prompt_generator.py tests/
        @echo "$(GREEN)✓ Formatting looks good!$(NC)"

.PHONY: clean
clean: ## Remove cache files, logs, and build artifacts
	@echo "$(BLUE)Cleaning project...$(NC)"
	@echo "Removing Python cache files..."
	@find . -type d -name "__pycache__" -exec $(RMDIR) {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.py~" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec $(RMDIR) {} + 2>/dev/null || true
	@echo "Removing test and coverage artifacts..."
	@$(RMDIR) .pytest_cache 2>/dev/null || true
	@$(RMDIR) htmlcov 2>/dev/null || true
	@$(RM) .coverage 2>/dev/null || true
	@echo "Removing logs..."
	@$(RMDIR) logs 2>/dev/null || true
	@$(RM) *.log 2>/dev/null || true
	@echo "Removing build artifacts..."
	@$(RMDIR) build 2>/dev/null || true
	@$(RMDIR) dist 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

.PHONY: clean-all
clean-all: clean ## Remove everything including virtual environment
	@echo "$(RED)Removing virtual environment...$(NC)"
	@$(RMDIR) $(VENV) 2>/dev/null || true
	@echo "$(GREEN)✓ Complete cleanup done!$(NC)"

.PHONY: setup-ollama
setup-ollama: ## Display instructions for setting up Ollama
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)           Ollama Setup Instructions$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Step 1: Install Ollama$(NC)"
	@echo "  Visit: https://ollama.ai"
	@echo "  Download and install for your operating system"
	@echo ""
	@echo "$(GREEN)Step 2: Verify Installation$(NC)"
	@echo "  Run: $(YELLOW)ollama --version$(NC)"
	@echo ""
	@echo "$(GREEN)Step 3: Start Ollama Server$(NC)"
	@echo "  Run: $(YELLOW)ollama serve$(NC)"
	@echo "  (Keep this terminal open)"
	@echo ""
	@echo "$(GREEN)Step 4: Install a Model$(NC)"
	@echo "  Recommended models:"
	@echo "    $(YELLOW)ollama pull qwen3:latest$(NC)      # Fast, good quality (4GB)"
	@echo "    $(YELLOW)ollama pull llama2$(NC)            # Balanced (4GB)"
	@echo "    $(YELLOW)ollama pull mistral$(NC)           # Good for creative tasks (4GB)"
	@echo "    $(YELLOW)ollama pull codellama$(NC)         # Technical descriptions (4GB)"
	@echo ""
	@echo "$(GREEN)Step 5: Verify Model Installation$(NC)"
	@echo "  Run: $(YELLOW)ollama list$(NC)"
	@echo ""
	@echo "$(GREEN)Step 6: Test Ollama$(NC)"
	@echo "  Run: $(YELLOW)curl http://localhost:11434$(NC)"
	@echo "  Expected: 'Ollama is running'"
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "Once Ollama is running, use $(YELLOW)make run$(NC) to start the app"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"

.PHONY: check-env
check-env: ## Check if .env file exists and Ollama is reachable
	@echo "$(BLUE)Checking environment setup...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✓ .env file found$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env file not found$(NC)"; \
		echo "  Run: cp .env.example .env"; \
	fi
	@echo "$(BLUE)Checking Ollama connection...$(NC)"
	@curl -s http://localhost:11434 > /dev/null && \
		echo "$(GREEN)✓ Ollama is running$(NC)" || \
		echo "$(RED)✗ Ollama is not running$(NC)\n  Start with: ollama serve"

.PHONY: dev
dev: check-env run ## Check environment and run the application

.PHONY: watch
watch: ## Run the application with auto-reload (requires watchdog)
	@echo "$(BLUE)Starting development server with auto-reload...$(NC)"
	@echo "$(YELLOW)Note: Flask debug mode is enabled by default$(NC)"
	$(VENV_PYTHON) prompt_generator.py

.PHONY: shell
shell: ## Open a Python shell with the application context
	@echo "$(BLUE)Opening Python shell...$(NC)"
	$(VENV_PYTHON) -i -c "from prompt_generator import app; print('App loaded. Use app variable to interact.')"

.PHONY: deps-update
deps-update: ## Update dependencies to latest versions
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(VENV_PIP) install --upgrade -r requirements.txt
	$(VENV_PIP) install --upgrade -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies updated!$(NC)"
	@echo "$(YELLOW)Don't forget to test thoroughly and update requirements.txt$(NC)"

.PHONY: deps-list
deps-list: ## List all installed packages
	@echo "$(BLUE)Installed packages:$(NC)"
	$(VENV_PIP) list

.PHONY: deps-freeze
deps-freeze: ## Generate requirements.txt from current environment
	@echo "$(BLUE)Freezing dependencies...$(NC)"
	$(VENV_PIP) freeze > requirements-frozen.txt
	@echo "$(GREEN)✓ Dependencies saved to requirements-frozen.txt$(NC)"
	@echo "$(YELLOW)Review before replacing requirements.txt$(NC)"

.PHONY: logs
logs: ## Display recent application logs
	@if [ -f logs/app.log ]; then \
		echo "$(BLUE)Recent application logs:$(NC)"; \
		tail -50 logs/app.log; \
	else \
		echo "$(YELLOW)No log file found. Run the app first.$(NC)"; \
	fi

.PHONY: logs-follow
logs-follow: ## Follow application logs in real-time
	@if [ -f logs/app.log ]; then \
		echo "$(BLUE)Following logs (Ctrl+C to stop)...$(NC)"; \
		tail -f logs/app.log; \
	else \
		echo "$(YELLOW)No log file found. Run the app first.$(NC)"; \
	fi

.PHONY: validate
validate: lint test ## Run linting and tests (CI simulation)
	@echo "$(GREEN)✓ All validation passed!$(NC)"

.PHONY: ci
ci: ## Run full CI pipeline locally
	@echo "$(BLUE)Running full CI pipeline...$(NC)"
	@make lint
	@make test
	@echo "$(GREEN)✓ CI pipeline complete!$(NC)"

.PHONY: docker-build
docker-build: ## Build Docker image (requires Dockerfile)
	@echo "$(YELLOW)Docker support not yet implemented$(NC)"
	@echo "Create a Dockerfile to enable this feature"

.PHONY: info
info: ## Display project information
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)           ComfyUI Prompt Generator$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(GREEN)Project Information:$(NC)"
	@echo "  Version:        1.0.0"
	@echo "  Python:         $(shell $(PYTHON) --version 2>&1)"
	@echo "  Virtual Env:    $(VENV)"
	@if [ -d "$(VENV)" ]; then echo "  Status:         $(GREEN)✓ Installed$(NC)"; else echo "  Status:         $(RED)✗ Not installed$(NC)"; fi
	@echo ""
	@echo "$(GREEN)Dependencies:$(NC)"
	@echo "  Production:     requirements.txt"
	@echo "  Development:    requirements-dev.txt"
	@echo ""
	@echo "$(GREEN)Quick Commands:$(NC)"
	@echo "  make help       Show all commands"
	@echo "  make install    Setup project"
	@echo "  make run        Start application"
	@echo "  make test       Run tests"
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(NC)"

.PHONY: git-status
git-status: ## Show git status and branch information
	@echo "$(BLUE)Git Status:$(NC)"
	@git status -s
	@echo ""
	@echo "$(BLUE)Current Branch:$(NC)"
	@git branch --show-current
	@echo ""
	@echo "$(BLUE)Recent Commits:$(NC)"
	@git log --oneline -5

.PHONY: backup
backup: ## Create a backup of the project (excluding venv)
	@echo "$(BLUE)Creating project backup...$(NC)"
	@BACKUP_NAME="comfyui-prompt-gen-backup-$$(date +%Y%m%d-%H%M%S).tar.gz"; \
	tar -czf $$BACKUP_NAME \
		--exclude='venv' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='logs' \
		--exclude='.git' \
		. && \
	echo "$(GREEN)✓ Backup created: $$BACKUP_NAME$(NC)"
