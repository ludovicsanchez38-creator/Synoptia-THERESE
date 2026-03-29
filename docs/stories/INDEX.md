# User Stories Index - THÉRÈSE v2

> Reconstituées le 29 mars 2026 par 12 agents scribes parcourant le code source.
> 305 user stories couvrant l'intégralité du codebase.

## Domaines

| Fichier | Domaine | Stories | Count |
|---------|---------|---------|-------|
| [US-001-chat-onboarding.md](US-001-chat-onboarding.md) | Chat + Onboarding | US-001 → US-041 | 41 |
| [US-100-email.md](US-100-email.md) | Email (composeur, wizard, classification, réponse IA) | US-100 → US-130 | 31 |
| [US-200-calendar-tasks.md](US-200-calendar-tasks.md) | Calendrier + Tâches | US-200 → US-225 | 26 |
| [US-300-crm-invoices.md](US-300-crm-invoices.md) | CRM + Factures + Email-CRM linking | US-300 → US-314 | 15 |
| [US-400-board-skills.md](US-400-board-skills.md) | Board IA (5 conseillers) + Skills Office | US-400 → US-415 | 16 |
| [US-500-memory-rgpd.md](US-500-memory-rgpd.md) | Mémoire + RGPD | US-500 → US-533 | 34 |
| [US-600-settings-mcp.md](US-600-settings-mcp.md) | Settings + MCP (19 presets) + Images + Notifications | US-600 → US-629 | 30 |
| [US-700-navigation-ux.md](US-700-navigation-ux.md) | Navigation + Sidebar + UX transverse + Accessibilité | US-700 → US-721 | 22 |
| [US-800-security.md](US-800-security.md) | Sécurité (Fernet, anti-injection, rate limit, CORS) | US-800 → US-809 | 10 |
| [US-900-providers-integrations.md](US-900-providers-integrations.md) | 10 Providers LLM + Voix + MCP + Brave Search | US-900 → US-923 | 24 |
| [US-1000-desktop.md](US-1000-desktop.md) | Tauri desktop + Updater + Backup + Infrastructure | US-1000 → US-1022 | 23 |
| [US-1100-orphelins.md](US-1100-orphelins.md) | Stories orphelines (Avocat du diable) | US-1100 → US-1132 | 33 |
| **TOTAL** | | | **305** |

## Méthode de reconstruction

12 agents "scribes" ont parcouru le code source en parallèle :
- 8 scribes par domaine fonctionnel
- 3 scribes supplémentaires (sécurité, providers, desktop)
- 1 avocat du diable (recherche inverse : routers, composants, data-testid orphelins)

Chaque story suit le format :
```
### US-XXX : Titre
**En tant que** [persona]
**Je veux** [action]
**Afin de** [bénéfice]

**Critères d'acceptation :** [checklist testable]
**Composants :** [fichiers code]
**data-testid :** [sélecteurs pour tests browser]
```

## Couverture

- **30 routers backend** couverts (11 orphelins identifiés par l'avocat du diable)
- **120+ composants frontend** analysés
- **20 stores Zustand** documentés
- **22 hooks custom** référencés
- **100+ services backend** cartographiés

## Priorités issues du Jury (29 mars 2026)

| Prio | Feature | Stories liées |
|------|---------|---------------|
| P0 | CC/BCC composeur email | US-104 |
| P0 | Z-index standardisé | US-707, US-629 |
| P1 | Signature HTML | US-110 |
| P1 | useGuardedAction (pas d'erreur silencieuse) | US-708 |
| P2 | Email ↔ CRM linking | US-125, US-313 |
| P2 | Suivi métier (FollowUp) | US-314 |
| P3 | Réponse automatique email | Différée |
| Refusé | Confirmation de lecture | - |
