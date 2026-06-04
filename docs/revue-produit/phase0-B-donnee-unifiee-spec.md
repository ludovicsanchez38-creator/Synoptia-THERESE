# Spec — Phase 0 / Chantier B : Donnée unifiée

**Date** : 2026-06-04 · **Branche** : `chantier-revue-produit` · **Statut** : validé, prêt pour plan d'implémentation
**Pistes couvertes** : P3 (une seule Mémoire), P4 (un seul Contact Mémoire↔CRM), P5 (recherche sémantique réelle)
**Décisions cadre** : cible solopreneur/TPE · approche **frontend-first** (la table `contacts` est déjà unique en base) · store **dédié** `contactsStore` · Mémoire repliée en **panneau in-window** · sync Sheets **ciblée**.

## 1. Contexte et problème
- La base a **une seule table `contacts`** (`models/entities.py`), portant déjà les champs mémoire (nom, email, notes, tags, scope), CRM (stage, score, source, last_interaction) et RGPD, avec relations projets/activités/factures.
- Mais **deux surfaces d'API** sur cette table : `/api/memory/contacts` et `/api/crm/contacts`, aux effets de bord **divergents** :
  - `/api/memory/contacts` POST → embed Qdrant + score dynamique + log d'activité (pas de Sheets).
  - `/api/crm/contacts` POST → sync Google Sheets + score figé 50 (**pas d'embed Qdrant**).
- **Deux stores frontend** sans état partagé : `crmStore` (données contacts CRM) et un fetch local dans la Mémoire (`MemoryPanel`), plus une **fenêtre Tauri détachée** `MemoryPanelStandalone`. D'où : contact créé d'un côté invisible de l'autre, doublons, et contacts CRM non indexés pour la recherche sémantique.
- La recherche de la Mémoire est un **filtre texte JS local**, alors que `POST /api/memory/search` (Qdrant) existe déjà mais n'est pas utilisé par l'UI.

## 2. Objectif (résultat utilisateur)
« Thérèse fait ce qu'elle dit, et mes contacts sont au même endroit partout, retrouvables par leur contexte. » Un contact = un seul objet, vu sous l'angle Mémoire (notes, sémantique, RGPD) ou Pipeline (stage, score, activités), sans désync ni doublon.

## 3. Architecture cible
- **`contactsStore` (nouveau, Zustand)** = source de vérité unique des contacts.
  - État : `contacts: ContactResponse[]`, `searchResults: ContactResponse[]`, `loading: boolean`, `selectedContactId: string | null`.
  - Actions : `fetchContacts()`, `createContact(payload)`, `updateContact(id, patch)`, `deleteContact(id)`, `search(query)`, `upsertLocal(contact)`, `removeLocal(id)`.
  - Les mutations locales ne s'appliquent qu'**après** confirmation API (pas d'optimistic trompeur — pont vers le Chantier A).
- **`panelStore`** : inchangé dans son rôle (visibilité des panneaux UI uniquement).
- **`crmStore`** : recentré sur **projets + pipeline** (transitions de stage, déclenchement de scoring) ; ne détient plus de copie des contacts, les lit depuis `contactsStore`.
- **Mémoire** et **CRM** consomment tous deux `contactsStore`. La création depuis le chat (entity suggestion) passe aussi par `contactsStore.createContact()`.

## 4. P4 — un seul Contact
- **CRUD canonique = `/api/memory/contacts`** : POST (create), GET / GET{id} (read), `PATCH /contacts/{id}` (update général), DELETE{id} — tous présents et porteurs des effets de bord riches (embed Qdrant + score + activité). `contactsStore` les utilise.
- **Distinction importante** : les **transitions de stage** du pipeline restent sur `PATCH /api/crm/contacts/{id}/stage` (opération CRM spécifique, pilotée par `crmStore`). Seule la **modification des champs généraux** d'un contact passe par le PATCH canonique mémoire.
- **Effet attendu** : tout contact (chat, Mémoire, CRM) est créé une fois, visible des deux vues, indexé pour la recherche sémantique. Disparition du bug « contact annoncé créé mais absent ».
- **Sync Google Sheets (décision)** : la création unifiée pousse vers Sheets **uniquement si un spreadsheet est configuré ET pour les ajouts explicites** (Mémoire/CRM), **pas** pour les entités auto-détectées dans le chat. Implémentation : extraire la logique Sheets de `crm.py` POST dans un **helper partagé** appelé par le chemin canonique avec un flag `sync_sheets` (par défaut faux pour les créations issues du chat). Petit ajout backend **additif**, pas une consolidation d'API.
- `crm.py` POST `/contacts` et `/import` restent en place (non cassés) ; le frontend ne les utilise plus pour le CRUD courant (le store passe par le chemin canonique). Les opérations spécialisées CRM (recalculate-score, import preview) restent côté `crmStore`/CRM.

## 5. P3 — une seule Mémoire (in-window)
- **Suppression de la fenêtre Tauri détachée pour la Mémoire** (`MemoryPanelStandalone` + son enregistrement dans `windowManager`/`openPanelWindow('memory')`). Raison : Zustand ne synchronise pas entre fenêtres Tauri (contextes JS isolés) → la seule façon fiable d'avoir « une seule Mémoire » est un panneau in-window unique.
- La Mémoire devient **un panneau dans la fenêtre principale**, piloté par `panelStore.showMemoryPanel`, adossé à `contactsStore`. `ChatHeader` : remplacer `openPanelWindow('memory')` par le toggle du panneau in-window.
- Aligné avec la Phase 1 (1 fenêtre + panneaux contextuels) ; pas de plomberie d'événements cross-fenêtres.

## 6. P5 — recherche sémantique réelle
- La barre de recherche de la Mémoire appelle `contactsStore.search(query)` → `POST /api/memory/search` (Qdrant), debounce ~250 ms, état `loading`, repli sur la liste complète si requête vide.
- Résultat : retrouver un contact par rôle/contexte/notes, pas seulement par nom.

## 7. Gestion d'erreurs
- Toute action `contactsStore` : succès UI **seulement** après réponse OK de l'API ; échec → message clair + état inchangé, jamais de faux succès. Les erreurs réseau/serveur remontent un message lisible (pas de `catch` muet).

## 8. Stratégie de tests (TDD, écrits avant le code)
- **Backend** (pytest) :
  - Le helper Sheets partagé pousse vers Sheets quand `sync_sheets=true` + spreadsheet configuré, et ne pousse pas sinon.
  - Le chemin canonique de création embed bien le contact dans Qdrant (mock du service Qdrant) et calcule un score.
  - Guard de régression (idiome du repo) : la création de contact via le chemin canonique reste indexée Qdrant.
- **Frontend** (vitest) :
  - `contactsStore.createContact` ajoute à la liste unique après confirmation ; `deleteContact` idempotent ; `updateContact` patch le bon contact.
  - `search()` appelle `/api/memory/search` et peuple `searchResults` ; requête vide → liste complète.
  - Mémoire et CRM lisent la même source (un contact créé est présent pour les deux).
  - Aucune mutation locale avant réponse API (test du non-optimistic).

## 9. Périmètre
**Inclus** : `contactsStore`, bascule Mémoire/CRM sur ce store, suppression de la fenêtre Mémoire détachée, branchement recherche sémantique, helper Sheets partagé + flag.
**Exclus (YAGNI / autres phases)** : refonte visuelle des surfaces (Phase 1), consolidation des deux namespaces backend en `/api/contacts` (cleanup ultérieur possible), Chantier A (vérité d'exécution générale des actions) traité séparément, tunnel de vente CRM complet (Phase 2).

## 10. Risques et points de vigilance
- **MemoryPanelStandalone** : vérifier tous les points d'entrée (ChatHeader, raccourcis, dashboard) qui ouvrent la fenêtre Mémoire avant de la retirer, pour ne pas laisser de bouton mort.
- **crmStore** : s'assurer qu'aucun consommateur ne lit encore `crmStore.contacts` après bascule (sinon liste vide).
- **Sheets** : confirmer le format de ligne attendu par le Sheet « Clients » pour ne pas casser la sync existante.
- **Qdrant en test** : mocker l'embedding pour éviter des appels réels (cf. dette technique repo sur les tests à appels externes).
- **Ré-embed à la mise à jour** : vérifier que `PATCH /api/memory/contacts/{id}` ré-indexe le contact dans Qdrant quand ses notes/champs sémantiques changent (sinon la recherche sémantique reste sur l'ancienne version). À couvrir par un test.

## 11. Carte des changements (pour le plan)
- **Nouveau** : `src/frontend/src/stores/contactsStore.ts`.
- **Modifié** : `crmStore.ts` (retrait des contacts, lecture depuis contactsStore), `MemoryPanel.tsx` (store + recherche sémantique), `CRMPanel.tsx` (store), `ChatHeader.tsx` (toggle in-window au lieu de fenêtre), entity suggestion / création contact côté chat, `services/api/memory.ts` + `crm.ts` (le store centralise les appels).
- **Supprimé/replié** : `MemoryPanelStandalone.tsx` + enregistrement `memory` dans `windowManager`/`openPanelWindow`.
- **Backend (additif)** : helper Sheets partagé + flag `sync_sheets` sur le chemin de création canonique.
