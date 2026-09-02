# Protocoles de Tests Exhaustifs - THERESE

> Tests browser via Chrome MCP, organisés par persona et user stories.
> Conçu le 28 mars 2026, panel 4 experts (QA Senior, Avocat du diable, UX, Dev Frontend).

## Architecture

```
tests/protocols/
  app/                               # THERESE App (Desktop Tauri)
    personas/
      A1-sophie-freelance.md         # Graphiste freelance, non-tech (48 etapes, ~180 tests)
      A2-marc-consultant.md          # Consultant RH, Excel (42 etapes, ~160 tests)
      A3-lea-power-user.md           # Coach business, power user (55 etapes, ~220 tests)
    modules/                         # Tests par module (a venir)
    catastrophes/                    # Scenarios catastrophe App

  server/                            # THERESE Server (Web multi-tenant)
    personas/
      S1-agent-municipal.md          # Agent role=agent (35 etapes, ~130 tests)
      S2-chef-service.md             # Manager role=manager (38 etapes, ~140 tests)
      S3-dsi-admin.md                # DSI role=admin (42 etapes, ~170 tests)
    modules/                         # Tests par module (a venir)
    catastrophes/                    # Scenarios catastrophe Server

  shared/
    catastrophes.md                  # 10 scenarios catastrophe transversaux
    chrome-mcp-patterns.md           # Patterns anti-flaky Chrome MCP
    data-testid-inventory.md         # Inventaire data-testid (a venir)
```

## Personas

> **Deux durees, deux choses differentes.** « Duree fiche » est le temps
> d'execution A LA MAIN annonce par la fiche elle-meme ; « Duree Chrome MCP »
> est le temps d'une campagne pilotee par un agent, avec ses captures. Elles
> etaient jusqu'au 02/09/2026 melangees sous un seul en-tete, ce qui les
> faisait paraitre contradictoires d'un facteur 3 a 5. Seule S3 declare la
> seconde dans sa fiche ; les cinq autres valeurs de cette colonne ne viennent
> que d'ici et restent sans garde automatique.
>
> **« Complements »** compte les etapes suffixees (MT, CH, TP, RBAC, VIS, PER)
> qui suivent le parcours numerote : isolation multi-tenant, separation des
> privileges, persistance. Elles etaient absentes de ce tableau, donc invisibles
> a qui prepare une campagne. `tests/test_protocoles_readme_coherent.py` tient
> desormais les colonnes Etapes, Complements et Duree fiche sur les fiches.

| Persona | Produit | Etapes | Complements | Tests | Duree fiche | Duree Chrome MCP |
|---------|---------|--------|-------------|-------|-------------|------------------|
| A1 Sophie (freelance) | App | 48 | - | ~180 | 25-35 min | 2h30-3h |
| A2 Marc (consultant) | App | 42 | - | ~160 | 25-35 min | 2h-2h30 |
| A3 Lea (power user) | App | 55 | - | ~220 | 40-55 min | 3h-3h30 |
| S1 Agent Municipal | Server | 35 | 7 | ~130 | 25-35 min | 1h30-2h |
| S2 Chef de Service | Server | 38 | 8 | ~140 | 35-50 min | 1h30-2h |
| S3 DSI Admin | Server | 42 | - | ~170 | non renseignee | 2h-2h30 |
| **TOTAL** | | **260** | **15** | **~1000** | **~2h30-3h30 (hors S3)** | **13-16h** |

## Comment lancer

### App (THERESE Desktop)
```bash
# 1. Lancer backend + frontend
cd ~/Desktop/Dev\ Synoptia/Synoptia-THERESE
make dev-backend &
make dev-frontend &

# 2. Ouvrir Chrome avec extension Claude-in-Chrome

# 3. Lancer une persona
/test-therese  # pour la batterie rapide
# OU suivre le protocole persona manuellement
```

### Server (THERESE Server)
```bash
# 1. Tunnel SSH vers le VPS
ssh -f -N -L 8880:127.0.0.1:80 ubuntu@51.178.16.63

# 2. Ouvrir Chrome

# 3. Lancer une persona
/test-therese-server --url http://localhost:8880
```

## Priorites

- **P0** : bloquant release - si FAIL, on ne publie pas
- **P1** : important - a corriger avant la prochaine release
- **P2** : nice to have - backlog

## Ordre d'execution recommande

1. S1 Agent (Server) - le plus court, valide le socle auth
2. A1 Sophie (App) - valide l'onboarding et le parcours de base
3. S3 DSI Admin (Server) - valide admin + RBAC
4. A3 Lea (App) - power user, couvre les edge cases
5. Catastrophes - les 10 scenarios critiques
6. A2 Marc + S2 Chef de Service - couverture complete
