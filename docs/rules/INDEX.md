# Index des Règles par Métier - THÉRÈSE V2

> Chaque fichier contient les conventions, patterns et anti-patterns pour un domaine spécifique du projet.

## Règles disponibles

| Fichier | Domaine | Description |
|---------|---------|-------------|
| [RULES-BACKEND.md](./RULES-BACKEND.md) | Backend Python | FastAPI, SQLModel, providers, routage, services, patterns architecturaux |
| [RULES-FRONTEND.md](./RULES-FRONTEND.md) | Frontend React | Tauri, composants, stores Zustand, hooks, TailwindCSS, animations |
| [RULES-SECURITE.md](./RULES-SECURITE.md) | Sécurité | Chiffrement, authentification, CORS, sandbox, RGPD, OWASP LLM Top 10 |
| [RULES-LLM.md](./RULES-LLM.md) | LLM et Providers | Multi-providers, tool calling, streaming SSE, MCP, Board de décision |
| [RULES-TESTS.md](./RULES-TESTS.md) | Tests | pytest, Vitest, Playwright, fixtures, conventions, matrice de couverture |
| [RULES-DESIGN.md](./RULES-DESIGN.md) | Design et UX | Palette, typographie, composants, animations Framer Motion, accessibilité |
| [RULES-DONNEES.md](./RULES-DONNEES.md) | Données et Mémoire | SQLite, Qdrant, RAG hybride, RGPD, sauvegarde, CRM sync |
| [RULES-DEVOPS.md](./RULES-DEVOPS.md) | DevOps et Déploiement | Makefile, migrations, Git, Tauri build, monitoring, performance |

## Autres documents

| Fichier | Description |
|---------|-------------|
| [../README.md](../README.md) | Présentation complète du projet |
| [../API.md](../API.md) | Documentation API (tous les endpoints) |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Guide de contribution |
| [../architecture.md](../architecture.md) | Architecture technique détaillée |
| [../prd-therese.md](../prd-therese.md) | Product Requirements Document |
| [../USER_STORIES.md](../USER_STORIES.md) | 100 user stories |
| [../benchmark-cowork.md](../benchmark-cowork.md) | Analyse concurrentielle vs Cowork |
| [../benchmark-memoire.md](../benchmark-memoire.md) | État de l'art mémoire IA |
| [../benchmark-ux.md](../benchmark-ux.md) | Patterns UX et design system |

## Règles transversales

Ces règles s'appliquent à **tous** les fichiers du projet :

1. **Jamais de tirets longs** (–) - utiliser des tirets courts (-) ou parenthèses
2. **Toujours les accents** en français (é, è, ê, à, ù, ô, ç, î)
3. **Jamais de `rm`** - utiliser `mv fichier ~/.Trash/`
4. **Commits en français** - format `type: description`
5. **Tester avant de valider** - aucun fix n'est terminé sans vérification
6. **Proposer un plan** avant toute implémentation non triviale
7. **Lire les logs** avant de spéculer sur un bug
