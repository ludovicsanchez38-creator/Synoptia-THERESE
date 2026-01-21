.PHONY: dev install test lint clean build

# Variables
BACKEND_DIR = src/backend
FRONTEND_DIR = src/frontend

# Développement
dev:
	@echo "🚀 Lancement THÉRÈSE en mode dev..."
	@cd $(BACKEND_DIR) && uv run uvicorn main:app --reload --port 8000 &
	@cd $(FRONTEND_DIR) && npm run dev

dev-backend:
	@echo "🐍 Lancement backend seul..."
	@cd $(BACKEND_DIR) && uv run uvicorn main:app --reload --port 8000

dev-frontend:
	@echo "⚛️  Lancement frontend seul..."
	@cd $(FRONTEND_DIR) && npm run dev

# Installation
install:
	@echo "📦 Installation des dépendances..."
	@cd $(BACKEND_DIR) && uv sync
	@cd $(FRONTEND_DIR) && npm install
	@echo "✅ Installation terminée"

install-backend:
	@echo "📦 Installation backend..."
	@cd $(BACKEND_DIR) && uv sync

install-frontend:
	@echo "📦 Installation frontend..."
	@cd $(FRONTEND_DIR) && npm install

# Tests
test:
	@echo "🧪 Lancement des tests..."
	@cd $(BACKEND_DIR) && uv run pytest -v
	@cd $(FRONTEND_DIR) && npm test

test-backend:
	@echo "🧪 Tests backend..."
	@cd $(BACKEND_DIR) && uv run pytest -v

test-frontend:
	@echo "🧪 Tests frontend..."
	@cd $(FRONTEND_DIR) && npm test

# Lint
lint:
	@echo "🔍 Vérification du code..."
	@cd $(BACKEND_DIR) && uv run ruff check .
	@cd $(FRONTEND_DIR) && npm run lint

lint-fix:
	@echo "🔧 Correction automatique..."
	@cd $(BACKEND_DIR) && uv run ruff check --fix .
	@cd $(FRONTEND_DIR) && npm run lint:fix

# Build
build:
	@echo "🏗️  Build de production..."
	@cd $(FRONTEND_DIR) && npm run build

# Clean
clean:
	@echo "🧹 Nettoyage..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .venv -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

# Help
help:
	@echo "THÉRÈSE v2 - Commandes disponibles"
	@echo ""
	@echo "  make dev          - Lancer en mode développement"
	@echo "  make dev-backend  - Lancer le backend seul"
	@echo "  make dev-frontend - Lancer le frontend seul"
	@echo "  make install      - Installer les dépendances"
	@echo "  make test         - Lancer les tests"
	@echo "  make lint         - Vérifier le code"
	@echo "  make lint-fix     - Corriger le code automatiquement"
	@echo "  make build        - Build de production"
	@echo "  make clean        - Nettoyer les fichiers générés"
	@echo "  make help         - Afficher cette aide"
