# Règles LLM et Providers - THÉRÈSE V2

## Architecture multi-providers

THÉRÈSE supporte 6 fournisseurs LLM via une architecture de providers modulaire.

### Providers supportés

| Provider | Modèle par défaut | Tool Calling | Streaming | Grounding |
|----------|-------------------|--------------|-----------|-----------|
| Anthropic (Claude) | claude-sonnet-4-20250514 | Oui (natif) | Oui (SSE) | Non |
| OpenAI (GPT) | gpt-4o | Oui (function calling) | Oui (SSE) | Non |
| Google (Gemini) | gemini-2.0-flash | Oui | Oui | Oui (Google Search) |
| Mistral | mistral-large-latest | Oui | Oui | Non |
| Grok (xAI) | grok-3 | Oui (format OpenAI) | Oui | Non |
| Ollama | mistral:7b | Non | Oui | Non |

### Architecture des providers

```
services/providers/
├── base.py          # BaseProvider (ABC)
│   ├── stream_response()    # Méthode abstraite
│   ├── get_models()         # Liste des modèles
│   └── supports_tools()     # Capacité tool calling
├── anthropic.py     # Claude API (natif)
├── openai.py        # GPT API (function calling)
├── gemini.py        # Gemini API + Google Search
├── mistral.py       # Mistral API
├── grok.py          # Grok API (compatible OpenAI)
└── ollama.py        # Ollama local
```

### Règles d'implémentation d'un nouveau provider

1. Hériter de `BaseProvider`
2. Implémenter `stream_response()` (async generator)
3. Implémenter `get_models()` (liste statique ou dynamique)
4. Gérer le format de messages propre au provider
5. Supporter le streaming SSE
6. Gérer les erreurs spécifiques (rate limit, auth, timeout)
7. Ajouter dans le registre de providers dans `llm.py`
8. Écrire les tests unitaires

### Format de messages

Chaque provider a son propre format. Le service `ContextWindow` gère la conversion :

**Format Anthropic** :

```json
{
  "role": "user" | "assistant",
  "content": [{"type": "text", "text": "..."}]
}
```

**Format OpenAI/Grok** :

```json
{
  "role": "system" | "user" | "assistant" | "tool",
  "content": "..."
}
```

**Format Gemini** :

```json
{
  "role": "user" | "model",
  "parts": [{"text": "..."}]
}
```

### Gestion du contexte (ContextWindow)

- Budget de tokens configurable (défaut : 8000)
- Troncature automatique des messages anciens
- System prompt toujours inclus en premier
- Mémoire (contacts/projets) injectée dans le system prompt
- Fichiers indexés injectés si pertinents

---

## Tool Calling

### Outils disponibles

1. **WEB_SEARCH_TOOL** : Recherche DuckDuckGo
2. **MEMORY_TOOLS** : Recherche contacts/projets dans la mémoire
3. **MCP_TOOLS** : Outils dynamiques des serveurs MCP

### Flux d'exécution des outils

1. Message utilisateur envoyé au LLM avec les définitions d'outils
2. LLM décide d'appeler un outil (ou pas)
3. Si outil appelé : exécution côté serveur
4. Résultat renvoyé au LLM comme message tool_result
5. LLM génère la réponse finale intégrant le résultat
6. Maximum 5 itérations d'outils par message

### Format de définition d'outil (Anthropic)

```json
{
  "name": "web_search",
  "description": "Recherche sur le web via DuckDuckGo",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Requête de recherche"}
    },
    "required": ["query"]
  }
}
```

### Format de définition d'outil (OpenAI/function calling)

```json
{
  "type": "function",
  "function": {
    "name": "web_search",
    "description": "Recherche sur le web via DuckDuckGo",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"}
      },
      "required": ["query"]
    }
  }
}
```

---

## Streaming SSE

### Format des événements

```
event: chunk
data: {"type": "token", "content": "Bonjour"}

event: chunk
data: {"type": "tool_result", "tool_name": "web_search", "content": "..."}

event: chunk
data: {"type": "entities_detected", "contacts": [...], "projects": [...]}

event: chunk
data: {"type": "status", "content": "done", "usage": {...}, "uncertainty": {...}}
```

### Règles de streaming

- Chaque token est envoyé individuellement via SSE
- Le frontend accumule les tokens pour le rendu Markdown
- Les tool_result sont envoyés comme événements séparés
- Le statut "done" marque la fin du stream
- Usage (tokens, coût) envoyé avec le statut final
- Annulation possible via flag `_active_generations`

---

## Intégration MCP (Model Context Protocol)

### 19 presets organisés par tier

**Tier 1 (sans clé API)** : Filesystem, Fetch, Time, Sequential Thinking

**Tier 2 (Google)** : Google Workspace, Notion, Airtable

**Tier 3 (APIs externes)** : GitHub, Slack, HubSpot, Todoist, Brave Search, Stripe, WhatsApp, etc.

### Règles MCP

- Transport stdio (JSON-RPC 2.0)
- Découverte automatique des outils au démarrage du serveur
- Variables d'environnement chiffrées au repos
- Timeout de 60s pour les requêtes en attente
- Nettoyage automatique des serveurs morts
- Logs stderr capturés en async

---

## Board de décision (5 conseillers)

### Rôles et personnalités

1. **L'Analyste** : Analyse structurée, données, métriques (Claude)
2. **Le Stratège** : Vision créative, opportunités, positionnement (GPT)
3. **L'Avocat du Diable** : Objections, risques, failles (Claude)
4. **Le Pragmatique** : Faisabilité, ressources, étapes concrètes (Mistral)
5. **Le Visionnaire** : Tendances, futur, innovation (Gemini)

### Flux de délibération

1. Question posée aux 5 conseillers en parallèle (streaming)
2. Chaque conseiller donne son avis avec son style
3. Synthèse automatique générée (consensus + divergences)
4. Score de confiance calculé
5. Décision persistée en base (historique consultable)

---

## Extraction d'entités

### Flux automatique

1. Après chaque réponse LLM, extraction en arrière-plan
2. Le LLM identifie contacts et projets mentionnés
3. Seuil de confiance : 0.6 minimum
4. Déduplication contre les entités existantes
5. Suggestions envoyées au frontend via SSE (`entities_detected`)
6. L'utilisateur valide ou ignore les suggestions

---

## Gestion des clés API

- Stockage chiffré en base SQLite (Fernet)
- Clé maître dans le Trousseau macOS
- Cache en mémoire pour éviter le déchiffrement répété
- Fallback sur variables d'environnement
- Validation de la clé avant sauvegarde (appel test au provider)

---

## Gestion des erreurs LLM

- Rate limit (429) : Retry avec backoff exponentiel
- Auth error (401/403) : Notification à l'utilisateur
- Timeout : Retry une fois, puis erreur
- Context overflow : Troncature automatique et retry
- Provider indisponible : Suggestion de provider alternatif
- Réponse vide : Retry avec température ajustée

---

## Métriques et coûts

- Tokens consommés trackés par message (input + output)
- Coût estimé en EUR par provider
- Latence du premier token mesurée
- Historique d'utilisation (quotidien/mensuel)
- Limites configurables par l'utilisateur
- Alerte quand 80% du budget atteint

---

## Anti-patterns à éviter

- Jamais envoyer de clé API au frontend
- Jamais de prompt système modifiable par l'utilisateur
- Jamais plus de 5 itérations d'outils par message
- Jamais de stream non terminé (toujours envoyer `status:done`)
- Jamais logger le contenu des conversations
- Pas de fallback silencieux entre providers (toujours informer l'utilisateur)
