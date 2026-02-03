# Documentation API - THÉRÈSE V2

## Informations générales

- **Base URL** : `http://localhost:8000`
- **Authentification** : Header `X-Therese-Token: {token}`
- **Format** : JSON (`application/json`)
- **Streaming** : SSE (`text/event-stream`) pour le chat et le board
- **Rate Limiting** : 60 requêtes/minute par IP

## Endpoints publics (sans authentification)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Info application (nom, version, statut) |
| `GET` | `/health` | Health check simple |
| `GET` | `/health/services` | Statut détaillé des services |
| `POST` | `/api/auth/token` | Obtenir le token de session |

---

## Chat (`/api/chat`)

### POST `/api/chat/` - Envoyer un message

Envoie un message et reçoit une réponse en streaming SSE.

**Body** :

```json
{
  "conversation_id": "uuid (optionnel, créé si absent)",
  "message": "Texte du message",
  "files": ["chemin/fichier.txt"],
  "model": "claude-sonnet-4-20250514 (optionnel)"
}
```

**Réponse SSE** :

```
event: chunk
data: {"type": "token", "content": "Bonjour"}

event: chunk
data: {"type": "tool_result", "tool_name": "web_search", "content": "..."}

event: chunk
data: {"type": "entities_detected", "contacts": [...], "projects": [...]}

event: chunk
data: {"type": "status", "content": "done", "usage": {"input_tokens": 150, "output_tokens": 200, "cost_eur": 0.003}}
```

### GET `/api/chat/` - Lister les conversations

**Réponse** :

```json
[
  {
    "id": "...",
    "title": "...",
    "created_at": "...",
    "message_count": 5
  }
]
```

### GET `/api/chat/{conversation_id}` - Détail conversation

**Réponse** :

```json
{
  "id": "...",
  "title": "...",
  "messages": [...],
  "created_at": "..."
}
```

### POST `/api/chat/{conversation_id}/title` - Renommer

**Body** :

```json
{"title": "Nouveau titre"}
```

### DELETE `/api/chat/{conversation_id}` - Supprimer

### POST `/api/chat/{conversation_id}/cancel` - Annuler la génération

---

## Mémoire (`/api/memory`)

### Contacts

#### GET `/api/memory/contacts` - Lister les contacts

**Params** : `?scope=global&scope_id=xxx`

**Réponse** :

```json
[
  {
    "id": "...",
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "...",
    "company": "...",
    "tags": [...],
    "score": 85
  }
]
```

#### POST `/api/memory/contacts` - Créer un contact

**Body** :

```json
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean@example.fr",
  "company": "Acme Corp",
  "phone": "+33 6 12 34 56 78",
  "notes": "CEO, rencontré au salon",
  "tags": ["client", "premium"],
  "scope": "global"
}
```

**Réponse** : `201 Created` + contact complet

#### GET `/api/memory/contacts/{id}` - Détail contact

#### PATCH `/api/memory/contacts/{id}` - Modifier un contact

**Body** : Champs à modifier (partiel accepté)

#### DELETE `/api/memory/contacts/{id}` - Supprimer un contact

**Params** : `?cascade=true` (supprime aussi les entités scoped)

### Projets

#### GET `/api/memory/projects` - Lister

#### POST `/api/memory/projects` - Créer

```json
{
  "name": "Refonte site web",
  "description": "Refonte complète du site corporate",
  "contact_id": "uuid-du-contact",
  "status": "in_progress",
  "budget": 5000,
  "tags": ["web", "design"]
}
```

#### PATCH `/api/memory/projects/{id}` - Modifier

#### DELETE `/api/memory/projects/{id}` - Supprimer

### Recherche hybride

#### POST `/api/memory/search` - Recherche

```json
{
  "query": "consultant marketing digital",
  "limit": 5
}
```

**Réponse** :

```json
[
  {
    "entity_type": "contact",
    "entity_id": "...",
    "text": "...",
    "score": 0.87
  }
]
```

---

## Fichiers (`/api/files`)

### GET `/api/files/` - Lister les fichiers indexés

### POST `/api/files/index` - Indexer un fichier

```json
{"path": "/chemin/vers/fichier.txt"}
```

### GET `/api/files/search?q=mot-clé` - Rechercher dans les fichiers

### DELETE `/api/files/{id}` - Retirer de l'index

---

## Configuration (`/api/config`)

### GET `/api/config/` - Configuration complète

### POST `/api/config/api-key` - Définir une clé API

```json
{"provider": "anthropic", "api_key": "sk-ant-..."}
```

### Profil utilisateur

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/config/profile` | Récupérer le profil |
| `POST` | `/api/config/profile` | Définir le profil |
| `POST` | `/api/config/profile/import-claude-md` | Import automatique depuis CLAUDE.md |
| `DELETE` | `/api/config/profile` | Supprimer le profil |

**Body POST `/api/config/profile`** :

```json
{"name": "Ludo", "company": "Synoptïa", "role": "Consultant IA"}
```

### LLM

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/config/llm` | Configuration LLM actuelle |
| `POST` | `/api/config/llm` | Modifier la configuration LLM |

**Body POST `/api/config/llm`** :

```json
{"provider": "anthropic", "model": "claude-sonnet-4-20250514"}
```

### Autres

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET/POST` | `/api/config/working-directory` | Répertoire de travail |
| `GET/POST` | `/api/config/onboarding-complete` | Statut onboarding |
| `GET/POST` | `/api/config/web-search` | Configuration recherche web |
| `GET` | `/api/config/ollama/status` | Statut Ollama |

---

## Skills Office (`/api/skills`)

### GET `/api/skills/list` - Lister les skills disponibles

**Réponse** :

```json
[
  {
    "id": "docx_report",
    "name": "Rapport DOCX",
    "format": "docx",
    "description": "..."
  }
]
```

### POST `/api/skills/execute/{skill_id}` - Générer un document

```json
{"prompt": "Crée un rapport sur les tendances IA 2026 avec 3 sections"}
```

**Réponse** :

```json
{
  "file_id": "...",
  "filename": "rapport_ia_2026.docx",
  "download_url": "/api/skills/download/..."
}
```

### GET `/api/skills/download/{id}` - Télécharger le fichier généré

---

## Board de décision (`/api/board`)

### GET `/api/board/advisors` - Les 5 conseillers

### GET `/api/board/advisors/{role}` - Détail d'un conseiller

### POST `/api/board/deliberate` - Lancer une délibération (SSE)

```json
{
  "question": "Dois-je investir dans une formation IA pour mes clients ?",
  "context": "Budget 5000€, 3 mois"
}
```

### GET `/api/board/decisions` - Historique des décisions

### GET `/api/board/decisions/{id}` - Détail

### DELETE `/api/board/decisions/{id}` - Supprimer

---

## Images (`/api/images`)

### POST `/api/images/generate` - Générer une image

```json
{
  "prompt": "Logo minimaliste pour une startup IA",
  "provider": "openai",
  "size": "1024x1024"
}
```

### POST `/api/images/generate-with-reference` - Avec image de référence

### GET `/api/images/download/{id}` - Télécharger

### GET `/api/images/list` - Historique

### GET `/api/images/status` - Disponibilité des providers

---

## Saisie vocale (`/api/voice`)

### POST `/api/voice/transcribe` - Transcrire un audio

**Content-Type** : `multipart/form-data`

**Body** : Fichier audio (WebM/Opus)

**Réponse** :

```json
{"text": "Texte transcrit"}
```

---

## Calculateurs (`/api/calc`)

### POST `/api/calc/roi` - Retour sur investissement

```json
{"investment": 10000, "revenue": 25000, "period_months": 12}
```

### POST `/api/calc/ice` - Score ICE

```json
{"impact": 8, "confidence": 7, "ease": 6}
```

### POST `/api/calc/rice` - Score RICE

```json
{"reach": 1000, "impact": 3, "confidence": 80, "effort": 5}
```

### POST `/api/calc/npv` - Valeur Actuelle Nette

```json
{"initial_investment": 50000, "cash_flows": [15000, 20000, 25000], "discount_rate": 0.1}
```

### POST `/api/calc/break-even` - Seuil de rentabilité

```json
{"fixed_costs": 5000, "price_per_unit": 100, "variable_cost_per_unit": 40}
```

---

## MCP (`/api/mcp`)

### Serveurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/mcp/servers` | Lister |
| `POST` | `/api/mcp/servers` | Ajouter |
| `POST` | `/api/mcp/servers/{id}/start` | Démarrer |
| `POST` | `/api/mcp/servers/{id}/stop` | Arrêter |
| `POST` | `/api/mcp/servers/{id}/restart` | Redémarrer |
| `DELETE` | `/api/mcp/servers/{id}` | Supprimer |

### Outils

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/mcp/tools` | Lister les outils disponibles |
| `POST` | `/api/mcp/tools/call` | Exécuter un outil |

**Body POST `/api/mcp/tools/call`** :

```json
{
  "tool_name": "read_file",
  "server_id": "filesystem",
  "arguments": {"path": "/tmp/test.txt"}
}
```

### Presets

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/mcp/presets` | 19 presets disponibles |
| `POST` | `/api/mcp/presets/{id}/install` | Installer un preset |

---

## Email (`/api/email`)

### Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/email/auth/initiate` | Lancer OAuth Gmail |
| `POST` | `/api/email/auth/callback` | Callback OAuth |

### Comptes

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/email/accounts` | Lister les comptes |
| `POST` | `/api/email/imap/setup` | Configurer IMAP/SMTP |
| `POST` | `/api/email/imap/test` | Tester la connexion |

### Messages

#### GET `/api/email/accounts/{id}/messages` - Lire les messages

#### POST `/api/email/send` - Envoyer un email

```json
{
  "account_id": "...",
  "to": ["destinataire@example.fr"],
  "subject": "Objet du mail",
  "body": "Contenu en texte ou HTML",
  "is_html": false
}
```

---

## Calendrier (`/api/calendar`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/calendar/events?start=2026-02-01&end=2026-02-28` | Événements |
| `POST` | `/api/calendar/events` | Créer |
| `PATCH` | `/api/calendar/events/{id}` | Modifier |
| `DELETE` | `/api/calendar/events/{id}` | Supprimer |
| `GET` | `/api/calendar/sync` | Synchroniser |

**Body POST `/api/calendar/events`** :

```json
{
  "title": "Réunion client",
  "start": "2026-02-15T10:00:00",
  "end": "2026-02-15T11:00:00",
  "location": "Visio",
  "description": "Point mensuel"
}
```

---

## Tâches (`/api/tasks`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/tasks/` | Lister |
| `POST` | `/api/tasks/` | Créer |
| `PATCH` | `/api/tasks/{id}` | Modifier |
| `DELETE` | `/api/tasks/{id}` | Supprimer |
| `POST` | `/api/tasks/{id}/complete` | Terminer |

**Body POST `/api/tasks/`** :

```json
{"title": "...", "project_id": "...", "due_date": "2026-03-01"}
```

---

## Factures (`/api/invoices`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/invoices/` | Lister |
| `POST` | `/api/invoices/` | Créer |
| `GET` | `/api/invoices/{id}/pdf` | Télécharger le PDF |
| `POST` | `/api/invoices/{id}/send` | Envoyer par email |

---

## CRM (`/api/crm`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/crm/sync/config` | Configuration sync |
| `POST` | `/api/crm/sync/config` | Définir le spreadsheet ID |
| `POST` | `/api/crm/sync/connect` | Connexion OAuth Google |
| `GET` | `/api/crm/sync/callback` | Callback OAuth |
| `POST` | `/api/crm/sync` | Synchroniser depuis Google Sheets |
| `POST` | `/api/crm/sync/import` | Import direct |

---

## Données et RGPD (`/api/data`, `/api/rgpd`)

### Export/Import

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/data/export` | Exporter toutes les données |
| `POST` | `/api/data/import` | Importer une sauvegarde |
| `POST` | `/api/data/backup` | Créer une sauvegarde |

### RGPD

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/rgpd/export` | Export données personnelles |
| `POST` | `/api/rgpd/delete` | Droit à l'oubli |
| `GET` | `/api/rgpd/audit` | Journal d'audit |

---

## Codes d'erreur

| Code | Signification |
|------|---------------|
| `200` | OK |
| `201` | Créé |
| `204` | Pas de contenu |
| `400` | Requête invalide |
| `401` | Non authentifié |
| `403` | Accès refusé |
| `404` | Non trouvé |
| `422` | Erreur de validation |
| `429` | Trop de requêtes |
| `500` | Erreur serveur |

### Format d'erreur standard

```json
{
  "detail": "Description de l'erreur",
  "code": "ERROR_CODE",
  "recoverable": true
}
```
