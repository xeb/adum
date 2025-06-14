.PHONY: help install api test clean

help: ## Show this help message
	@echo "Commands"
	@echo "---------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv pip install -e .

api: ## Start the mechArm270 API server
	python3 api.py

client: ## Start the client control interface
	python3 client.py

test: ## Run tests (placeholder)
	@echo "Tests not implemented yet"

clean: ## Clean up Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +