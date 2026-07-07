# Atelier documentaire - Design V1 (brainstorm validé 07/07/2026)

> Issu du brainstorming Ludo + Claude du 07/07/2026, déclenché par les retours
> de Dr_logic-3D (avril-juillet 2026, distillés dans le FEEDBACK-DISTILLED de
> Katia) : sa méthode manuelle de production documentaire (trame → sections →
> relances réinjectées → synthèse multi-sources → réorganisation contrôlée)
> coûte des heures de copier-coller et bute sur l'incapacité des LLM à
> réorganiser un gros document sans perte.

## Décisions de cadrage (Ludo, 07/07/2026)

| Question | Décision |
|---|---|
| Cible | **Le solopreneur** (utilisateur type THÉRÈSE). La mécanique de Dr_logic est le moteur sous le capot, pas l'interface. Vocabulaire simple, parcours guidé. |
| Cas d'usage V1 | **Rédiger un gros document guidé** de bout en bout : dossier de formation, guide client, propale 20-50 pages. Trame → sections validées une à une → export Word. |
| Stockage | **Entité Document dans la base THÉRÈSE** (SQLite chiffrée) : cohérence avec contacts/projets, recherche, RGPD. Export .md/.docx à la demande (circuit `/api/skills/download` existant). **Obsidian découplé** : éclaireur « connecter un vault comme SOURCE de connaissances » = chantier séparé, plus tard. |
| Approche | **A - Vue Document dédiée** (trame + section active + chat contextué). L'approche « tout dans le chat » recrée la douleur d'origine ; l'éditeur riche type Notion est démesuré (YAGNI). |

## Hors périmètre V1 (explicitement)

- Synthèse multi-sources (déposer des PDF → synthèse recentrée) : V2, le cas
  power-user de Dr_logic. Les fondations (identifiants stables, orchestrateur)
  la préparent.
- Restructuration assistée d'un document importé : V2 (l'invariant
  d'identifiants la rend possible).
- Réglages fins des relances (nombre, divergence, ton) : power-user, plus tard.
- Édition riche par blocs draggables : jamais en V1 - markdown + rendu suffit.
- Mode collaboratif, versions, diff : non.

## 1. Architecture

### Backend (FastAPI)
- `models/entities.py` :
  - `Document` : id, title, brief (description du besoin), status
    (`en_cours | termine`), project_id (nullable, FK Projet), contact_id
    (nullable), created_at/updated_at.
  - `DocumentSection` : **id stable généré à la création (uuid), JAMAIS
    recalculé** - c'est la garantie anti-perte. document_id, title, ordre
    (float ou rang), depth (0/1), brief de section (consigne 1 ligne),
    content (markdown), summary (résumé ~150 mots généré à la validation),
    status (`vide | brouillon | validee`), created_at/updated_at.
  - `DocumentPiste` : id, document_id, section_origine_id (nullable), texte,
    status (`nouvelle | exploree | ignoree`), created_at.
- `routers/documents.py` : CRUD document/sections/pistes +
  - `POST /api/documents/{id}/outline` : génère la trame depuis le brief
    (LLM, non-stream, renvoie les sections créées).
  - `POST /api/documents/sections/{id}/draft` : rédige UNE section en
    streaming SSE (même mécanique que le chat). Paramètre optionnel
    `instruction` (retouche : « raccourcis », « ajoute un exemple »).
  - `POST /api/documents/sections/{id}/validate` : passe en `validee` +
    génère et stocke le summary.
  - `GET /api/documents/{id}/export?format=md|docx` : assemblage markdown
    dans l'ordre de la trame → .md direct ou docx via skill docx-pro
    (même circuit que l'export de conversations livré le 07/07).
- `services/document_orchestrator.py` : construit le contexte de rédaction
  d'une section : brief document + trame complète (titres + consignes) +
  **résumés** des sections validées (pas leur texte intégral - budget tokens
  maîtrisé, un doc de 50 pages coûte comme une page) + consigne de la section
  + mémoire liée (contact/projet rattachés). Format de sortie du LLM :
  contenu markdown + liste `pistes[]` optionnelle (idées hors-section,
  routées vers DocumentPiste au lieu de polluer le texte).

### Frontend (React/Zustand)
- `navigationStore` : nouvelle vue `documents` (content-swap, pattern
  Projets/Indexation, Échap via resolveEscape).
- `components/documents/` : `DocumentsList` (liste + progression
  « 7/12 sections validées »), `DocumentWorkspace` (3 zones), `OutlineTree`
  (trame, drag & drop **listeners sur toute la ligne** - leçon BUG-041),
  `SectionEditor` (titre, consigne, rendu markdown, Rédiger/Retoucher/
  Valider, streaming en place), `PistesPanel` (volet droit repliable,
  badge compteur), `documentStore` (Zustand).
- actionRegistry : `document.new`, `document.open` (⌘K + Accueil).

## 2. Données et flux (cycle de vie)

1. **Création** : titre + brief 2-3 phrases + rattachement projet/contact
   optionnel (leur contexte nourrit la rédaction).
2. **Trame** : plan hiérarchique généré (sections + consignes 1 ligne),
   librement éditable (renommer/ajouter/supprimer/réordonner). Identifiants
   stables posés à la création. **Invariant de complétude** : toute
   réorganisation se vérifie en comparant les ensembles d'identifiants
   avant/après (l'idée de Dr_logic, en invariant de base).
3. **Rédaction** : section par section, ordre libre. Contexte LLM = brief +
   trame + résumés validés + consigne + mémoire. Jamais le document entier.
4. **Pistes** : le format de sortie permet au LLM de déposer les idées
   hors-section dans le panneau Pistes. « Développer cette piste » ouvre le
   chat contextué dessus.
5. **Export** : assemblage ordonné → .md ou .docx. Document `termine` quand
   toutes les sections sont validées (réouvrable).

## 3. Interface

- Entrées : ⌘K (`document.new`/`document.open`), carte Accueil, sidebar.
- `DocumentWorkspace` : gauche = trame (arborescence cliquable, statuts
  colorés tokens sémantiques theme-aware, drag & drop toute-ligne) ;
  centre = section active (titre, consigne éditable, markdown rendu,
  boutons Rédiger/Retoucher/Valider, streaming en direct) ; bas = chat
  contextué à la section (les instructions modifient le contenu en place) ;
  droite = volet Pistes repliable.
- DA : brutaliste éditorial en vigueur (btn-brutal, tags carrés, pastilles
  duotone cerclées). Pas d'emoji. Accents partout.

## 4. Cas d'erreur

- **Erreur LLM en rédaction** : section reste `brouillon` avec le texte
  partiel persisté, message causal (pattern erreurs email 07/07), bouton
  « Reprendre ». Chaque chunk est persisté au fil de l'eau.
- **Trame regénérée après rédaction** : jamais silencieux. Sections rédigées
  préservées et rattachées par identifiant ; celles sans place → « sections
  orphelines » visibles, jamais supprimées automatiquement.
- **Complétude** : vérification des identifiants à chaque réorganisation et
  à l'export ; un écart bloque avec explication.
- **Fermeture app en pleine rédaction** : tout est en base, l'atelier
  rouvre en l'état.
- **Provider sans streaming fiable / Ollama faible** : le draft section est
  un appel court - dégradation gracieuse déjà en place côté providers.

## Critères de succès V1

1. Un solopreneur produit un document de 20+ pages structuré en < 2 h de
   travail effectif, exporté en Word propre, sans copier-coller.
2. Dr_logic reproduit (en mode simple) sa méthode : aucune perte de contenu
   à la réorganisation, pistes capturées et réexplorables.
3. Zéro texte inventé hors des sections demandées (vérité d'exécution :
   chaque contenu est rattaché à une section validée par l'utilisateur).

## Prochaines étapes

1. `/plan` d'implémentation détaillé (tâches TDD, lots backend → front →
   orchestrateur → export, revues adversariales aux jointures).
2. Implémentation par lots avec validation visuelle avant toute release.
3. Bêta : ouvrir un thread Discord dédié avec Dr_logic comme co-testeur
   (il a les cas réels), avant l'annonce générale.
