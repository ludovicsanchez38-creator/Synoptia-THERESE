# Chantier B — Script de test human-like (pour Syn, 2e regard)

But : valider en conditions réelles l'unification des contacts (Mémoire ↔ CRM), la Mémoire in-window, et la recherche sémantique. **Sur la branche `chantier-revue-produit`.**

## Setup ISOLÉ (ne pas toucher aux vraies données ~/.therese)
```bash
cd <repo>/Synoptia-THERESE
git fetch && git checkout chantier-revue-produit
# Backend isolé sur un port + base jetable :
THERESE_DATA_DIR=/tmp/therese-test-B uv run uvicorn app.main:app --host 127.0.0.1 --port 17393 --app-dir src/backend &
# Pointer temporairement le front sur 17393 : éditer src/frontend/src/services/api/core.ts ligne 9 -> 17393
cd src/frontend && npm run dev    # Vite :1420
```
Ouvrir Chrome sur http://localhost:1420 (Chrome MCP). Note : en navigateur (hors Tauri), certaines API natives (file drop) loguent des erreurs sans gravité ; c'est attendu.
**À la fin : `git checkout src/frontend/src/services/api/core.ts` (revert du port) + arrêter le backend + jeter `/tmp/therese-test-B`.**

## Tests à dérouler (cocher)
1. **Boot** : l'app passe le splash et l'onboarding sans crash. [ ]
2. **P4 — création CRM visible en Mémoire** :
   - Ouvrir le CRM (⌘P), créer un contact (avec une source/prospect). [ ]
   - Ouvrir la Mémoire (⌘M) : le **même contact apparaît** (la Mémoire montre tous les contacts). [ ]
3. **P4 — création depuis le chat visible des deux côtés** :
   - Dans le chat, faire détecter un contact (ou via la modale +), le sauvegarder. [ ]
   - Vérifier qu'il apparaît en Mémoire immédiatement (sans recharger). [ ]
4. **P3 — Mémoire in-window** :
   - Le bouton Mémoire du header ouvre un **panneau dans la fenêtre** (pas une nouvelle fenêtre). [ ]
   - Aucun "bouton mort" / aucune fenêtre Mémoire détachée. [ ]
5. **P5 — recherche sémantique** (nécessite Qdrant + Ollama embeddings lancés) :
   - Taper une requête par **rôle/contexte** (pas juste le nom) dans la recherche Mémoire. [ ]
   - Vérifier que ça interroge `/api/memory/search` (onglet réseau) et renvoie des résultats pertinents. [ ]
   - Requête vide → retour à la liste complète. [ ]
6. **Pas de faux succès** : une création qui échouerait (couper le backend) ne doit PAS afficher le contact comme créé. [ ]

## Verdict attendu
Reporter : OK / KO par point, captures à l'appui, et tout écart de cohérence Mémoire↔CRM. Synthèse à remonter à Ludo + dans le hub agents.
