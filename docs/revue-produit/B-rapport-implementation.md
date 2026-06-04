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
| P5-fix | ee61fae | recherche contacts **hybride** (filtre local + sémantique) — 2e regard Syn |

## Couverture des pistes
- **P3 (une Mémoire)** : fenêtre Tauri détachée supprimée, Mémoire = panneau in-window unique adossé au store. Plus de désync entre fenêtres.
- **P4 (un Contact)** : `contactsStore` unique ; Mémoire (tous) et CRM (filtré par `source`) sont deux vues ; chat/modale/CRM créent via le store ; un contact créé apparaît des deux côtés.
- **P5 (recherche sémantique)** : barre Mémoire branchée sur `/api/memory/search` (Qdrant), débounce 250 ms. **Corrigée après le 2e regard de Syn** en recherche **hybride** (filtre local par nom + fusion sémantique) — voir section dédiée plus bas.
- **Bonus B6** : un contact créé côté CRM est désormais indexé dans Qdrant (avant : invisible à la recherche sémantique).

## Vérifications automatiques (toutes vertes)
- **Frontend** : `tsc --noEmit` = 0 erreur · `vitest` = **129 tests** (dont nouveaux : 7 contactsStore + 1 EntitySuggestion) · `eslint` = au seuil (≤27 warnings, 0 erreur) · `npm run build` (tsc + vite) = OK.
- **Backend** : `pytest tests/test_regression.py` (dont +2 BUG-102) = vert · suite complète hors e2e = **exit 0** · `ruff` = clean.

## Vérification navigateur human-like (1er regard, déroulé par Claude)
App lancée dans Chrome (MCP) contre un **backend isolé** (port dédié 17393, base jetable `/tmp`, **zéro donnée de Ludo touchée**), onboarding complété via API. Flux d'écriture réel déroulé :
- **P3 — Mémoire in-window** ✓ : le bouton Mémoire du header ouvre un **panneau dans la même fenêtre** (glisse depuis la droite, dashboard en backdrop), pas une fenêtre détachée.
- **P4 — création via store unique** ✓ : contact créé via la modale "Nouveau contact" → apparaît **instantanément** dans la liste Mémoire (compteur Contacts 0 → 1). Le log backend confirme la création via le chemin canonique `POST /api/memory/contacts` (routage B5).
- **P5 — recherche sémantique** ⚠️ **lecture initiale erronée** : j'avais lu le fait que taper le nom **masquait** le contact comme « le sémantique fonctionne ». C'était faux du point de vue utilisateur — un nom tapé doit **trouver** le contact, pas le cacher. Syn (2e regard) l'a justement classé **KO**. Corrigé en recherche hybride (section ci-dessous).
- Limite honnête : la **vue croisée CRM** (contact CRM visible en Mémoire) n'a pas pu être déroulée en navigateur car le CRM s'ouvre en **fenêtre séparée** (`window.open` bloqué par le navigateur — c'est l'architecture fenêtres-panels, précisément le sujet de la Phase 1). Elle est couverte au niveau code (B2 : CRMPanel lit `useContactsStore`) + tests unitaires, et confiée à **Syn** dans l'environnement Tauri réel (`B-test-script-syn.md`) pour un **2e regard indépendant**.

## Correctif P5 — recherche hybride (2e regard Syn, commit `ee61fae`)
**Constat de Syn** (compte rendu hub, environnement Tauri réel) : « P5 recherche sémantique KO en UI » — taper le nom d'un contact le faisait **disparaître** au lieu de le trouver (Qdrant renvoyait vide, l'UI affichait « Aucun contact »).

**Diagnostic** : `contactsStore.search()` appelait uniquement `/api/memory/search` (sémantique pur). Sans embedding pertinent (contact tout juste créé, Qdrant froid, ou requête = simple nom propre), le sémantique renvoie vide → le contact existant devient introuvable. C'est contre-intuitif pour l'utilisateur, qui s'attend à retrouver un contact en tapant son nom.

**Fix** : `search()` devient **hybride**.
- Filtre local immédiat sur `first_name`/`last_name`/`company`/`email` (`contactMatchesQuery`) : on retrouve **toujours** par le nom.
- Fusion sans doublon avec les résultats sémantiques (`mergeContactsById`, le local prime).
- Repli sur le seul filtre local si le sémantique **échoue** (pas de `throw`, recherche jamais cassée).

**Vérifications** :
- Unitaire : 9/9 `contactsStore.test.ts`, dont le scénario Syn explicite (« trouve par le NOM même si le sémantique renvoie vide ») + résilience (sémantique en erreur → repli local).
- Navigateur (2e passe, même backend isolé 17393, base jetable `/tmp`, **zéro donnée de Ludo touchée**) : contact « Revue P5Browser » créé, puis recherche `Revue` → **trouvé** ; `Browser` (substring du nom) → **trouvé** ; `ZzzNoMatchXY` → **« Aucun contact »** (le filtre filtre bien, ce n'est pas un « toujours afficher » cassé).

**Leçon** (mémorisée) : une UX « contre-intuitive mais techniquement explicable » reste un bug tant que l'utilisateur ne l'a pas validée. Le 2e regard indépendant (Syn) a rattrapé une lecture biaisée par l'implémentation.

## Notes / vigilance
- `crm.py` POST `/contacts` conserve sa sync Google Sheets ; B6 y ajoute juste l'embed Qdrant (résilient si Qdrant absent).
- Le défaut de couverture de tests composant du repo (6%) fait que la garantie de non-régression visuelle repose sur le typecheck + le test navigateur (Syn).
- Hors-périmètre (phases suivantes) : refonte visuelle des surfaces (Phase 1), consolidation des deux namespaces backend, tunnel de vente CRM (Phase 2).
