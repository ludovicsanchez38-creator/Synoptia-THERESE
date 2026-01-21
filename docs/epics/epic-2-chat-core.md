# Epic 2 : Chat Core

> Interface de conversation intelligente avec Claude API

## Vision

Créer une expérience de chat fluide et réactive :
- Interface épurée inspirée de Linear/Warp
- Streaming des réponses en temps réel
- Support Markdown riche
- Historique de session persistant

## Stories incluses

| ID | Titre | Points | Priorité |
|----|-------|--------|----------|
| E2-01 | Créer l'interface chat (input + messages) | 5 | P0 |
| E2-02 | Intégrer l'API Claude (envoi/réception) | 5 | P0 |
| E2-03 | Implémenter le streaming des réponses | 5 | P0 |
| E2-04 | Gérer l'historique de conversation (session) | 3 | P0 |
| E2-05 | Ajouter le support Markdown dans les réponses | 3 | P1 |
| E2-06 | Implémenter copier/coller et actions sur messages | 2 | P1 |

**Total : 23 points**

## Critères de succès de l'Epic

- [ ] L'utilisateur peut envoyer un message et recevoir une réponse
- [ ] Les réponses s'affichent caractère par caractère (streaming)
- [ ] Le Markdown est rendu (titres, listes, code blocks)
- [ ] L'historique persiste pendant la session
- [ ] Copier un message fonctionne (⌘C ou bouton)
- [ ] L'UI reste réactive pendant le streaming

## Design de l'interface

```
┌─────────────────────────────────────────────────────────┐
│  THÉRÈSE                                    [_] [□] [X] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 👤 Ludo                              14:32      │   │
│  │ Résume-moi le benchmark Cowork                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🤖 THÉRÈSE                           14:32      │   │
│  │ Voici les points clés du benchmark :            │   │
│  │                                                 │   │
│  │ ## Forces de Cowork                             │   │
│  │ - Exécution de code Python                      │   │
│  │ - Accès au filesystem                           │   │
│  │ - Interface épurée                   [📋] [🔄]  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Message...                              [⏎ Envoyer] │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Spécifications techniques

### Input utilisateur
- Textarea auto-resize
- Envoi : Enter (ou Shift+Enter pour newline)
- Placeholder : "Message THÉRÈSE..."
- Disabled pendant streaming

### Messages
- Distinction visuelle user/assistant
- Timestamp discret
- Actions hover : copier, régénérer (assistant only)
- Avatar : initiale ou icône

### Streaming
- Affichage caractère par caractère
- Indicateur "THÉRÈSE réfléchit..."
- Annulation possible (bouton stop)

### Markdown
- Titres (h1-h4)
- Listes (ordonnées, non-ordonnées)
- Code inline et blocks (avec syntax highlighting)
- Liens cliquables
- Gras, italique

## Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Latence API Claude | UX dégradée | Streaming + timeout + retry |
| Erreurs API (rate limit) | Blocage | Gestion erreur gracieuse + message user |
| Rendu Markdown complexe | Bugs UI | Lib éprouvée (react-markdown) |

## Dépendances

- E1-05 (IPC Tauri ↔ Backend) obligatoire
- E1-02 (Backend FastAPI) obligatoire

## Définition of Done

- Chat fonctionnel end-to-end
- Streaming visible
- Markdown rendu correctement
- Tests E2E basiques
- 0 erreur console

---

*Epic owner : Agent Dev Frontend*
*Sprint cible : Sprint 1-2*
