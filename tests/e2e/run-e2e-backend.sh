#!/usr/bin/env bash
# Backend E2E jetable (revue 0.40) : port dédié + THERESE_DATA_DIR temporaire,
# détruit en fin de suite. Lancé par le webServer de playwright.config.ts.
set -euo pipefail

PORT="${THERESE_E2E_PORT:-17393}"
if [ "$PORT" = "17293" ]; then
  echo "E2E interdits sur le port 17293 (instance THÉRÈSE réelle)" >&2
  exit 1
fi

# Data dir DÉTERMINISTE par port : purgé ici à chaque départ, détruit en fin
# de suite par le globalTeardown Playwright (le SIGKILL de Playwright sur ce
# shell court-circuite le trap - le teardown Node, lui, s'exécute toujours).
DATA_DIR="${TMPDIR:-/tmp}/therese-e2e-$PORT"
rm -rf "$DATA_DIR"
mkdir -p "$DATA_DIR"
export THERESE_DATA_DIR="$DATA_DIR"

# ------------------------------------------------------------------
# Hermétisme des fournisseurs de modèle (B-265, 03/09/2026).
#
# Deux parcours du premier lancement passaient ici et échouaient sur le
# runner : le composeur y était désactivé, avec « Aucun modèle actif ne peut
# répondre ». La suite ne testait pas la même application des deux côtés,
# parce que ce backend héritait de l'environnement du shell qui le lance -
# une clé de fournisseur exportée dans le profil de connexion, et surtout un
# Ollama qui tourne sur le poste. `_available_models_for("ollama")` interroge
# `settings.ollama_base_url` : un Ollama vivant suffisait à rendre le modèle
# « disponible » en local et nulle part ailleurs.
#
# La machine ne doit plus rien dire au test. On coupe donc les deux sources :
# les variables de clés (celles du catalogue `modeles_catalogue.py`, plus
# celles des services voisins - images, dictée, recherche web) et l'adresse
# d'Ollama, poussée sur le port 9 (« discard »), fermé par convention : la
# connexion est refusée tout de suite au lieu d'expirer au bout de cinq
# secondes à chaque appel.
#
# Ce que les parcours exigent, ils le posent eux-mêmes par l'API du backend
# jetable (`poserUnModeleActif`, helpers/surfaces.ts). Un test qui dépend de
# ce qui traîne sur la machine ne prouve rien.
# ------------------------------------------------------------------
for cle in \
  ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY GOOGLE_API_KEY \
  MISTRAL_API_KEY XAI_API_KEY OPENROUTER_API_KEY PERPLEXITY_API_KEY \
  GLM_API_KEY KIMI_API_KEY QWEN_API_KEY MINIMAX_API_KEY \
  DEEPSEEK_API_KEY INFOMANIAK_API_KEY \
  OPENAI_IMAGE_API_KEY GEMINI_IMAGE_API_KEY FAL_API_KEY \
  GROQ_API_KEY BRAVE_API_KEY SEARXNG_URL OPENCLAW_API_URL
do
  unset "$cle"
done
export OLLAMA_BASE_URL="http://127.0.0.1:9"
# La sonde de dérive du catalogue (0.48) appelle /models chez un fournisseur
# cloud une fois par jour : rien ne doit sortir d'ici.
export THERESE_SONDE_CATALOGUE="off"

# pydantic-settings lit un `.env` relatif au dossier courant, qui est la
# racine du dépôt (cd plus bas). Il n'y en a pas aujourd'hui ; s'il en
# apparaît un, il rouvrirait exactement la fuite qu'on vient de fermer.
if [ -f "$(dirname "$0")/../../.env" ]; then
  echo "[e2e-backend] ATTENTION : un .env à la racine peut réintroduire des clés de fournisseur" >&2
fi

cleanup() {
  if [ -n "${UVICORN_PID:-}" ]; then
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
  fi
  rm -rf "$DATA_DIR"
}
# PAS de `exec` : le shell doit survivre à uvicorn pour exécuter ce trap.
trap cleanup EXIT INT TERM

cd "$(dirname "$0")/../.."
echo "[e2e-backend] port $PORT, données jetables : $DATA_DIR"
uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --app-dir src/backend &
UVICORN_PID=$!
wait "$UVICORN_PID"
