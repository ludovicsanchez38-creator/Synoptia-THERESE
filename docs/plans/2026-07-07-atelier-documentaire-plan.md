# Plan : Atelier documentaire V1

**Objectif** : rédaction guidée d'un gros document (trame → sections validées une à une → export Word), design validé le 07/07 (`docs/plans/2026-07-07-atelier-documentaire-design.md`).
**Architecture** : entités Document/DocumentSection (id stables anti-perte)/DocumentPiste en base ; orchestrateur backend qui contextualise chaque section (brief + trame + résumés validés) ; routers outline/draft SSE/validate/export ; vue frontend content-swap (trame + section + chat contextué + Pistes).
**Stack** : FastAPI + SQLModel (patterns du repo), React/Zustand, SSE existant, export via `/api/skills/download`.
**Fichiers impactés** : `src/backend/app/models/entities.py`, `src/backend/app/models/schemas_documents.py` (neuf), `src/backend/app/services/document_orchestrator.py` (neuf), `src/backend/app/routers/documents.py` (neuf), `src/backend/app/main.py`, `tests/test_documents_*.py` (neufs), `src/frontend/src/stores/{navigationStore,documentStore}.ts`, `src/frontend/src/services/api/documents.ts` (neuf), `src/frontend/src/components/documents/*` (neufs), `src/frontend/src/lib/actionRegistry.ts`, `src/frontend/src/components/chat/ChatLayout.tsx`, `src/frontend/src/components/home/QuickActions.tsx`.
**Estimation** : 21 tâches en 5 lots, ~2-3 sessions. Branche `feat/atelier-documentaire`, jamais sur main sans suite verte.

**Règles transverses** (appliquées à chaque tâche, non répétées) :
- TDD : le test de la tâche est écrit AVANT ou AVEC le code, `uv run pytest` depuis la RACINE.
- Accents français partout, pas d'emoji, tokens sémantiques theme-aware côté UI.
- `mypy` ne doit pas dépasser 993 erreurs (baseline actuelle réelle) : tout nouveau code est typé.
- Poser `.agents-sync-paused` pendant les gros lots (le hook auto-wip commite sinon).
- Revue adversariale (3 lentilles : exactitude/régression/honnêteté) à la fin des lots B, C et D.

---

## Lot A - Fondations backend (entités + CRUD)

### Tâche A1 : entités Document, DocumentSection, DocumentPiste

**Fichiers** : modifier `src/backend/app/models/entities.py` ; créer `tests/test_documents_entities.py`.

**Instructions** : ajouter en fin de fichier, en suivant le pattern exact des entités existantes (`generate_uuid`, timestamps UTC) :

```python
class Document(SQLModel, table=True):
    """Document long construit dans l'atelier documentaire (design 07/07/2026)."""

    __tablename__ = "documents"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str
    brief: str = ""  # description du besoin, nourrit chaque section
    status: str = Field(default="en_cours")  # en_cours | termine
    project_id: str | None = Field(default=None, foreign_key="projects.id")
    contact_id: str | None = Field(default=None, foreign_key="contacts.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentSection(SQLModel, table=True):
    """Section d'un document. L'id est STABLE : posé à la création, jamais
    recalculé - c'est l'invariant anti-perte (vérification de complétude par
    comparaison d'ensembles d'ids à chaque réorganisation et à l'export)."""

    __tablename__ = "document_sections"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    title: str
    brief: str = ""  # consigne d'une ligne : ce que la section doit couvrir
    order: float = 0.0  # rang trié (float = insertion entre deux sans renuméroter)
    depth: int = 0  # 0 = section, 1 = sous-section
    content: str = ""  # markdown rédigé
    summary: str = ""  # résumé ~150 mots généré à la validation (contexte des suivantes)
    status: str = Field(default="vide")  # vide | brouillon | validee
    orphan: bool = False  # section détachée par une regénération de trame (jamais supprimée auto)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentPiste(SQLModel, table=True):
    """Idée annexe capturée pendant la rédaction (les « relances » de Dr_logic)."""

    __tablename__ = "document_pistes"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    document_id: str = Field(foreign_key="documents.id", index=True)
    section_origine_id: str | None = Field(default=None)
    texte: str
    status: str = Field(default="nouvelle")  # nouvelle | exploree | ignoree
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

NB : les nouvelles TABLES sont créées au boot par `SQLModel.metadata.create_all` (database.py:478) - aucune migration ad-hoc nécessaire (réservées aux nouvelles colonnes sur tables existantes).

**Vérification** :
- [ ] `uv run pytest tests/test_documents_entities.py -q` vert (test : créer un document + 2 sections + 1 piste via `db_session`, relire, vérifier ids uuid distincts et statuts par défaut)
- [ ] `uv run pytest tests/test_regression.py -q` vert (aucune régression schéma)

**Commit** : `feat(documents): entités Document/DocumentSection/DocumentPiste (ids stables anti-perte)`

### Tâche A2 : schémas API

**Fichiers** : créer `src/backend/app/models/schemas_documents.py`.

**Instructions** : schémas Pydantic (pattern `schemas_voice.py`) : `DocumentCreate` (title, brief, project_id?, contact_id?), `DocumentResponse` (tous champs + `sections_total`/`sections_validees`), `SectionResponse` (tous champs), `SectionUpdate` (title?, brief?, content?, order?, depth?), `SectionsReorder` (liste `{id, order, depth}`), `PisteResponse`, `PisteUpdate` (status), `DraftRequest` (instruction: str | None = None). Tout typé, docstrings une ligne.

**Vérification** :
- [ ] `uv run python -c "import sys; sys.path.insert(0,'src/backend'); from app.models.schemas_documents import DocumentCreate"` sans erreur

**Commit** : `feat(documents): schémas API de l'atelier documentaire`

### Tâche A3 : router CRUD documents + sections

**Fichiers** : créer `src/backend/app/routers/documents.py` ; modifier `src/backend/app/main.py` (enregistrer le router, préfixe `/api/documents`, chercher les `include_router` existants) ; créer `tests/test_documents_router.py`.

**Instructions** : endpoints CRUD purs (pattern `routers/calendar.py` pour la forme, session `Depends(get_session)`) :
- `POST /api/documents` (DocumentCreate → DocumentResponse)
- `GET /api/documents` (liste avec compteurs sections via requêtes agrégées)
- `GET /api/documents/{id}` (document + sections triées par `order` + pistes)
- `DELETE /api/documents/{id}` (supprime sections et pistes associées, transactionnel)
- `PATCH /api/documents/sections/{id}` (SectionUpdate ; un PATCH de `content` passe le statut à `brouillon` si `vide`)
- `POST /api/documents/{id}/sections` (créer une section manuelle : title, brief, order, depth)
- `POST /api/documents/{id}/sections/reorder` (SectionsReorder) : **vérification de complétude AVANT écriture** - l'ensemble des ids reçus doit être exactement l'ensemble des ids non-orphelins en base, sinon 409 avec le détail (ids manquants / inconnus). C'est l'invariant du design, testé explicitement.
- `GET/POST/PATCH pistes` : liste, création manuelle, changement de statut.

**Vérification** :
- [ ] `uv run pytest tests/test_documents_router.py -q` vert - tests clés : CRUD nominal ; reorder avec id manquant → 409 et AUCUNE écriture ; reorder valide réordonne ; delete cascade
- [ ] `uv run mypy src/backend/app --ignore-missing-imports | grep -c ' error:'` ≤ 993

**Commit** : `feat(documents): router CRUD + réorganisation gardée par l'invariant de complétude`

---

## Lot B - Orchestrateur (le cerveau)

### Tâche B1 : contexte de rédaction d'une section

**Fichiers** : créer `src/backend/app/services/document_orchestrator.py` ; créer `tests/test_document_orchestrator.py`.

**Instructions** : fonctions PURES testables sans LLM ni DB :

```python
def build_outline_prompt(title: str, brief: str) -> str: ...
def parse_outline_response(raw: str) -> list[dict]:  # [{title, brief, depth}]
    """Parse la réponse LLM (JSON attendu, tolérant aux fences ```json)."""
def build_section_context(
    document: "Document",
    sections: list["DocumentSection"],  # triées par order
    target: "DocumentSection",
    instruction: str | None = None,
) -> str:
    """Brief document + trame complète (titres+consignes) + RÉSUMÉS des
    sections validées (jamais leur texte intégral) + consigne de la cible
    + instruction de retouche éventuelle. Budget tokens maîtrisé."""
def build_summary_prompt(section: "DocumentSection") -> str: ...
def parse_draft_output(raw: str) -> tuple[str, list[str]]:
    """Sépare le contenu markdown des pistes : le prompt demande un bloc
    final optionnel 'PISTES:' (une par ligne, préfixe '- '). Retourne
    (contenu_sans_bloc, [pistes])."""
```

Prompts en français, format de sortie explicite. `parse_outline_response` : gérer JSON pur, fences, et lever `ValueError` claire sinon (le router transformera en 502 « trame illisible, réessaie »).

**Vérification** :
- [ ] Tests unitaires purs verts : parsing outline (JSON pur/fencé/invalide), parse_draft_output (avec/sans bloc PISTES), build_section_context contient les résumés validés et PAS le contenu intégral des autres sections, instruction incluse quand fournie

**Commit** : `feat(documents): orchestrateur - prompts et parsing purs (contexte par résumés)`

### Tâche B2 : génération de trame (outline)

**Fichiers** : modifier `src/backend/app/routers/documents.py` ; compléter `tests/test_documents_router.py`.

**Instructions** : `POST /api/documents/{id}/outline` : garde 409 si des sections non-vides existent déjà (jamais de regénération silencieuse - proposer plutôt la création manuelle de sections) ; appelle `llm_service.generate_content(prompt=build_outline_prompt(...))` (signature : `src/backend/app/services/llm.py:803`) ; parse ; crée les `DocumentSection` (order = 10.0, 20.0, 30.0... - pas d'espacement de 1 : insertion facile) ; renvoie les sections. LLM mocké dans les tests (patch `generate_content`).

**Vérification** :
- [ ] Tests : trame nominale créée et triée ; réponse LLM illisible → 502 et aucune section créée ; document avec sections rédigées → 409

**Commit** : `feat(documents): génération de trame (sections à ids stables, jamais de regénération silencieuse)`

### Tâche B3 : rédaction d'une section en streaming + validation

**Fichiers** : modifier `src/backend/app/routers/documents.py`, `src/backend/app/services/document_orchestrator.py` ; compléter les tests.

**Instructions** :
- `POST /api/documents/sections/{id}/draft` (DraftRequest) : SSE (modèle : `_command_stream` de `routers/chat.py` pour le format `data: {...}` + `StreamingResponse` avec les mêmes headers). Flux : chunks `{type:"text", content}` streamés depuis `llm_service.stream_response(context)` ; à la fin, `parse_draft_output` sépare pistes → `DocumentPiste` créées ; contenu persisté (statut `brouillon`) ; chunk final `{type:"done", section_id}`. **Persistance au fil de l'eau** : accumuler et écrire le contenu partiel en base toutes les ~2 s (le design exige zéro perte sur fermeture d'app) ; en cas d'erreur provider, chunk `{type:"error", content: message causal}` et le partiel RESTE en base.
- `POST /api/documents/sections/{id}/validate` : génère le `summary` via `generate_content(build_summary_prompt(...))` (fallback : 300 premiers caractères du contenu si le LLM échoue - la validation ne doit jamais bloquer), statut `validee`. Si toutes les sections non-orphelines sont `validee` → document `termine`.
- Tests : stream avec provider mocké (générateur async de chunks) → contenu persisté + pistes créées ; erreur provider à mi-course → partiel en base + statut `brouillon` ; validate → summary + statuts.

**Vérification** :
- [ ] Tests du lot verts + `uv run pytest tests/ --ignore=tests/e2e -q --timeout=30` : pas de régression (hors 2 artefacts Ollama locaux connus)
- [ ] **Revue adversariale du lot B** (3 lentilles) - corriger avant de continuer

**Commit** : `feat(documents): rédaction SSE par section (persistance continue) + validation avec résumé`

---

## Lot C - Export

### Tâche C1 : assemblage et export md/docx

**Fichiers** : modifier `src/backend/app/routers/documents.py`, `document_orchestrator.py` ; compléter les tests.

**Instructions** : `assemble_markdown(document, sections)` (titres `##`/`###` selon depth, ordre `order`, sections orphelines EXCLUES mais listées en annexe si non vides) ; `GET /api/documents/{id}/export?format=md|docx` : **vérification de complétude d'abord** (toute section non-orpheline doit exister - comparaison d'ids, 409 sinon) ; réutiliser TEL QUEL le pattern de l'export de conversations (`routers/chat.py::export_conversation`, commit e6c25b1) : md écrit dans `registry.output_dir` (convention `{titre}_{id8}.md`), docx via `registry.execute("docx-pro", ...)`, réponse `{file_name, download_url}`.

**Vérification** :
- [ ] Tests : export md → download réel via `/api/skills/download/{id}` contient les titres dans l'ordre ; document vide → 400 ; format inconnu → 400
- [ ] Test manuel : `curl` export d'un document de 3 sections, ouvrir le .md

**Commit** : `feat(documents): export md/docx par le circuit des documents générés`

---

## Lot D - Frontend

### Tâche D1 : API client + store

**Fichiers** : créer `src/frontend/src/services/api/documents.ts` (+ exports dans `index.ts`) ; créer `src/frontend/src/stores/documentStore.ts`.

**Instructions** : `documents.ts` : miroir typé des endpoints (pattern `chat.ts` ; le draft SSE suit `streamMessage` - lire son implémentation `chat.ts:130` pour le parsing `data:`). `documentStore` (Zustand, pattern `taskStore`) : `documents`, `currentDocument` (avec sections+pistes), `sectionActive`, actions `load/open/create/updateSection/reorder/draftSection (consomme le stream, met à jour le contenu au fil de l'eau)/validateSection/exportDocument`.

**Vérification** :
- [ ] `npx tsc --noEmit` vert ; test Vitest du store : draft simule 3 chunks → contenu concaténé, statut brouillon

**Commit** : `feat(documents): api client + documentStore (streaming consommé au fil de l'eau)`

### Tâche D2 : vue navigation + liste des documents

**Fichiers** : modifier `src/frontend/src/stores/navigationStore.ts` (ajouter `'documents'` au type `AppView` ligne ~21) ; créer `src/frontend/src/components/documents/DocumentsList.tsx` ; modifier `src/frontend/src/components/chat/ChatLayout.tsx` (rendu lazy de la vue, modèle : la vue `files`/`projects` - même wrapper `flex-1 min-h-0`, leçon 0.24.3).

**Instructions** : liste avec progression (« 7/12 sections validées », barre fine), bouton « Nouveau document » → modale légère (titre + brief + projet lié optionnel - liste des projets via l'api existante), clic → ouvre le workspace (state du store). Vide guidé : une phrase + bouton créer.

**Vérification** :
- [ ] Vitest : la liste rend les documents mockés + la progression ; navigation : `setView('documents')` affiche la vue, Échap revient (resolveEscape gère déjà le retour de vue - vérifier qu'aucun écouteur local n'est ajouté)

**Commit** : `feat(documents): vue Documents (liste + création) dans la navigation content-swap`

### Tâche D3 : atelier - trame + section active

**Fichiers** : créer `src/frontend/src/components/documents/DocumentWorkspace.tsx`, `OutlineTree.tsx`, `SectionEditor.tsx` (+ tests Vitest).

**Instructions** :
- `OutlineTree` : arborescence triée (indentation par depth), statuts en tags carrés theme-aware (`text-success`/`text-warning`/`text-text-muted`), clic → section active. Drag & drop @dnd-kit : **listeners sur toute la ligne** + `onDragCancel` + activationConstraint 8px (copier le pattern `ProjectsKanban.tsx` post-BUG-041, PAS l'ancien pattern poignée) ; au drop → `reorder` (l'API refuse avec 409 si incohérence - afficher l'erreur, recharger).
- `SectionEditor` : titre + consigne éditables (PATCH au blur), contenu markdown rendu (composant de rendu du chat réutilisé - chercher l'usage `react-markdown`/`remark-gfm` dans `MessageBubble`), boutons « Rédiger » (draft stream affiché en direct), « Retoucher » (champ instruction → draft avec instruction), « Valider ». États d'erreur : message causal + bouton Reprendre (le partiel est déjà en base).
- Tests : drag depuis le corps de la ligne (pattern `TaskKanban.test.tsx`, y compris le gotcha click-suppression : test de clic AVANT les tests de drag) ; le stream met le contenu à jour ; Valider appelle l'API et passe le tag.

**Vérification** :
- [ ] Vitest verts ; `npx tsc --noEmit` ; lint ≤ 27 warnings

**Commit** : `feat(documents): atelier - trame draggable (pattern BUG-041) + éditeur de section streamé`

### Tâche D4 : panneau Pistes + ⌘K + Accueil

**Fichiers** : créer `src/frontend/src/components/documents/PistesPanel.tsx` ; modifier `src/frontend/src/lib/actionRegistry.ts`, `src/frontend/src/components/home/QuickActions.tsx`.

**Instructions** : volet droit repliable (badge compteur des `nouvelle`), chaque piste : texte + « Explorer » (statut `exploree` + préremplit le champ instruction de la section d'origine) + « Ignorer ». actionRegistry : `{ id: 'documents.open', label: 'Atelier documentaire', group: 'Navigation', keywords: ['document', 'rédiger', 'dossier'], run: () => nav().setView('documents') }` + `documents.new`. Carte Accueil « Rédiger un document » dans QuickActions (registre).

**Vérification** :
- [ ] Vitest : piste explorée disparaît du badge ; ⌘K « Atelier » navigue
- [ ] **Revue adversariale du lot D**

**Commit** : `feat(documents): panneau Pistes + entrées ⌘K et Accueil`

---

## Lot E - Intégration et qualité

### Tâche E1 : vérification visuelle réelle (preview navigateur)

**Instructions** : pattern de la session voix locale du 07/07 : `preview_start` `therese-backend-test` (data_dir temp, launch.json de ~/.claude) + `therese-frontend` ; onboarding complété via `POST /api/config/onboarding-complete` ; dérouler le parcours complet avec le provider mocké impossible en preview → utiliser Ollama local si dispo, sinon vérifier trame/édition/reorder/export et documenter que le draft réel sera validé à la recette. Screenshots des 3 zones + export .md téléchargé.

**Vérification** :
- [ ] Parcours créer → trame → éditer → réordonner → exporter vérifié en navigateur, captures dans la PR

### Tâche E2 : suite complète + PR + doc

**Instructions** : `uv run pytest tests/ --ignore=tests/e2e -q --timeout=30` + suite frontend + mypy ≤ 993 + ruff ; PR `feat/atelier-documentaire` → main avec captures ; MAJ `CLAUDE.md` du repo (section modules : + Atelier documentaire) et `docs/CHANGELOG.md` ; fiche recette pour Dr_logic (thread Discord dédié APRÈS release, avec ses cas réels).

**Vérification** :
- [ ] CI 6/6 verte sur la PR ; dette éventuelle tracée au CLAUDE.md

**Commit final** : PR squash `feat(documents): atelier documentaire V1 (trame, rédaction guidée, pistes, export)`

---

## Hors périmètre rappelé (ne pas dériver)
Synthèse multi-sources, restructuration d'un document importé, réglages fins des relances, éditeur riche, collaboration : V2+. Le panneau Pistes V1 = capture + explorer/ignorer, rien de plus.
