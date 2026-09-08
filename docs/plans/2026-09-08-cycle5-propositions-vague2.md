# Cycle 5, vague 2 : cinq propositions acceptées par Ludo (design court, avant code)

Contexte : boucle `boucle-amelioration-app`, cycle 5 en `IMPLEMENT`. Ludo a
tranché le portail humain le 08/09/2026 : onze propositions acceptées, dont
six petites déjà livrées (P-046, P-047, P-050, P-052, P-053, P-054, commits
`cefe1d66` à `67eb96a4`). Restent cinq, plus lourdes : ce document est le
design à challenger avant d'écrire du code (rituel COCO puis TDD).

Contraintes de fond : aucune perte de fonctionnalité ; toute écriture garde
son parcours de confirmation existant ; pas de nouveau mécanisme fail-open ;
un sujet = un commit, test rouge d'abord, sabotage après.

## P-056 · La génération de trame de l'Atelier devient un traitement annulable

**Constat.** `POST /api/documents/{id}/outline` (`routers/documents.py:547`)
appelle `llm_service.generate_content` en ligne, sans rien enregistrer dans le
registre des traitements (`services/traitements.py`). Donc ni suivi dans
« Travaux », ni levier d'arrêt : l'auditeur a vu la sienne courir 3 min 20 s.
Le Board fait déjà l'inverse (`routers/board.py:199`) : `creer_traitement`,
`demarrer()`, `lier_adaptateur(AnnulationParTacheAsyncio(tache))`, et
`annulation_demandee` passé au service.

**Design.**
1. Backend : dans `generate_outline`, après le garde-fou 409, créer un
   traitement `type="document_outline"`, `label=document.title[:80]`,
   `entity_id=document_id` (best-effort comme le Board : un échec du registre
   n'empêche pas la génération). `await handle.demarrer()` ; l'appel LLM tourne
   dans une `asyncio.Task` liée par `lier_adaptateur(AnnulationParTacheAsyncio(tache))`.
   Fin normale → `handle.terminer_succes()` (nom exact à lire dans
   `TraitementHandle`) ; `ValueError` du parseur → échec + 502 comme aujourd'hui ;
   `AnnuleAvantDemarrage` ou `CancelledError` → le registre marque CANCELLED
   et la route répond **409 `{"detail": "Génération de la trame annulée.",
   "code": "outline_cancelled"}`** sans écrire de section. La déconnexion du
   client pendant l'attente ne doit pas laisser de traitement RUNNING
   orphelin (leçon B-653 : clôture dans un `finally`).
2. Frontend : le client ne connaît pas l'identifiant du traitement pendant
   que le POST est en vol. Deux voies, à trancher :
   (a) le client génère un `task_id` (uuid) et l'envoie dans le corps
   `{ "task_id": "…" }` ; `creer_traitement` accepte un id fourni ;
   (b) le client lit `GET /api/processing-tasks?actives=true` et filtre
   `type === 'document_outline' && entity_id === documentId`.
   Préférence : (b), aucun changement de contrat d'écriture, et « Travaux »
   liste déjà les actifs ; (a) seulement si (b) est jugé trop racé.
3. UI : dans l'état « Trame en cours » (`SectionEditor` prop `trameEnCours`),
   un bouton « Annuler la génération » qui appelle `annulerTraitement(id)` ;
   `documentStore.generateOutline` traite le 409 `outline_cancelled` comme
   une fin neutre (message « Génération annulée », pas une erreur rouge).
   Le panneau « Travaux » affiche le type sous un libellé lisible (« Trame
   du document »).

**Tests.** Backend : route qui enregistre un traitement (lister actifs pendant
l'appel, avec un faux LLM qui attend un événement) ; `demander_arret` pendant
l'appel → 409 `outline_cancelled`, zéro section, traitement CANCELLED ; fin
normale → SUCCEEDED. Frontend : le bouton n'apparaît qu'en `trameEnCours`,
appelle l'annulation du bon traitement, et le store affiche une fin neutre.

## P-051 · Confirmer le lancement d'un agent d'action

**Constat.** `ActionPanel.handleQuickLaunch` (`:474`) lance immédiatement un
agent sans paramètre (« Relance clients » part au premier clic) ; un agent
avec paramètres passe par la fiche et son bouton « Lancer ».

**Design.** Tout agent passe par la fiche : `handleQuickLaunch` sélectionne
l'agent dans tous les cas ; la fiche d'un agent sans paramètre montre sa
description, ce qu'il va faire, et le bouton « Lancer ». Un seul clic de
plus, aucun mécanisme nouveau, aucun `requestExternalAction` (fail-open).
Quand un agent aura un effet externe (envoi d'e-mails), la fiche portera la
confirmation d'écriture existante ; hors périmètre ici.

**Tests.** Cliquer un agent sans paramètre n'appelle pas `launchAction` et
affiche la fiche ; « Lancer » l'appelle ; un agent avec paramètres garde son
parcours ; `ActionPanel.*.test.tsx` restent verts.

## P-049 · Renseigner les variables d'un prompt

**Constat.** L'API et l'écran durable existent (`/api/variables`,
`Paramètres > VariablesSection`) ; le composeur affiche « inconnues :
{nom_client}… » et, depuis le cycle 4, « Compléter dans le message »
sélectionne le premier jeton. Il manque le geste qui remplit les jetons.

**Design.** Sous la puce des inconnues, « Renseigner les variables » ouvre un
petit formulaire inline (un champ par jeton inconnu, dans l'ordre d'apparition).
Deux boutons : « Remplacer dans le message » (substitution locale, une fois,
rien d'enregistré : par défaut, car `{nom_client}` est une donnée de contexte,
pas un réglage) et « Enregistrer comme variables » (appelle `createVariable`
pour chaque champ rempli, puis relance `previewVariables`). Échap ferme le
formulaire et rend le focus au composeur. Aucun envoi automatique.

**Tests.** Le formulaire liste exactement les inconnues ; « Remplacer » réécrit
le message et vide la liste des inconnues ; « Enregistrer » appelle l'API
une fois par variable et l'aperçu passe à « résolues » ; Échap ferme.

## P-048 · Créer et faire évoluer un livrable

**Constat.** `DeliverablesWorkspaceCanvas` liste, filtre et compte ; l'API
`createDeliverable` / `updateDeliverable` (`services/api/crm-extended.ts:142`)
n'a aucun appelant. Backend : `POST/PUT /api/crm/deliverables` existent
(champs `project_id`, `title`, `description`, `status` parmi `a_faire`,
`en_cours`, `en_revision`, `valide`, `due_date`).

**Design.** Un projet sélectionné : bouton « Ajouter un livrable » → formulaire
inline (titre obligatoire, échéance optionnelle, statut par défaut « À
faire ») → `createDeliverable`, puis rechargement de la liste et message de
succès dans le canevas. Sur chaque ligne, un sélecteur de statut (quatre
valeurs) → `updateDeliverable(id, { status })` ; « Validé » pose
`completed_at` côté serveur si la route le fait déjà (à lire), sinon on
n'invente rien. L'état vide dit « Aucun livrable : ajoute le premier » au lieu
de « pas encore possible » ; les filtres restent conditionnés à au moins un
livrable (B-635). Écriture interne, pas d'effet externe : même niveau de
confirmation que la création d'un contact (aucun dialogue supplémentaire).

**Tests.** Création : le bouton n'existe qu'avec un projet ; titre vide
refusé ; succès → ligne visible et compteur à jour ; erreur API → message,
formulaire conservé. Statut : le sélecteur appelle l'API avec le bon id ;
erreur → statut d'origine rétabli.

## P-045 · Dire que l'effort ne s'applique pas aux GPT-5 avec outils

**Constat.** `providers/openai.py:136` pose `reasoning_effort = "none"` dès
qu'un outil est fourni à un modèle GPT-5/o-series (l'API Chat Completions
refuse outils + raisonnement) ; THÉRÈSE fournit ses outils à chaque
message. Le sélecteur d'effort (`LLMTab.tsx:568`) ne le dit pas.

**Design.** Lecture retenue : la mention, pas la migration vers
`/v1/responses` (chantier lourd, hors de cette vague). Sous le sélecteur,
quand `selectedProvider === 'openai'` et que le modèle est de la famille
GPT-5/o-series (même prédicat que le backend, exposé par le catalogue ou
recopié avec un test de parité), un texte : « Avec ce modèle, l'effort choisi
ne s'applique pas aux conversations de THÉRÈSE : l'API d'OpenAI refuse le
raisonnement dès qu'un outil est fourni. Il s'applique aux générations sans
outil (trame, rédaction). » Rien ne change côté moteur.

**Tests.** La mention apparaît pour `openai` + `gpt-5.6-luna`, pas pour
`anthropic` ni pour `gpt-4.1` ; le prédicat frontend et le prédicat backend
(`_uses_max_completion_tokens`) donnent la même réponse sur une liste de
modèles témoins.

## Ordre proposé

P-045 (une mention), P-051 (une fiche), P-048 (deux appels API existants),
P-049 (un formulaire), P-056 (backend + frontend). Chaque sujet : test rouge,
correctif, sabotage, commit `P-0xx`, portes rapides ; vitest complet et CI
de `main` lue avant de passer au suivant lourd.

## V2 après la revue COCO (08/09/2026, 22 h 52, 63 fichiers relus)

Verdicts : P-056 NO-GO (9 findings), P-051, P-049, P-048, P-045 GO avec
réserves (16 findings). Tous relus dans le code : aucun faux. Ce que la V2
change, finding par finding (numéros de la revue).

**P-045.** (1) Deux phrases distinctes : « Dans THÉRÈSE, l'effort est
désactivé pour ce modèle dès qu'une conversation utilise des outils » et
« Sans outils, ce réglage n'est transmis qu'aux modèles pris en charge
(GPT-5.6) » ; pas de promesse sur 5.5/5.4. (2) « lorsqu'une conversation
utilise des outils », pas « toutes les conversations » ; `aria-describedby`
du sélecteur vers la mention. Prédicat frontend = préfixes `gpt-5`, `o1`,
`o3`, `o4`, test de parité avec `_uses_max_completion_tokens` sur des témoins.

**P-051.** (1) Les trois entrées passent par la fiche : `handleQuickLaunch`,
`ChatInput` (`{{action:…}}`) et `CommandExecutor` (catalogue chargé ou non) ;
un helper unique `ouvrirLaFicheAgent(agent)` dans le store. (2) L'erreur de
lancement s'affiche dans la fiche (`role="alert"`), paramètres conservés,
« Lancer » réessayable. (3) La fiche prend le focus sur son titre à
l'ouverture, « Retour » est nommé, le retour rend le focus à la carte.

**P-049.** (1) Pas de substitution dans le message brut (les directives
`[contact: …]` du message sont analysées avant la résolution des variables,
`chat.py:1505` puis `:1593` ; une valeur injectée deviendrait une commande).
Le geste « Remplacer dans le message » est ABANDONNÉ : le formulaire ne fait
qu'enregistrer des variables (`createVariable(nom, 'text', valeur)`) et le
message garde ses jetons, résolus au bon endroit par le moteur. (2) Chaque
aperçu est étiqueté par le texte et un compteur de requête ; une réponse
périmée est ignorée ; la confirmation de double-envoi se réarme quand
l'aperçu change. (3) Enregistrement par champ avec succès/erreur par ligne,
saisies refusées conservées, aucun remplacement automatique sur 409. (4)
Sans objet (plus de remplacement local). (5) Échap consommé dans le
formulaire (stopPropagation), focus rendu au composeur, champs labellisés,
raccourci existant conservé.

**P-048.** (1) Les mutations capturent `project.id` au départ et n'appellent
`refresh` que si le projet actif est encore le même. (2) Un seul changement
de statut en vol par livrable (sélecteur désactivé pendant l'écriture), la
ligne prend le DTO renvoyé par `updateDeliverable`. (3) Quitter `valide`
efface `completed_at` côté serveur ; revalider le redate ; test du cycle
complet. (4) Le retard se calcule par jour civil (`localDateKey`), tests
hier/aujourd'hui/demain. (5) Le backend valide titre non blanc et statut
parmi les quatre (422 sinon) ; un statut inconnu existant reste affiché tel
quel dans le sélecteur jusqu'à un choix volontaire. (6) Mentions « sans
modifier les données » et « Aucune validation » réécrites, test `etatVide`
mis à jour (filtres absents à vide conservés).

**P-056.** (1) Voie (a) : le client fournit `task_id` (UUID v4 validé,
optionnel pour les appels existants) ; `creer_traitement` accepte un id
fourni, collision → 409. `entity_id` entre dans le DTO. (2) Transitions
exactes : QUEUED → RUNNING (`demarrer`) → `terminer(DONE | FAILED |
CANCELLED)` par le producteur après son nettoyage réel ; `cancel_requested`
reste jusqu'à la clôture par le producteur. (3) La tâche porteuse couvre
TOUT le travail (LLM, analyse, relecture des sections, remplacement,
commit) ; point de non-retour = juste avant l'écriture : `annulation_demandee`
consulté, puis écriture sous `asyncio.shield` ; annulation après le commit =
DONE (la trame existe). (4) Deux générations simultanées du même document :
409 `outline_in_progress` (un traitement actif de ce type pour cet
`entity_id`) ; les sections sont RELUES dans la transaction d'écriture et le
remplacement n'a lieu que si elles sont toujours toutes vides, sinon 409
sans écriture. (5) La porteuse est détachée (référence forte conservée), la
route l'attend sous `asyncio.shield` : une déconnexion du client n'annule
pas le traitement, qui reste visible et annulable dans « Travaux » ; toute
exception (parseur, `RuntimeError` du LLM, SQL) → `terminer(FAILED, error)`
puis 502/500. (6) Pas de best-effort : registre indisponible → 503, aucun
appel LLM. (7) Réponse annulée = `JSONResponse` 409 `{code:
"outline_cancelled", message}` ; `ApiError` gagne un champ `code` (additif)
lu depuis `data.code`. (8) `documentStore.outlineGeneration = { documentId,
taskId, arretDemande }` remplace l'heuristique `isLoading && sections === 0` ;
réponse tardive ignorée si le document ouvert a changé. (9) Tests backend
sans HTTP concurrent : la porteuse est appelée directement avec un faux LLM
qui attend un événement, `demander_arret` pendant l'attente → CANCELLED et
zéro section ; les chemins simples (409 en cours, 503 registre, DONE) par la
route.

Ordre inchangé : P-045, P-051, P-048, P-049, P-056.
