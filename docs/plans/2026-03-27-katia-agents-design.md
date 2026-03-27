# Design : Katia & Agents dans l'Atelier - v0.9.0

## Decisions validees

- **Runtime** : OpenClaw externe (port 18789, DreamQuest/VPS)
- **Acces data** : Katia appelle l'API THERESE via MCP Bridge
- **Scope MVP** : Actions concretes des le Sprint 2 (emails, factures, CRM)
- **UX** : Bouton dedie dans l'Atelier + layout split (sessions | chat)
- **Architecture** : MCP Bridge (serveur MCP expose les tools THERESE a OpenClaw)

## Architecture

THERESE Desktop                          OpenClaw (DreamQuest/VPS)
Frontend React                           Gateway :18789
  AtelierPanel  <-- SSE/poll -->           Agent "katia"
    SessionList                              MCP tools
    AgentChat                                  therese-mcp
    NewTaskDialog                                |
Backend FastAPI  <----- HTTP (MCP) --------------+
  routers/agents.py
    POST /agents/dispatch
    GET /agents/sessions
    GET /agents/sessions/{id}/messages
    POST /agents/sessions/{id}/send
  services/
    openclaw_bridge.py     <- NOUVEAU
    mcp_therese_server.py  <- NOUVEAU
SQLite + Qdrant

## Fichiers a creer/modifier

| Fichier | Action | Role |
|---------|--------|------|
| services/openclaw_bridge.py | CREER | Client HTTP vers OpenClaw API |
| services/mcp_therese_server.py | CREER | Serveur MCP (14 tools) |
| routers/agents.py | MODIFIER | Endpoints dispatch/sessions/messages |
| models/entities_agents.py | MODIFIER | Modele AgentSession |
| components/atelier/AtelierPanel.tsx | MODIFIER | Layout split |
| components/atelier/SessionList.tsx | CREER | Liste sessions actives |
| components/atelier/AgentChat.tsx | CREER | Chat avec agent |
| components/atelier/NewTaskDialog.tsx | CREER | Dialog lancement tache |
| stores/atelierStore.ts | MODIFIER | State sessions |
| services/api/agents.ts | MODIFIER | Endpoints frontend |

## Modele de donnees

AgentSession (SQLModel table):
  id: str (UUID)
  agent_name: str ("katia")
  instruction: str (texte libre)
  status: str (running | done | error | cancelled)
  openclaw_session_id: str (ID cote OpenClaw)
  created_at: datetime
  finished_at: datetime | None
  result_summary: str | None
  actions_count: int = 0

## MCP Tools (14 tools MVP)

### CRM (3)
- list_contacts : GET /crm/contacts
- get_contact : GET /crm/contacts/{id}
- create_activity : POST /crm/activities

### Email (3)
- list_emails : GET /email/messages
- draft_email : POST /email/draft
- send_email : POST /email/send

### Facturation (2)
- list_invoices : GET /invoices
- create_invoice : POST /invoices

### Taches (2)
- list_tasks : GET /tasks
- create_task : POST /tasks

### Calendrier (2)
- list_events : GET /calendar/events
- create_event : POST /calendar/events

### Memoire (2)
- search_memory : POST /memory/search
- get_project : GET /memory/projects/{id}

## Interface

Layout split dans l'Atelier :
- Gauche : SessionList (pastille verte=running, check=done, rouge=error)
- Droite : AgentChat (messages Katia a gauche, utilisateur a droite)
- Header : bouton [+ Tache] ouvre NewTaskDialog
- Raccourci : Cmd+Shift+K = Atelier + focus nouvelle tache

## Flux

1. Solo clique [+ Tache], tape "relance les prospects sans reponse 15j"
2. Backend POST /agents/dispatch -> openclaw_bridge.spawn_session()
3. OpenClaw cree session Katia, retourne session_id
4. Backend stocke dans SQLite (AgentSession)
5. Frontend poll GET /agents/sessions toutes les 5s
6. Katia travaille via MCP tools (lit CRM, prepare brouillons)
7. Solo clique sur la session -> chat en temps reel
8. Solo peut intervenir -> POST /sessions/{id}/send
9. Katia termine -> status=done, result_summary

## Cas d'erreur

- OpenClaw non accessible : bandeau + bouton grise
- Agent pas configure : message guide
- Crash mid-tache : status error + bouton Relancer
- Action dangereuse : confirmation dans le chat
- 3 agents max : message d'attente
- Token expire : re-generation automatique
- Reseau coupe : retry 3x + backoff + error
- THERESE fermee : sessions continuent, resync au relancement

## Sprints

Sprint 2 : US-001 (lancer) + US-004 (notifications)
Sprint 3 : US-002 (sessions visibles) + US-013 (auto-update)
Sprint 5 : US-003 (multi-agents paralleles)
