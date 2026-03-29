Parfait ! J'ai maintenant une vue complète du projet. Laissez-moi générer les user stories :

## SCRIBE INTÉGRATIONS - USER STORIES THÉRÈSE v2

Voici les user stories reconstituées pour les intégrations **Multi-provider LLM**, **Voix**, **MCP** et **Brave Search** de THÉRÈSE :

---

### US-900 : Sélectionner et basculer entre 10 providers LLM

**En tant que** solopreneur/TPE
**Je veux** sélectionner parmi 10 providers LLM (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Perplexity, DeepSeek, Infomaniak, Ollama)
**Afin de** adapter le fournisseur selon ma disponibilité de crédits et les capacités recherchées

**Critères d'acceptation :**
- [ ] Sélection du provider persiste dans preferences (DB)
- [ ] Sélection du modèle persiste pour chaque provider
- [ ] Ollama local sans clé API requise
- [ ] OpenRouter accepte modèles avec "/" (ex: "anthropic/claude-sonnet-4-6")
- [ ] Interface montre le statut de configuration (clé présente ou manquante)

**Composants :**
- `src/backend/app/services/llm.py` : `_default_config()`, `LLMService.config`
- `src/backend/app/services/providers/base.py` : `LLMProvider` enum (10 providers)
- `src/frontend/src/components/settings/LLMTab.tsx` : `PROVIDERS` config array

**Tests :**
- `tests/test_services_llm.py` : sélection provider, modèle par défaut

---

### US-901 : Configurer clés API pour 9 providers cloud

**En tant que** solopreneur/TPE
**Je veux** ajouter/mettre à jour les clés API pour les 9 providers (Anthropic, OpenAI, Gemini, Mistral, Grok, OpenRouter, Perplexity, DeepSeek, Infomaniak)
**Afin de** sécuriser mes credentials et les utiliser immédiatement

**Critères d'acceptation :**
- [ ] Clés API chiffrées en DB (Fernet) + optionnel env vars
- [ ] UI masque/révèle la clé (Eye icon)
- [ ] Validation du préfixe clé (ex: "sk-ant-" pour Anthropic)
- [ ] Message d'erreur si clé manquante pour provider sélectionné
- [ ] Cache API keys en mémoire (reload_api_key_cache) pour perf

**Composants :**
- `src/backend/app/services/llm.py` : `_get_api_key_from_db()`, `load_api_key_cache`
- `src/backend/app/services/encryption.py` : Fernet chiffrement
- `src/frontend/src/components/settings/LLMTab.tsx` : form API key, sauvegarde
- `src/backend/app/routers/config.py` : endpoint `POST /config/api-key`

**Tests :**
- `tests/test_services_llm.py` : chiffrement/déchiffrement clés

---

### US-902 : Circuit breaker - bascule automatique provider si erreur

**En tant que** solopreneur/TPE
**Je veux** que THÉRÈSE bascule automatiquement sur un provider fallback si le provider principal est indisponible
**Afin de** maintenir la continuité de service sans intervention manuelle

**Critères d'acceptation :**
- [ ] Circuit breaker détecte `HTTPStatusError` ou timeout provider
- [ ] Fallback priorité : providers avec clé API valide → Ollama local
- [ ] Log de la bascule (provider changement détecté)
- [ ] Tentative forcée provider initial si aucun fallback dispo
- [ ] Restoration config initiale après requête fallback

**Composants :**
- `src/backend/app/services/circuit_breaker.py` : état providers
- `src/backend/app/services/llm.py` : `_resolve_with_circuit_breaker()`, `_get_fallback_configs()`
- `src/backend/app/services/llm.py` : `stream_response_with_tools()` (US-006)

**Tests :**
- `tests/test_services_llm.py` : fallback chain, récupération provider principal

---

### US-903 : Provider Anthropic avec support outils (tool calling)

**En tant que** solopreneur/TPE
**Je veux** utiliser Claude (Anthropic) avec support des outils MCP et skills
**Afin de** bénéficier des meilleures capacités de raisonnement et d'intégration

**Critères d'acceptation :**
- [ ] Modèles Claude supportés : Opus 4.6, Sonnet 4.6, Haiku 4.5
- [ ] Conversion outils OpenAI → format Anthropic (input_schema)
- [ ] Stream tool calls avec id, name, arguments JSON
- [ ] Continue conversation après tool result (tool_use + tool_result blocks)
- [ ] Context window 200k tokens

**Composants :**
- `src/backend/app/services/providers/anthropic.py` : `AnthropicProvider`, `_convert_tools()`
- `src/backend/app/services/providers/anthropic.py` : `stream()`, `continue_with_tool_results()`

**Tests :**
- `tests/test_services_llm.py` : streaming tool calls Anthropic

---

### US-904 : Provider OpenAI avec modèles GPT-5 et o3/o4

**En tant que** solopreneur/TPE
**Je veux** utiliser GPT-5, o3, o4 (reasoning models) via OpenAI
**Afin de** bénéficier du raisonnement avancé pour problèmes complexes

**Critères d'acceptation :**
- [ ] Détection dynamique `max_completion_tokens` pour GPT-5.x, o1, o3, o4
- [ ] Tool calling via `tool_choice: "auto"`
- [ ] Handling finish_reason : stop, tool_calls, length, content_filter
- [ ] Context window 200k tokens
- [ ] Messages système en format OpenAI

**Composants :**
- `src/backend/app/services/providers/openai.py` : `_uses_max_completion_tokens()`, `_build_request_body()`
- `src/backend/app/services/providers/openai.py` : `stream()`, `continue_with_tool_results()`

**Tests :**
- `tests/test_services_llm.py` : max_completion_tokens GPT-5, tool calls OpenAI

---

### US-905 : Provider Gemini avec grounding Google Search

**En tant que** solopreneur/TPE
**Je veux** utiliser Gemini avec grounding web automatique (Google Search)
**Afin de** obtenir des réponses enrichies avec sources web sans configuration Brave

**Critères d'acceptation :**
- [ ] Modèles Gemini 3.1/3/2.5 avec grounding
- [ ] Enable/disable grounding via `enable_grounding` param
- [ ] Conversion messages → Gemini format (contents/parts)
- [ ] Logging métadonnées grounding (webSearchQueries)
- [ ] Context window 1M tokens
- [ ] Filtrage messages vides (Gemini rejette parts vides)

**Composants :**
- `src/backend/app/services/providers/gemini.py` : `stream()` avec `enable_grounding`
- `src/backend/app/services/llm.py` : passage `enable_grounding=False` pour skills/génération

**Tests :**
- `tests/test_services_llm.py` : grounding Google Search Gemini

---

### US-906 : Provider OpenRouter avec 200+ modèles (routing proxy)

**En tant que** solopreneur/TPE
**Je veux** accéder à 200+ modèles LLM (Claude, GPT, Gemini, Llama, etc.) via OpenRouter
**Afin de** tester/basculer entre modèles sans gérer 10 clés API différentes

**Critères d'acceptation :**
- [ ] Format modèle avec "/" autorisé (ex: "anthropic/claude-sonnet-4-6", "meta-llama/llama-4")
- [ ] Messages système en format OpenAI (OpenRouter-compatible)
- [ ] Handling erreurs spécifiques : 401 (clé), 402 (crédit), 403 (permission), 429 (rate limit)
- [ ] Free models notation `:free` supportée
- [ ] Detection finish_reason=length (raisonnement model timeout)
- [ ] Detection finish_reason=content_filter (modèle filtré réponse)

**Composants :**
- `src/backend/app/services/providers/openrouter.py` : `stream()`, gestion erreurs
- `src/frontend/src/components/settings/LLMTab.tsx` : modèles OpenRouter liste

**Tests :**
- `tests/test_services_llm.py` : erreurs OpenRouter (401, 402, 403)

---

### US-907 : Provider Ollama local - IA 100% offline sans clé API

**En tant que** solopreneur/TPE
**Je veux** utiliser Ollama en local pour l'IA sans clé API, sans envoyer données au cloud
**Afin de** préserver la confidentialité et réduire latence

**Critères d'acceptation :**
- [ ] Auto-détection Ollama running sur localhost:11434
- [ ] Message d'erreur lisible si Ollama non démarré (ConnectError)
- [ ] Message si modèle manquant → indique cmd "ollama pull"
- [ ] Timeout connexion 5s, pas de timeout lecture (machines lentes)
- [ ] BUG-048 : options num_predict + num_ctx pour skills Office
- [ ] BUG-052 : cap num_ctx à 8192 pour machines <8 Go RAM
- [ ] Context window 32k tokens (configurable par modèle)

**Composants :**
- `src/backend/app/services/providers/ollama.py` : `stream()`, gestion erreurs lisibles
- `src/backend/app/services/llm.py` : `_default_config()` fallback Ollama si aucune clé
- `src/frontend/src/components/settings/LLMTab.tsx` : sélection modèles Ollama local

**Tests :**
- `tests/test_services_llm.py` : ConnectError, modèle 404, OOM 500

---

### US-908 : Provider Mistral souverain français + tools support

**En tant que** solopreneur/TPE
**Je veux** utiliser Mistral AI (provider IA français souverain)
**Afin de** bénéficier d'une solution française avec tool calling

**Critères d'acceptation :**
- [ ] Modèles : Mistral Large 3, Codestral, Devstral, Mistral Small
- [ ] Tool calling détection `tool_calls` dans delta
- [ ] Gestion arguments JSON partiellement streamés (chunk invalide → fallback {})
- [ ] Context window 256k tokens
- [ ] Erreur API 401/429 gérée

**Composants :**
- `src/backend/app/services/providers/mistral.py` : `stream()` avec tool_calls parsing

---

### US-909 : Provider Grok (xAI) - intégration basique

**En tant que** solopreneur/TPE
**Je veux** utiliser Grok 4 et 3 de xAI
**Afin de** tester un provider alternatif puissant

**Critères d'acceptation :**
- [ ] Modèles Grok 4, Grok 4.1 Fast, Grok 3
- [ ] Format OpenAI-compatible
- [ ] Context window 131k tokens
- [ ] Pas de tool calling (implémentation basique)

**Composants :**
- `src/backend/app/services/providers/grok.py` : `stream()` simple

---

### US-910 : Récupération audio + transcription Whisper Groq

**En tant que** solopreneur/TPE
**Je veux** enregistrer ma voix via micro et la transcrire en texte
**Afin de** composer mes messages chat sans taper au clavier

**Critères d'acceptation :**
- [ ] Enregistrement audio via Tauri plugin mic-recorder (desktop) ou Web API (fallback)
- [ ] Transcription via Groq Whisper API (whisper-large-v3-turbo, langue FR)
- [ ] Format output : TranscriptionResponse (text, duration_seconds, language)
- [ ] Gestion erreurs : 401 (clé), 429 (limite), timeout, réseau
- [ ] Texte inséré dans chat après transcription

**Composants :**
- `src/frontend/src/hooks/useVoiceRecorder.ts` : `startRecording()`, `stopRecording()`, `toggleRecording()`
- `src/backend/app/routers/voice.py` : `POST /transcribe`, appel Groq API
- `src/frontend/src/components/chat/` : button micro + transcription inline

**Tests :**
- `tests/test_routers_voice.py` : appel Groq, 401/429 errors

---

### US-911 : Configuration clé API Groq pour transcription

**En tant que** solopreneur/TPE
**Je veux** configurer ma clé API Groq pour la transcription vocale
**Afin de** activer la saisie audio

**Critères d'acceptation :**
- [ ] Clé API chiffrée en DB ou lue depuis env GROQ_API_KEY
- [ ] UI masque/révèle clé (Eye icon)
- [ ] Validation connectivité Groq
- [ ] Message erreur si clé manquante

**Composants :**
- `src/backend/app/routers/voice.py` : `_get_groq_api_key()`, chiffrement
- `src/frontend/src/components/settings/ServicesTab.tsx` : form Groq key

---

### US-912 : Recherche web Brave Search intégrée

**En tant que** solopreneur/TPE
**Je veux** faire des recherches web et injecter les résultats dans la réponse LLM
**Afin de** que THÉRÈSE soit à jour sur l'actualité et les données web

**Critères d'acceptation :**
- [ ] Configuration clé API Brave Search (2k requêtes/mois gratuit)
- [ ] Service `BraveSearchService` : requête, parsing résultats
- [ ] Fallback DuckDuckGo si clé manquante
- [ ] Format résultat : SearchResult (title, url, snippet, source)
- [ ] Région par défaut FR, language FR

**Composants :**
- `src/backend/app/services/web_search.py` : `BraveSearchService.search()`
- `src/backend/app/routers/chat.py` : intégration résultats web en système prompt
- `src/frontend/src/components/settings/ServicesTab.tsx` : form Brave key

**Tests :**
- `tests/test_services_web_search.py` : requête Brave, fallback DuckDuckGo

---

### US-913 : MCP - 19 presets de serveurs pour intégrations

**En tant que** solopreneur/TPE
**Je veux** installer/configurer 19 serveurs MCP préconfigurés par catégorie
**Afin de** connecter THÉRÈSE à mes outils existants (Notion, Airtable, Gmail, Stripe, etc.)

**Catégories de 19 presets :**

**Essentiels (3 sans API key) :**
1. **Filesystem** - Lecture/écriture fichiers locaux (`@modelcontextprotocol/server-filesystem`)
2. **Fetch** - Récupération contenu URLs (`@modelcontextprotocol/server-fetch`)
3. **Time** - Conversions timezone, horloge mondiale (`@modelcontextprotocol/server-time`)

**Productivité (5) :**
4. **Google Workspace** - Gmail, Drive, Calendar, Docs, Sheets
5. **Notion** - Bases données, pages, knowledge management
6. **Airtable** - Bases données, CRM, gestion projets
7. **Todoist** - Gestion tâches, projets, deadlines
8. **Trello** - Tableaux Kanban, cartes, listes

**Recherche (2) :**
9. **Brave Search** - Recherche web avancée
10. **Perplexity** - Recherche web IA-augmentée

**Marketing (1) :**
11. **Brevo** - Email marketing, campagnes, contacts

**CRM & Ventes (2) :**
12. **HubSpot CRM** - Contacts, deals, tâches, pipeline
13. **Pipedrive** - CRM ventes, deals, activités

**Finance (1) :**
14. **Stripe** - Paiements, clients, factures, liens

**Communication (1) :**
15. **WhatsApp Business** - Messages, templates, contacts

**Avancé (3) :**
16. **Sequential Thinking** - Raisonnement structuré étape par étape
17. **Slack** - Envoyer messages, lire channels
18. **Playwright** - Automatisation navigateur (formulaires, extraction)

**Critères d'acceptation :**
- [ ] Endpoint `GET /mcp/presets` : liste des 19 avec statut installed
- [ ] Endpoint `POST /mcp/presets/{preset_id}/install` : installation avec env vars
- [ ] Remplacement placeholders `{HOME}`, `{WORKING_DIRECTORY}` dans args
- [ ] Chiffrement env vars sensibles (API keys)
- [ ] Whitelist commandes MCP : npx, node, python, uvx, deno, bun, docker
- [ ] Blacklist commandes dangereuses : rm, bash, sh, curl, chmod, sudo, ssh
- [ ] SEC-001 : validation arguments sans opérateurs shell (;, |, &&, etc.)

**Composants :**
- `src/backend/app/routers/mcp.py` : `PRESET_SERVERS` array (19 presets), `list_presets()`, `install_preset()`
- `src/backend/app/services/mcp_service.py` : validation, démarrage serveurs
- `src/frontend/src/components/settings/ServicesTab.tsx` : liste presets, install UI

**Tests :**
- `tests/test_routers_mcp.py` : list presets, install avec env vars
- `tests/test_mcp_windows_command_resolution.py` : résolution commandes

---

### US-914 : MCP - Démarrage/arrêt/configuration serveurs

**En tant que** solopreneur/TPE
**Je veux** démarrer, arrêter, configurer les serveurs MCP individuellement
**Afin de** gérer les connexions et consommer les ressources selon mes besoins

**Critères d'acceptation :**
- [ ] Endpoint `POST /mcp/servers/{server_id}/start` : lancement serveur + transport stdio
- [ ] Endpoint `POST /mcp/servers/{server_id}/stop` : arrêt graceful (terminate 5s timeout)
- [ ] Endpoint `PUT /mcp/servers/{server_id}` : mise à jour config (nom, command, args, env)
- [ ] Endpoint `DELETE /mcp/servers/{server_id}` : suppression
- [ ] Endpoint `GET /mcp/servers` : liste avec statut (stopped, starting, running, error)
- [ ] Redémarrage automatique si config change
- [ ] Logging stderr du serveur sans bloquer stdout
- [ ] Cleanup requêtes pending après 60s timeout

**Composants :**
- `src/backend/app/services/mcp_service.py` : `start_server()`, `stop_server()`, `MCPServerStatus` enum
- `src/backend/app/services/mcp_service.py` : `_read_server_stderr()`, `_cleanup_pending_requests()` (Sprint 2 - PERF-2.8, PERF-2.14)
- `src/backend/app/routers/mcp.py` : endpoints CRUD serveurs
- `src/backend/app/models/entities.py` : persistence config (`~/.therese/mcp_servers.json`)

**Tests :**
- `tests/test_routers_mcp.py` : start/stop/update/delete

---

### US-915 : MCP - Exécution des outils (tool calling)

**En tant que** solopreneur/TPE
**Je veux** que l'LLM puisse appeler les outils MCP pour exécuter des actions
**Afin de** créer des tâches, envoyer emails, chercher des infos, etc.

**Critères d'acceptation :**
- [ ] Endpoint `GET /mcp/tools` : récupère tous les tools de tous les serveurs running
- [ ] Format outils LLM : OpenAI/Anthropic-compatible (type=function)
- [ ] Naming convention : `{server_id}__{tool_name}`
- [ ] Endpoint `POST /mcp/tools/call` : exécution outil avec arguments
- [ ] ToolCallResult : success, result, error, execution_time_ms
- [ ] Timeout outil 120s, signalement erreur LLM
- [ ] Chat flow : LLM stream → tool_call → exécution → continue_with_tool_results

**Composants :**
- `src/backend/app/services/mcp_service.py` : `get_tools_for_llm()`, `call_tool()`, `execute_tool_call()`
- `src/backend/app/services/mcp_service.py` : `_list_tools()` (discovery)
- `src/backend/app/routers/mcp.py` : endpoints tools listing et execution
- `src/backend/app/routers/chat.py` : intégration tool_call → exécution → continue

**Tests :**
- `tests/test_routers_mcp.py` : tool discovery, execution
- `tests/e2e/test_mcp.py` : chat avec tool calls end-to-end

---

### US-916 : MCP - Initialisation protocol + JSON-RPC

**En tant que** solopreneur/TPE (développeur)
**Je veux** que les serveurs MCP s'initialisent correctement avec le protocol 2024-11-05
**Afin que** THÉRÈSE communique correctement en JSON-RPC 2.0

**Critères d'acceptation :**
- [ ] `_initialize_server()` : envoi initialize request (protocolVersion, capabilities, clientInfo)
- [ ] Timeout init 90s (npx télécharge package au premier lancement)
- [ ] Envoi notification `initialized` après réponse
- [ ] JSON-RPC 2.0 format : jsonrpc, id, method, params
- [ ] Gestion responses via `_handle_server_message()`
- [ ] Pending requests avec futures + timeout

**Composants :**
- `src/backend/app/services/mcp_service.py` : `_initialize_server()`, `_send_request()`, `_send_notification()`

**Tests :**
- `tests/test_services_mcp.py` : init protocol

---

### US-917 : MCP - Environnement sécurisé + PATH enrichi

**En tant que** solopreneur (DevSecOps)
**Je veux** que les subprocessus MCP ne reçoivent que les env vars minimales
**Afin de** éviter les fuites de clés API

**Critères d'acceptation :**
- [ ] Env vars minimales : PATH, HOME, USER, LANG, TERM, NODE_PATH, TMPDIR
- [ ] Env vars sensibles déchiffrées du storage (Fernet)
- [ ] BUG-062 : PATH enrichi avec /usr/local/bin, /opt/homebrew/bin, nvm/fnm/volta
- [ ] BUG-078 : chemins Windows APPDATA, LOCALAPPDATA, PROGRAMFILES
- [ ] Pas de copie complète os.environ
- [ ] Résolution symlinks via shutil.which()

**Composants :**
- `src/backend/app/services/mcp_service.py` : `start_server()` env construction

**Tests :**
- `tests/test_services_mcp.py` : env vars filtrage

---

### US-918 : MCP - Sécurité : whitelist commandes + validation arguments

**En tant que** solopreneur (DevSecOps)
**Je veux** que seules les commandes MCP autorisées puissent s'exécuter
**Afin d'** empêcher injection de commandes malveillantes

**Critères d'acceptation :**
- [ ] Whitelist : npx, node, python, python3, uvx, uv, docker, deno, bun
- [ ] Blacklist : rm, bash, sh, curl, wget, nc, telnet, ssh, chmod, sudo, kill
- [ ] SEC-001 : validation args : interdiction opérateurs shell (;, |, &&, ||, `, $, >, <)
- [ ] Normalisation nom commande (Windows .exe, .cmd, .bat)
- [ ] Validation `validate_mcp_command()` appelée avant start_server

**Composants :**
- `src/backend/app/services/mcp_service.py` : `validate_mcp_command()`, `_normalize_command_name()`
- `src/backend/app/routers/mcp.py` : validation lors du create/install preset

**Tests :**
- `tests/test_services_mcp.py` : validation whitelist/blacklist

---

### US-919 : Stockage persistant config LLM, modèles, clés API

**En tant que** solopreneur/TPE
**Je veux** que ma configuration LLM (provider, modèle, clés) soit sauvegardée
**Afin de** ne pas la reconfigurer à chaque démarrage

**Critères d'acceptation :**
- [ ] BD : `preferences` table (key, value)
- [ ] Clés persistées : `llm_provider`, `llm_model`, `{provider}_api_key`
- [ ] Clés API chiffrées Fernet
- [ ] API endpoint pour sauvegarder : `POST /config/save`
- [ ] Invalidation cache après mise à jour : `invalidate_api_key_cache()`
- [ ] LLMService global singleton réinitialisé après changement config

**Composants :**
- `src/backend/app/models/entities.py` : `Preference` entity
- `src/backend/app/routers/config.py` : endpoints save/load config
- `src/backend/app/services/llm.py` : cache api keys, `load_api_key_cache()`, `invalidate_llm_service()`

**Tests :**
- `tests/test_services_llm.py` : persistance config

---

### US-920 : THERESE.md - Mémoire persistante injectée en system prompt

**En tant que** solopreneur/TPE
**Je veux** que THÉRÈSE lise mon fichier THERESE.md et l'injecte dans le system prompt
**Afin que** l'IA connaisse mes contacts, projets, instructions personnalisées

**Critères d'acceptation :**
- [ ] Chemin THERESE.md : `~/.therese/THERESE.md` ou `~/THERESE.md`
- [ ] Contenu tronqué à 10k chars si > 10k
- [ ] Injection en system prompt avec section "## Instructions THERESE.md:"
- [ ] Lazy loading + caching (reload_therese_md())
- [ ] BUG-053 : injection date réelle pour éviter [Date actuelle] non substituée

**Composants :**
- `src/backend/app/services/llm.py` : `load_therese_md()`, `_get_system_prompt_with_identity()`

---

### US-921 : Circuit breaker - État providers + métriques résilience

**En tant que** solopreneur (DevOps)
**Je veux** que THÉRÈSE track l'état des providers et bascule sur fallback automatiquement
**Afin de** maintenir la résilience du service

**Critères d'acceptation :**
- [ ] Service `CircuitBreaker` : record_success(), record_failure(), is_available()
- [ ] État provider : disponible, circuit ouvert (en panne)
- [ ] Logging bascule : "Circuit breaker: bascule anthropic → openai"
- [ ] Compteurs : succès, échecs, erreurs par provider

**Composants :**
- `src/backend/app/services/circuit_breaker.py` : implémentation

**Tests :**
- `tests/test_services_llm.py` : circuit breaker behavior

---

### US-922 : Post-processing F-11 - Conversion tableaux Markdown → listes

**En tant que** utilisateur final
**Je veux** que les tableaux Markdown complexes soient convertis en listes lisibles
**Afin d'** avoir un formatage cohérent avec les directives THÉRÈSE

**Critères d'acceptation :**
- [ ] Détection lignes tableau (commence par |)
- [ ] Extraction en-têtes (si ligne séparatrice ---)
- [ ] Conversion format : "- Clé : Valeur | Clé2 : Valeur2"
- [ ] Si 1 colonne : "- Valeur"
- [ ] Reste du texte inchangé

**Composants :**
- `src/backend/app/services/llm.py` : `convert_markdown_tables_to_bullets()`, `_table_block_to_bullets()`

---

### US-923 : Système d'identity utilisateur + profile injection

**En tant que** solopreneur/TPE
**Je veux** que THÉRÈSE personnalise ses réponses selon mon profil (nom, entreprise, métier)
**Afin qu'** elle communique de manière personnalisée et pertinente

**Critères d'acceptation :**
- [ ] Profile utilisateur : name, company, role, etc.
- [ ] Format profile : injected en section "## Utilisateur" du system prompt
- [ ] Fallback : system prompt sans profil si profile vide
- [ ] Profile chargé de `UserProfile` service (DB ou cache)

**Composants :**
- `src/backend/app/services/user_profile.py` : `get_cached_profile()`, `UserProfile.format_for_llm()`
- `src/backend/app/services/llm.py` : `_get_system_prompt_with_identity()`

**Tests :**
- `tests/test_services_llm.py` : injection profile

---

Cette reconstruction couvre les **10 providers LLM**, **circuit breaker avec fallback**, **transcription vocale**, **19 presets MCP** avec sécurité, et **recherche web Brave Search**, pour un total de **24 user stories** numérotées US-900 à US-923.