# Plan d'implémentation — Phase 0 / Chantier B : Donnée unifiée

> **Pour l'exécutant :** TDD strict, test d'abord vu échouer, puis code minimal, puis commit. Étapes en cases `- [ ]`. Branche `chantier-revue-produit` (jamais main).

**But :** une seule source de vérité des contacts (`contactsStore`), Mémoire et CRM comme deux vues, recherche sémantique réelle, Mémoire repliée en panneau in-window.
**Archi :** store Zustand dédié qui réutilise l'API `memory.ts` existante (CRUD + `/api/memory/search`). `crmStore` se recentre sur projets/pipeline.
**Stack :** React 19 + Zustand 5 + TailwindCSS 4 + Tauri 2 ; tests Vitest (frontend), Pytest (backend).

Spec : `docs/revue-produit/phase0-B-donnee-unifiee-spec.md`.

---

## Lot B1 — `contactsStore` (fondation, TDD)
**Files :** Create `src/frontend/src/stores/contactsStore.ts` · Test `src/frontend/src/stores/contactsStore.test.ts`

Interface :
```ts
interface ContactsStore {
  contacts: ContactResponse[];
  searchResults: ContactResponse[] | null; // null = pas de recherche active
  loading: boolean;
  selectedContactId: string | null;
  fetchContacts: () => Promise<void>;
  createContact: (data: ContactCreatePayload) => Promise<ContactResponse>;
  updateContact: (id: string, patch: Partial<ContactResponse>) => Promise<void>;
  deleteContact: (id: string) => Promise<void>;
  search: (query: string) => Promise<void>;
  setSelectedContact: (id: string | null) => void;
  upsertLocal: (c: ContactResponse) => void;
  removeLocal: (id: string) => void;
}
```
Règle clé : aucune mutation locale avant confirmation API (anti-faux-succès). `search('')` remet `searchResults = null` (repli liste complète).

- [ ] B1.1 Écrire les tests vitest (mock de `../services/api/memory`) :
  - `createContact` n'ajoute à `contacts` qu'après résolution de l'API ; rejet ⇒ liste inchangée + throw.
  - `fetchContacts` peuple `contacts` et passe `loading` true→false.
  - `updateContact` patch le bon contact après confirmation.
  - `deleteContact` retire le contact ; idempotent si déjà absent.
  - `search('q')` appelle `searchMemory` et peuple `searchResults` ; `search('')` ⇒ `searchResults=null`.
- [ ] B1.2 Lancer `npm test -- contactsStore` → FAIL (store absent).
- [ ] B1.3 Implémenter `contactsStore.ts` (réutilise `listContacts/createContact/updateContact/deleteContact/searchMemory` de `memory.ts`).
- [ ] B1.4 `npm test -- contactsStore` → PASS.
- [ ] B1.5 Commit `feat(contacts): contactsStore source de vérité unique (P4)`.

## Lot B2 — CRM consomme `contactsStore`
**Files :** Modify `src/frontend/src/stores/crmStore.ts`, `src/frontend/src/components/crm/CRMPanel.tsx` (+ enfants lisant `useCRMStore().contacts`)

- [ ] B2.1 Test régression (grep source, idiome repo) : `crmStore.ts` n'expose plus `contacts`/`addContact`/`setContacts` (le store ne duplique plus les contacts).
- [ ] B2.2 Retirer de `crmStore` : `contacts`, `selectedContactId`, `setContacts`, `updateContact`, `addContact` + leur `partialize`. Garder projects + UI state.
- [ ] B2.3 CRMPanel et enfants lisent `useContactsStore().contacts` / `fetchContacts()` ; transitions de stage gardent l'endpoint CRM dédié.
- [ ] B2.4 `npm test` + `tsc` (typecheck via build) → vert ; corriger les références cassées.
- [ ] B2.5 Commit `refactor(crm): CRM lit contactsStore, crmStore recentré projets/pipeline`.

## Lot B3 — Mémoire consomme `contactsStore` + recherche sémantique (P5)
**Files :** Modify `src/frontend/src/components/memory/MemoryPanel.tsx`

- [ ] B3.1 Test : la recherche Mémoire appelle `contactsStore.search` (donc `/api/memory/search`), pas un filtre JS local. (test composant ou guard source selon faisabilité)
- [ ] B3.2 MemoryPanel lit `useContactsStore` ; la barre de recherche → `search(query)` debounce 250 ms ; affichage = `searchResults ?? contacts`.
- [ ] B3.3 `npm test` + typecheck → vert.
- [ ] B3.4 Commit `feat(memory): Mémoire sur contactsStore + recherche sémantique réelle (P5)`.

## Lot B4 — Mémoire in-window (P3)
**Files :** Modify `src/frontend/src/components/chat/ChatHeader.tsx`, `services/windowManager.ts` ; Remove/replier `MemoryPanelStandalone.tsx`

- [ ] B4.1 Recenser tous les `openPanelWindow('memory')` (grep) avant suppression.
- [ ] B4.2 ChatHeader : remplacer l'ouverture de la fenêtre Mémoire par le toggle in-window (`panelStore.toggleMemoryPanel`).
- [ ] B4.3 Retirer l'enregistrement `memory` de `windowManager`/PanelWindow et le composant `MemoryPanelStandalone`.
- [ ] B4.4 Vérifier zéro bouton mort (grep résiduel) ; `npm test` + typecheck → vert.
- [ ] B4.5 Commit `refactor(memory): Mémoire en panneau in-window, fin de la fenêtre détachée (P3)`.

## Lot B5 — Création unifiée depuis le chat
**Files :** Modify le chemin de création contact côté chat (EntitySuggestion / handler de création)

- [ ] B5.1 Test : valider qu'une création d'entité depuis le chat passe par `contactsStore.createContact` (donc visible Mémoire ET CRM).
- [ ] B5.2 Rebrancher la création contact du chat sur `contactsStore.createContact`.
- [ ] B5.3 `npm test` + typecheck → vert.
- [ ] B5.4 Commit `fix(chat): création de contact via contactsStore (visible des deux vues)`.

## Lot B6 — Backend : helper Sheets partagé + ré-embed à l'update
**Files :** Modify `src/backend/app/routers/crm.py` (extraire helper Sheets), `src/backend/app/routers/memory.py` (appel helper sur création explicite + ré-embed sur PATCH)

- [ ] B6.1 Tests pytest : helper Sheets pousse si `sync_sheets=true` + spreadsheet configuré, sinon non ; `PATCH /memory/contacts/{id}` ré-embed dans Qdrant (mock Qdrant).
- [ ] B6.2 Extraire la logique Sheets de `crm.py` POST dans `_sync_contact_to_sheets(session, contact)` ; l'appeler depuis le chemin canonique avec flag (défaut faux pour création auto chat).
- [ ] B6.3 S'assurer que `update_contact` (PATCH) déclenche `_embed_contact`.
- [ ] B6.4 `uv run pytest tests/test_regression.py tests/test_routers_*.py -q` → vert.
- [ ] B6.5 Commit `feat(contacts): helper Sheets partagé + ré-embed Qdrant à la mise à jour`.

## Vérification finale (après les 6 lots)
- [ ] V1 `npm run build` (tsc + vite) → vert ; `npm run lint` ≤ baseline ; `npm test` → vert.
- [ ] V2 `uv run pytest tests/ --ignore=tests/e2e -q` → vert.
- [ ] V3 Lancer l'app (backend + Vite) et **tests human-like sur navigateur (Chrome MCP)** : créer un contact depuis le chat → visible Mémoire ET CRM ; recherche sémantique ; pas de fenêtre Mémoire morte ; pas de faux succès.
- [ ] V4 **Envoi à Syn** (DQ SYN) pour qu'elle teste aussi sur navigateur — deux regards croisés.
- [ ] V5 Rapport de chantier + MAJ roadmap.

## Couverture spec (self-review)
- P3 → Lot B4. P4 → Lots B1/B2/B5/B6. P5 → Lot B3. Sheets ciblée → B6. Anti-faux-succès → B1. Ré-embed update → B6.
