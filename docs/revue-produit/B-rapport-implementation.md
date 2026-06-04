# Chantier B (Donnée unifiée) — Rapport d'implémentation

**Date** : 2026-06-04 · **Branche** : `chantier-revue-produit` · **Base** : `main` (v0.13.2)
**Méthode** : TDD strict (test d'abord, vu échouer, puis code), commits par lot, vérif après chaque lot.

## Commits (du plus ancien au plus récent)
| Lot | Commit | Sujet |
|-----|--------|-------|
| Docs | ab75044 | état des lieux + pistes + roadmap |
| Spec | 233940c | spec Chantier B |
| Plan | 054169d | plan 6 lots TDD |
| B1 | c256265 | `contactsStore` source de vérité unique (P4) |
| B2 | f32c3d7 | CRM lit contactsStore (vue filtrée par source) |
| B3 | f49ab8d | Mémoire sur contactsStore + recherche sémantique (P3 partiel + P5) |
| B5 | b8a4ac6 | création contact (chat + modale) via contactsStore |
| B4 | e2c99f6 | Mémoire en panneau in-window, fin de la fenêtre détachée (P3) |
| B6 | 04cc1c2 | contacts CRM indexés Qdrant à la création (BUG-102) |

## Couverture des pistes
- **P3 (une Mémoire)** : fenêtre Tauri détachée supprimée, Mémoire = panneau in-window unique adossé au store. Plus de désync entre fenêtres.
- **P4 (un Contact)** : `contactsStore` unique ; Mémoire (tous) et CRM (filtré par `source`) sont deux vues ; chat/modale/CRM créent via le store ; un contact créé apparaît des deux côtés.
- **P5 (recherche sémantique)** : barre Mémoire branchée sur `/api/memory/search` (Qdrant), débounce 250 ms, au lieu d'un filtre JS local.
- **Bonus B6** : un contact créé côté CRM est désormais indexé dans Qdrant (avant : invisible à la recherche sémantique).

## Vérifications automatiques (toutes vertes)
- **Frontend** : `tsc --noEmit` = 0 erreur · `vitest` = **129 tests** (dont nouveaux : 7 contactsStore + 1 EntitySuggestion) · `eslint` = au seuil (≤27 warnings, 0 erreur) · `npm run build` (tsc + vite) = OK.
- **Backend** : `pytest tests/test_regression.py` (dont +2 BUG-102) = vert · suite complète hors e2e = **exit 0** · `ruff` = clean.

## Vérification navigateur (smoke runtime — 1er regard)
- App lancée dans Chrome contre un backend isolé (port dédié, base jetable `/tmp`, **zéro donnée de Ludo touchée**).
- Résultat : le frontend (toutes les modifs Chantier B) **se charge, monte et s'exécute sans crash**, atteint l'onboarding/UI principale. Les seules erreurs console sont (a) backend injoignable quand on visait le sidecar de l'app installée (CORS), corrigé en passant sur le backend isolé, et (b) API Tauri absentes en navigateur (`useFileDrop`), sans rapport avec le Chantier B.
- Le **flux d'écriture human-like complet** (créer un contact → vérifier qu'il apparaît en Mémoire ET en CRM, recherche sémantique, panneau in-window) est confié à **Syn** pour un 2e regard dans l'environnement Tauri réel (cf. `B-test-script-syn.md`), et il est déjà couvert au niveau logique par les tests unitaires du store (B1) et d'EntitySuggestion (B5).

## Notes / vigilance
- `crm.py` POST `/contacts` conserve sa sync Google Sheets ; B6 y ajoute juste l'embed Qdrant (résilient si Qdrant absent).
- Le défaut de couverture de tests composant du repo (6%) fait que la garantie de non-régression visuelle repose sur le typecheck + le test navigateur (Syn).
- Hors-périmètre (phases suivantes) : refonte visuelle des surfaces (Phase 1), consolidation des deux namespaces backend, tunnel de vente CRM (Phase 2).
