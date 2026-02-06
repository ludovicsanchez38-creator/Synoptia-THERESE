.PHONY: dev install test lint clean build build-sidecar build-release db-migrate tauri

# Variables
BACKEND_DIR = src/backend
FRONTEND_DIR = src/frontend
VENV = .venv/bin

# Développement
dev:
	@echo "🚀 Lancement THÉRÈSE en mode dev..."
	@$(VENV)/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir $(BACKEND_DIR) &
	@cd $(FRONTEND_DIR) && npm run tauri dev

dev-backend:
	@echo "🐍 Lancement backend seul..."
	@$(VENV)/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir $(BACKEND_DIR)

dev-frontend:
	@echo "⚛️  Lancement frontend seul (sans Tauri)..."
	@cd $(FRONTEND_DIR) && npm run dev

tauri:
	@echo "🦀 Lancement Tauri (frontend + Rust)..."
	@cd $(FRONTEND_DIR) && npm run tauri dev

# Installation
install:
	@echo "📦 Installation des dépendances..."
	@uv sync
	@cd $(FRONTEND_DIR) && npm install
	@echo "✅ Installation terminée"

install-backend:
	@echo "📦 Installation backend..."
	@uv sync

install-frontend:
	@echo "📦 Installation frontend..."
	@cd $(FRONTEND_DIR) && npm install

# Database migrations
db-migrate:
	@echo "🗃️  Running database migrations..."
	@cd $(BACKEND_DIR) && $(CURDIR)/$(VENV)/alembic upgrade head

db-revision:
	@echo "🗃️  Creating new migration..."
	@cd $(BACKEND_DIR) && $(CURDIR)/$(VENV)/alembic revision --autogenerate -m "$(MSG)"

db-history:
	@cd $(BACKEND_DIR) && $(CURDIR)/$(VENV)/alembic history

# Tests
test:
	@echo "🧪 Lancement des tests..."
	@$(VENV)/pytest tests/ -v
	@cd $(FRONTEND_DIR) && npm test

test-backend:
	@echo "🧪 Tests backend..."
	@$(VENV)/pytest tests/ -v --ignore=tests/e2e

test-frontend:
	@echo "🧪 Tests frontend..."
	@cd $(FRONTEND_DIR) && npm test

test-e2e:
	@echo "🎭 Tests E2E (Playwright)..."
	@$(VENV)/pytest tests/e2e/ -v

test-e2e-headed:
	@echo "🎭 Tests E2E avec navigateur visible..."
	@$(VENV)/pytest tests/e2e/ -v --headed --slowmo 1000

install-e2e:
	@echo "📦 Installation dépendances E2E..."
	@uv pip install -e ".[e2e]"
	@$(VENV)/playwright install chromium
	@echo "✅ E2E prêt"

# Lint
lint:
	@echo "🔍 Vérification du code..."
	@$(VENV)/ruff check $(BACKEND_DIR)
	@cd $(FRONTEND_DIR) && npm run lint

lint-fix:
	@echo "🔧 Correction automatique..."
	@$(VENV)/ruff check --fix $(BACKEND_DIR)
	@cd $(FRONTEND_DIR) && npm run lint --fix

typecheck:
	@echo "🔍 Vérification TypeScript..."
	@cd $(FRONTEND_DIR) && npx tsc --noEmit

# Build
build:
	@echo "🏗️  Build de production..."
	@cd $(FRONTEND_DIR) && npm run tauri build

build-sidecar:
	@echo "📦 Build du sidecar backend (PyInstaller)..."
	@bash scripts/build-sidecar.sh

build-release: build-sidecar build
	@echo "✅ Build release complète (sidecar + Tauri)"

build-web:
	@echo "🏗️  Build frontend web..."
	@cd $(FRONTEND_DIR) && npm run build

# Clean
clean:
	@echo "🧹 Nettoyage..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/src-tauri/target 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

reset-sandbox:
	@echo "🧹 Reset sandbox E2E..."
	@rm -rf ~/.therese-test-sandbox
	@echo "✅ Sandbox réinitialisé"

reset-onboarding:
	@echo "🔄 Reset onboarding..."
	@sqlite3 ~/.therese/therese.db "DELETE FROM preferences WHERE key = 'onboarding_complete';"
	@echo "✅ Onboarding réinitialisé - relancer THÉRÈSE"

clean-all: clean
	@echo "🧹 Nettoyage complet..."
	@rm -rf node_modules 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/node_modules 2>/dev/null || true
	@rm -rf .venv 2>/dev/null || true
	@echo "✅ Nettoyage complet terminé"

# Help
help:
	@echo "THÉRÈSE v2 - Commandes disponibles"
	@echo ""
	@echo "  make dev              - Lancer backend + Tauri"
	@echo "  make dev-backend      - Lancer le backend seul"
	@echo "  make dev-frontend     - Lancer le frontend seul (Vite)"
	@echo "  make tauri            - Lancer Tauri uniquement"
	@echo "  make install          - Installer les dépendances"
	@echo "  make install-e2e      - Installer dépendances E2E (Playwright)"
	@echo "  make db-migrate       - Appliquer les migrations"
	@echo "  make db-revision MSG='description' - Créer une migration"
	@echo "  make test             - Lancer tous les tests"
	@echo "  make test-backend     - Tests backend uniquement"
	@echo "  make test-e2e         - Tests E2E (headless)"
	@echo "  make test-e2e-headed  - Tests E2E (navigateur visible)"
	@echo "  make lint             - Vérifier le code"
	@echo "  make lint-fix         - Corriger le code"
	@echo "  make typecheck        - Vérifier les types TypeScript"
	@echo "  make build            - Build de production (Tauri)"
	@echo "  make build-sidecar    - Build du sidecar backend (PyInstaller)"
	@echo "  make build-release    - Build complète (sidecar + Tauri)"
	@echo "  make clean            - Nettoyer les fichiers générés"
	@echo "  make clean-all        - Nettoyage complet (node_modules, venv)"
	@echo "  make reset-sandbox    - Reset environnement test E2E"
	@echo "  make reset-onboarding - Reset onboarding pour tests"
	@echo "  make help             - Afficher cette aide"
