# Cycle 20 : lot divers-ui

Exécution du 16 novembre 2026 dans l’arbre `gpt-c20-divers-ui`, branche
`gpt/c20-divers-ui`. Base constatée : `4dfc79d1568d123d7b517113a984b75baca84fc0`
(`v0.83.0-alpha-137-g4dfc79d1`). Les candidats ont été examinés dans l’ordre demandé.

Trois candidats confirmés, cinq rejetés, une règle à trancher. Aucun commit,
aucun `git add`, aucun push. Les tests et correctifs restent dans cet arbre.
Les rouges ci-dessous ont été exécutés avant leur correction respective.

## Verdicts et reproductions

Les chemins sont relatifs à la racine du dépôt. Pour Vitest, le nom après `::`
est celui du cas dans le fichier indiqué.

| ID | Verdict | Test (chemin::nom) | Rouge observé, en remplacement du commit du rouge | Commit du correctif |
| --- | --- | --- | --- | --- |
| B-1989 | `confirme` | `tests/test_invoice_pdf_francais.py::test_b1989_un_statut_inconnu_reste_en_francais_dans_le_pdf` | `AssertionError: assert 'Statut inconnu' in 'Document généré par THÉRÈSE - 16/11/2026\nPage 1\nFACTURE\nN° FACT-2026-324\nÉMETTEUR\nDESTINATAIRE\nÉmetteur de test...vrement : 40 €.\nEscompte pour paiement anticipé : néant.\nMentions légales : TVA incluse selon les taux en vigueur.\n'` ; 1 échec, 0 succès | non commité |
| B-1991 | `confirme` | `tests/test_b1991_fournisseur_agenda_inconnu.py::test_b1991_creer_sur_un_fournisseur_inconnu_explique_le_refus` | `AssertionError: assert 'account_id r...ogle Calendar' == 'Ce fournisse...is en charge.'` ; valeur reçue : `account_id requis pour Google Calendar` ; 1 échec, 0 succès | non commité |
| B-1995 | `confirme` | `src/frontend/src/components/calendar/CalendarPanel.da.test.tsx::B-1995 : le refus brut de Google est expliqué en français avec les données conservées` | `Error: expect(element).toHaveTextContent()` ; attendu : `L’API Google Calendar n’est pas activée.` ; reçu : `Google Calendar API has not been used in project 42 before or it is disabled.Données conservées.Réessayer` ; 1 échec, 0 succès, 28 cas exclus par le filtre | non commité |
| B-2000 | `rejete` | `src/frontend/src/components/board/BoardPanel.souverainOllamaCloud.b1172.test.tsx::seul un modèle Cloud installé : le mode souverain ne se déclare pas disponible` | Aucun rouge : le mode actif reste Cloud, déjà annoncé avant confirmation | sans changement |
| B-2001 | `rejete` | `src/frontend/src/components/settings/PrivacyTab.purgeIndisponible.b1209.test.tsx::« Enregistrer » n’envoie pas des valeurs par défaut non lues` et `::B-1230 : les commandes de purge sont grisées et la raison est dite` | Aucun rouge : valeurs signalées comme défauts, commandes désactivées, aucun envoi | sans changement |
| B-2004 | `rejete` | `src/frontend/src/components/settings/ToolsPanel.confirmationRisque.p106.test.tsx::risque medium : le clic installe directement` | Aucun rouge : comportement explicitement fixé pour le risque moyen | sans changement |
| B-2005 | `rejete` | `src/frontend/src/components/invoices/InvoicesPanel.debordement.p162.test.tsx::retire indice et arrêt clavier quand le filtre ne contient aucune pièce` | Aucun rouge : pas de tableau à faire défiler ; les actions restent accessibles | sans changement |
| B-2007 | `rejete` | `src/frontend/src/components/chat/ChatInput.modeles.c18m1.test.tsx::Mistral Large 4 se voit en préversion, et le réglage d’effort n’est pas appliqué` | Aucun rouge : le libellé suit l’effort effectivement transmis par le moteur | sans changement |
| B-2028 | `regle_a_trancher` | `src/frontend/src/components/onboarding/SecurityStep.deplieVisible.b1344.test.tsx::déplier le dernier risque l’amène sous les yeux` ; critère en discussion dans `tests/rendering/c22a.spec.ts:35` | Aucun rouge : pas de preuve d’un contenu effectivement masqué par ce pixel de tolérance | sans changement |

### B-1989 : repli du statut dans le PDF

Le nouveau test génère un vrai PDF dans `tmp_path`, puis en extrait le texte.
Le rouge porte sur l’absence de « Statut inconnu », avec le repli anglais en place.
Le correctif conserve les libellés connus et « Non renseigné » pour une valeur
vide ; une valeur non vide inconnue devient « Statut inconnu ».

Chemin de production vérifié avant correction : la route
`src/backend/app/routers/invoices.py:1364` appelle `InvoicePDFGenerator.generate_invoice_pdf` ;
le générateur appelle `libelle_statut_pdf` dans `src/backend/app/services/invoice_pdf.py:478`.
Le fichier corrigé est donc celui qui produit la facture servie par l’application.

L’ancienne assertion de `test_les_statuts_sont_traduits_et_accordes`, ligne 37,
imposait précisément « Custom status ». Elle a été remplacée par une égalité
exacte avec « Statut inconnu », sans retirer de cas ni assouplir l’assertion.
Le nouveau test contrôle également l’absence du libellé anglais dans le PDF.

Preuve rouge : `/tmp/divers-ui-b1989-rouge.xml`. Retour au vert : 5 tests réussis,
0 échec, 0 erreur, 0 ignoré dans `/tmp/divers-ui-b1989-vert.xml`.

### B-1991 : création d’un événement chez un fournisseur inconnu

Le nouveau test passe par `POST /api/calendar/events`, avec un agenda jetable
dont le fournisseur vaut `inconnu`. Avant correction : HTTP 400 avec une demande
de compte Google. Après correction : HTTP 400 et « Ce fournisseur d’agenda
n’est pas pris en charge. » Le fournisseur inconnu est refusé avant la branche Google.

Chemin de production vérifié avant correction : le routeur est inclus dans
`src/backend/app/main.py:1046` ; `create_event` est enregistré sur `POST /events`
dans `src/backend/app/routers/calendar.py:1192`. Le test exerce cette route.

Le commentaire périmé dans `tests/test_regression_facturation_agenda.py` a été
mis à jour ; ses assertions existantes n’ont pas été modifiées.

Preuve rouge : `/tmp/divers-ui-b1991-rouge.xml`. Retour au vert : 15 tests réussis,
0 échec, 0 erreur, 0 ignoré dans `/tmp/divers-ui-b1991-vert.xml`.

### B-1995 : explication française du refus Google Calendar

Le nouveau test monte `CalendarPanel`, simule le message brut cité et un échec
de lecture des événements, puis vérifie le bandeau affiché. Le correctif traduit
ce message identifié en conseil français. Les messages français déjà fournis par
le serveur conservent leur traitement. Le bandeau garde les données conservées,
le bouton Réessayer et l’absence de demande de reconnexion trompeuse.

Chemin de production vérifié avant correction :
`src/frontend/src/components/prototype/PrototypeUnifiedViewCanvas.tsx:95` rend
`CalendarPanel` ; `CalendarPanel.tsx:203`, `:257` et `:283` appellent
`classifyCalendarError`. Le correctif est dans cette fonction réellement utilisée.

Trois tests existants attendaient encore le texte anglais :
`CalendarPanel.da.test.tsx`, `CalendarPanel.cycle6.test.tsx` et
`CalendarPanel.grok0700.test.tsx`. Leurs attentes portent désormais sur la même
explication en français. La persistance après une lecture locale et la disparition
après un succès Google restent vérifiées. Le dernier test vérifie aussi l’absence
de tout bandeau d’alerte, pour éviter une assertion d’absence devenue triviale.

Preuve rouge : `/tmp/divers-ui-b1995-rouge.json`. Retour au vert : 42 tests réussis,
0 échec, 0 ignoré dans `/tmp/divers-ui-b1995-vert.json`.

## Motifs des rejets

- **B-2000** : `BoardPanel.tsx:120` initialise Cloud ; `ModeSelector.tsx:30` et `:56`
  annoncent le mode actif par `aria-pressed`. Le clic sur Souverain désactivé ne
  sélectionne pas ce mode. `BoardPanel.tsx:255-265` exige le consentement cloud
  et refuse de lancer un mode souverain devenu indisponible. La confirmation
  décrit le mode et le transfert avant le lancement (`:676-685`). La règle de
  désactivation est écrite dans `docs/stories/US-400-board-skills.md:115`.
  Vérification : 11 tests réussis dans les deux fichiers Board sélectionnés.
- **B-2001** : `PrivacyTab.tsx:632` dit explicitement que les valeurs affichées
  sont des défauts, pas la configuration réelle. Les lignes `:650`, `:673` et
  `:704` désactivent les trois commandes ; `:227` bloque aussi le gestionnaire
  d’enregistrement. La raison et le geste de rechargement restent visibles.
  Le commentaire du test décrit le défaut historique corrigé, pas un danger
  encore actif. Vérification : 8 tests réussis dans les deux fichiers PrivacyTab.
- **B-2004** : Filesystem est classé `medium` dans
  `src/backend/app/routers/mcp.py:315`. `ToolsPanel.tsx:413-420` applique la règle
  P-106 aux risques élevés. Cette portée est aussi annoncée dans
  `docs/releases/v0.81.0-alpha.md:10`, et le test P-106 ligne 87 exige
  explicitement l’installation directe des niveaux faible et moyen.
  L’avertissement Filesystem est affiché avant le clic et associé au bouton.
  Vérification : 11 tests réussis, sans installation réelle de connecteur.
- **B-2005** : `InvoicesPanel.tsx:273` réserve le cadre actif à un tableau chargé
  et non vide ; `:620` ne retire que l’arrêt Tab de ce cadre. L’état de chargement
  garde `role="status"` (`:413`) ; les erreurs et filtres vides ont des boutons
  Réessayer ou Réinitialiser (`:427`, `:460`). Le test vérifie le retour de
  l’indice après rechargement, le cadre focalisable avec des lignes et la
  préservation du focus. Vérification : 18 tests réussis.
- **B-2007** : `ChatInput.tsx:135-147` affiche l’effort résolu et annonce
  explicitement quand le réglage n’est pas appliqué. Le catalogue interne
  `src/backend/app/services/modeles_catalogue.py:255-261` ne définit pas d’effort
  pour cet identifiant, ce que couvre aussi
  `tests/test_c18_m1_modeles.py::test_mistral_large_4_n_envoie_pas_deffort`.
  Le commentaire d’en-tête du test frontend est périmé ; il ne justifie pas
  de faire annoncer un effort non envoyé. Vérification : 2 tests frontend réussis.
  Aucune capacité actuelle du fournisseur n’a été vérifiée en ligne.

## Règle à trancher : B-2028

**Question :** « Entièrement visible » impose-t-il zéro dépassement géométrique
du bouton de risque, ou aucun texte masqué avec une tolérance d’un pixel sur
son enveloppe ? Le test Playwright fixe un seuil numérique de 1 pixel, mais
ni son nom ni `docs/rapport-c22a-premier-usage.md:73-75` ne précisent la distinction
entre texte, espacement et bordure. Cette différence ne prouve pas un défaut
d’accessibilité à l’exécution.

Options :

1. Exiger `débordement <= 0` pour tout le bouton, bordure comprise.
2. Garder jusqu’à 1 pixel sur l’enveloppe pour la mesure, tout en exigeant
   qu’aucun texte utile ne soit masqué, avec des critères séparés.

**Recommandation : option 2**, documentée explicitement. Le critère doit porter
sur ce que l’utilisateur doit lire, sans faire d’un arrondi du cadre une perte
de contenu. Cette recommandation n’a pas été implémentée.

`SecurityStep.tsx:161-167` redemande déjà le défilement à la fin de l’animation,
seulement si le risque reste ouvert. Les 2 tests unitaires existants passent.
Ils ne mesurent pas le pixel dans un moteur de rendu. Le scénario Playwright
n’a pas été relancé ; aucune preuve de dépassement réel n’est revendiquée.

## Portes finales

| Porte | Périmètre | Réussis | Échoués / erreurs | Ignorés | Noms des échecs |
| --- | --- | ---: | ---: | ---: | --- |
| Pytest | 14 fichiers voisins et nouveaux tests | 122 | 0 / 0 | 0 | aucun |
| Ruff | `src/backend tests`, sans correction automatique | contrôle réussi | 0 diagnostic | sans objet | aucun |
| Vitest | 18 fichiers ciblés, 3 workers maximum | 104 | 0 | 0 | aucun |
| TypeScript | `npx tsc --noEmit` | contrôle réussi | 0 diagnostic | sans objet | aucun |
| ESLint | `npm run lint` | contrôle réussi | 0 erreur, 27 avertissements | sans objet | aucun |

Le XML `/tmp/divers-ui-pytest.xml` et le JSON `/tmp/divers-ui-vitest.json` ont été
lus après terminaison, indépendamment de la sortie console tronquée.
ESLint termine avec le code 0 : 20 avertissements `react-hooks/exhaustive-deps`
et 7 `react-refresh/only-export-components`, tous dans des fichiers non modifiés
par ce lot. Le seuil existant de 27 avertissements n’a pas été changé.
`git diff --check` ne signale aucune erreur d’espacement.

Commande backend :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_invoice_pdf_francais.py \
  tests/test_b1991_fournisseur_agenda_inconnu.py \
  tests/test_regression_facturation_agenda.py \
  tests/test_routers_calendar.py \
  tests/test_frontiere_facturation_agenda.py \
  tests/test_c22b_caldav_ecriture.py \
  tests/test_calendar_allday_semantics.py \
  tests/test_google_calendar_civil_time.py \
  tests/test_conditions_de_paiement_pdf.py \
  tests/test_lot15_pdf_montants.py \
  tests/test_b1357_mentions_pdf.py \
  tests/test_c22b_identite_facture.py \
  tests/test_facture_pdf_ouverture.py \
  tests/test_b1615_numero_a_lemission.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/divers-ui-pytest.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Commande frontend, depuis `src/frontend` :

```sh
npx vitest run \
  src/components/calendar/CalendarPanel.da.test.tsx \
  src/components/calendar/CalendarPanel.cycle6.test.tsx \
  src/components/calendar/CalendarPanel.grok0700.test.tsx \
  src/components/calendar/CalendarPanel.nomsAccessibles.test.tsx \
  src/components/calendar/CalendarPanel.plageAffichee.b1429.test.tsx \
  src/components/calendar/CalendarPanel.reconnexion.test.tsx \
  src/components/calendar/CalendarPanel.retourGrille.test.tsx \
  src/components/calendar/CalendarPanel.reconciliationAvantEvenements.test.tsx \
  src/components/calendar/calendarErrors.test.ts \
  src/components/board/BoardPanel.souverainOllamaCloud.b1172.test.tsx \
  src/components/board/BoardPanel.souverainParDefaut.test.tsx \
  src/components/settings/PrivacyTab.purgeIndisponible.b1209.test.tsx \
  src/components/settings/PrivacyTab.test.tsx \
  src/components/settings/ToolsPanel.avertissementRisque.b1193.test.tsx \
  src/components/settings/ToolsPanel.confirmationRisque.p106.test.tsx \
  src/components/invoices/InvoicesPanel.debordement.p162.test.tsx \
  src/components/chat/ChatInput.modeles.c18m1.test.tsx \
  src/components/onboarding/SecurityStep.deplieVisible.b1344.test.tsx \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=dot --reporter=json --outputFile=/tmp/divers-ui-vitest.json
npx tsc --noEmit
npm run lint
```

Le premier lancement Vitest a échoué **avant toute collecte**, car Vite tentait
d’écrire sa configuration compilée dans le `node_modules` partagé :
`Error: EPERM: operation not permitted, open '…/node_modules/.vite-temp/…'`.
Ce n’est pas un rouge de candidat. `--configLoader runner --no-cache` a permis
les exécutions suivantes sans modifier la configuration ni le lien de dépendances.

La console Vitest signale des limites jsdom déjà présentes (`scrollTo`, navigation)
et des avertissements React `act(...)`. Aucun échec ni test ignoré dans la porte
finale. Aucune suite complète lancée, aucun fournisseur LLM ni service en ligne
appelé, aucun serveur applicatif ouvert sur les ports réservés. Les données des
tests backend sont jetables ; aucun travail effectué dans `~/.therese` ou `.app-loop/`.

## Remédiation de la relecture, passe 1

Reprise du commit `55b877d4` dans le même arbre, initialement propre.
Cette section complète les preuves historiques ci-dessus et remplace le verdict
initial de B-1995. Les modifications de cette passe restent non indexées et non
commitées. Aucun autre constat n'a été traité.

### 1. P1 : conserver le statut historique dans le PDF

Constat confirmé. Le repli devient « Statut inconnu : valeur enregistrée »,
avec la casse et les accents d'origine. Le bloc d'informations échappe cette
valeur avant de la transmettre à ReportLab : les chevrons et l'esperluette ne
doivent ni disparaître ni devenir des balises. Les traductions connues et
« Non renseigné » restent inchangées.

Test ajouté avant correction :
`tests/test_invoice_pdf_francais.py::test_relecture_r1_le_pdf_conserve_le_statut_historique`.
Ses six cas génèrent un PDF et en extraient le texte : `partiellement_paye`,
`converted` sur facture, `refused`, `accepted` et `expired` sur avoir,
puis « À vérifier <paiement> & reçu ». Le statut source doit aussi rester intact.
Le test unitaire existant conserve une égalité exacte pour le repli et vérifie
désormais également la normalisation d'un statut connu et une valeur vide.

Rouge exécuté seul, avant modification de la production : 6 échecs, aucune erreur
ni exclusion, dans `/tmp/divers-ui-r1-c1-rouge.xml`, relu. Ligne d'échec :

```text
AssertionError: assert 'Statut inconnu : partiellement_paye' in 'Document généré par THÉRÈSE - 16/11/2026\nPage 1\nFACTURE\nN° FACT-2026-324\nÉMETTEUR\nDESTINATAIRE\nÉmetteur de test...vrement : 40 €.\nEscompte pour paiement anticipé : néant.\nMentions légales : TVA incluse selon les taux en vigueur.\n'
```

Après correction, les six fichiers voisins PDF ont donné 34 succès, aucun échec,
erreur ou test ignoré (`/tmp/divers-ui-r1-c1-vert.xml`, relu).
Appelants relus : route PDF `invoices.py:1364`, générateur et bloc d'informations
`invoice_pdf.py:478`. Les règles métier de statut ne changent pas.

### 2. P1 : résoudre l'alias Google implicite malgré une collision

Constat confirmé. Dans le seul cas de collision avec un fournisseur inconnu,
`request.model_fields_set` distingue le champ omis de la sélection explicite.
Avec un compte et un alias implicite, `_resoudre_primary_google` demande l'identifiant
réel du calendrier principal dans ce compte, puis la création utilise cet identifiant.
Une destination déjà enregistrée doit être Google et appartenir au même compte ;
sinon la route répond 409 avant toute création. La ligne inconnue n'est ni convertie
ni utilisée pour rattacher l'événement. Une sélection explicite reste refusée en 400.

Le test `tests/test_b1991_fournisseur_agenda_inconnu.py::test_relecture_r1_primary_implicite_resout_le_compte_sans_detourner_la_ligne`
a d'abord échoué seul, avant correction : 1 échec, aucune erreur ni exclusion
(`/tmp/divers-ui-r1-c2-rouge.xml`, relu). Lignes d'échec :

```text
AssertionError: {"code":"HTTP_ERROR","message":"Ce fournisseur d’agenda n’est pas pris en charge."}
assert 400 == 200
 +  where 400 = <Response [400 Bad Request]>.status_code
```

Il couvre maintenant la destination absente ou déjà en cache. Deux tests paramétrés
voisins couvrent la sélection explicite avec ou sans compte, puis une résolution
qui entrerait en conflit avec la ligne inconnue ou le calendrier d'un autre compte.
Les six nouveaux cas contrôlent les écritures réelles en base jetable et les appels
du transport simulé ; le test B-1991 initial reste intact.

Après correction, 69 tests voisins de routage, CalDAV, Google, journées entières
et frontières d'agenda sont passés sans échec, erreur ni exclusion
(`/tmp/divers-ui-r1-c2-voisins.xml`, relu). Les sept tests du fichier B-1991
sont inclus dans la porte finale.
Appelants relus : client `services/api/calendar.ts`, `EventForm.tsx`,
`usePrototypeMeetingData.ts` et `_create_event_google`. Les deux formulaires
transmettent un calendrier explicite ; le comportement local et CalDAV est conservé.

### 3. P2 : vérifier le contrat HTTP réel de B-1995

Constat de couverture confirmé. **B-1995 est requalifié `rejete` pour le parcours
403 examiné** : le message anglais simulé ne démontre pas un défaut de production.
`calendar.py:342` traduit déjà le refus ; les lectures d'agendas et d'événements
l'appellent aux lignes 429 et 1094, et la synchronisation propage ce refus.
Aucun chemin transmettant le message brut au panneau n'a été établi dans ces
trois parcours. La branche de traduction anglaise ajoutée à `calendarErrors.ts`
est donc retirée ; le traitement du message français reste en place.

Le nouveau test paramétré
`tests/test_b1995_contrat_erreur_google.py::test_relecture_r1_le_403_du_routeur_correspond_a_la_reponse_du_panneau`
exerce les trois routes réelles avec un refus Google brut dans `httpx.MockTransport`.
Il compare leur réponse à la même fixture JSON que le panneau et vérifie la
préservation d'un événement en base. Avec l'ancienne simulation anglaise dans
la fixture, son premier lancement isolé donne 3 échecs, aucune erreur ni exclusion
(`/tmp/divers-ui-r1-c3-rouge.xml`, relu). Ligne d'échec :

```text
assert {'body': {'co...'status': 403} == {'body': {'co...'status': 403}
```

Le détail du diff oppose le message français renvoyé par le routeur à
`Google Calendar API has not been used in project 42 before or it is disabled.`
La fixture a été corrigée selon la réponse observée. Le test B-1995 du panneau,
étendu pour exiger ce contrat mais gardant encore son ancienne injection anglaise,
a ensuite échoué seul : 1 échec, 28 cas hors filtre, aucun succès
(`/tmp/divers-ui-r1-c3-ui-rouge.json` et journal correspondant, relus).
Ligne d'échec : `Error: expect(element).toHaveTextContent()`.
Attendu : le conseil complet commençant par « Google refuse l'accès au calendrier
(403). » ; reçu : « L’API Google Calendar n’est pas activée. Active-la dans ta
console Google Cloud, puis relance la synchronisation.Données conservées.Réessayer ».

Le test utilise maintenant le vrai client HTTP frontend avec une réponse `fetch`
simulée par la fixture vérifiée côté serveur. Deux cas supplémentaires couvrent
les événements et la synchronisation. Le cache conservé, le conseil complet,
le bouton Réessayer et l'absence de reconnexion trompeuse restent vérifiés.
Les tests Cycle 6 et Grok montrent d'abord le bandeau, puis libèrent explicitement
la réponse des événements : le succès local le conserve, le succès Google l'efface.
Les appelants `loadCalendars`, `loadEvents`, la synchronisation de `CalendarPanel`
et le décodage du client HTTP ont été relus.

Ces rouges prouvent l'écart de simulation, pas une régression du serveur.
Rejouer les tests corrigés en annulant seulement le retrait de la branche
frontend ne les fera pas rougir : pour reproduire ce constat, il faut remettre
l'ancienne réponse anglaise simulée. Aucune nouvelle correction serveur de
traduction n'est revendiquée.

### Portes de la passe 1

| Porte | Périmètre | Réussis | Échecs / erreurs | Ignorés |
| --- | --- | ---: | ---: | ---: |
| Pytest | 17 fichiers ciblés et voisins | 141 | 0 / 0 | 0 |
| Vitest | 6 fichiers agenda | 46 | 0 / 0 | 0 |
| Ruff | `src/backend tests`, sans correction automatique | contrôle réussi | 0 diagnostic | sans objet |
| TypeScript | `tsc --noEmit` | contrôle réussi | 0 diagnostic | sans objet |
| ESLint | `npm run lint` | contrôle réussi | 0 erreur, 27 avertissements | sans objet |

Le XML `/tmp/divers-ui-r1.xml` et le JSON `/tmp/divers-ui-r1-vitest.json`
ont été lus après terminaison. ESLint termine avec le code 0 ; ses avertissements
portent sur des fichiers non modifiés. Aucun test existant n'a été affaibli.
`git diff --check` est propre. Aucun des rouges connus exclus par le mandat
n'entre dans ces comptes.

Commande backend, depuis la racine :

```sh
PYTHONDONTWRITEBYTECODE=1 THERESE_DATA_DIR=$(mktemp -d /tmp/divers-ui-r1-data-XXXXXX) \
  OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_invoice_pdf_francais.py \
  tests/test_b1991_fournisseur_agenda_inconnu.py \
  tests/test_b1995_contrat_erreur_google.py \
  tests/test_regression_facturation_agenda.py \
  tests/test_routers_calendar.py \
  tests/test_frontiere_facturation_agenda.py \
  tests/test_c22b_caldav_ecriture.py \
  tests/test_calendar_allday_semantics.py \
  tests/test_google_calendar_civil_time.py \
  tests/test_pluriel_agenda_google.py \
  tests/test_conditions_de_paiement_pdf.py \
  tests/test_lot15_pdf_montants.py \
  tests/test_b1357_mentions_pdf.py \
  tests/test_c19d_b1077.py \
  tests/test_c22b_identite_facture.py \
  tests/test_facture_pdf_ouverture.py \
  tests/test_b1615_numero_a_lemission.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/divers-ui-r1.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Commande frontend, depuis `src/frontend` :

```sh
VITE_THERESE_BACKEND_PORT=9 npm_config_offline=true npx --no-install vitest run \
  src/components/calendar/CalendarPanel.da.test.tsx \
  src/components/calendar/CalendarPanel.cycle6.test.tsx \
  src/components/calendar/CalendarPanel.grok0700.test.tsx \
  src/components/calendar/calendarErrors.test.ts \
  src/components/calendar/CalendarPanel.reconnexion.test.tsx \
  src/components/calendar/CalendarPanel.reconciliationAvantEvenements.test.tsx \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=dot --reporter=json --outputFile=/tmp/divers-ui-r1-vitest.json
npm_config_offline=true npx --no-install tsc --noEmit
npm run lint
```

Les options Vitest évitent toute écriture de configuration dans les dépendances
partagées. Aucun serveur applicatif, appel réseau ou fournisseur LLM, aucune suite
complète, aucun accès à `~/.therese` ou `.app-loop/`. Les données sont jetables ;
les seuls livrables sont les changements de cet arbre et les rapports sous `/tmp`.


## Remédiation de la relecture, passe 2

Reprise du 17 novembre 2026, dans le même arbre `gpt-c20-divers-ui`, depuis
`41559324`. Les neuf défauts de code sont confirmés. Chaque reproduction ci-dessous
a été écrite ou récupérée, puis exécutée seule avant le correctif correspondant.
Les fichiers de tests voisins ont ensuite été exécutés, après relecture des
appelants. Aucun test existant n'a été supprimé ou rendu moins exigeant.

### État de l'intégration et portée du constat 3

Contrairement à l'état annoncé dans la demande, `git rev-list --left-right --count
HEAD...c20/integration` rendait **4 / 4** au début de cette passe. Le sommet
initial de l'intégration était `75498edd`. Les seuls éléments non suivis au départ
étaient les liens de dépendances `.venv` et `src/frontend/node_modules`.

La consigne « NE COMMITE PAS, pas de git add » et l'accès en lecture seule aux
métadonnées Git ont été respectés : **aucun rebase de l'historique n'a été effectué**.
Les corrections et tests du lot migrations ont été repris dans les fichiers de
travail, sans indexation. Une comparaison binaire des **24 fichiers** de
`HEAD...75498edd` avec cette référence ne trouve aucune différence après reprise.
Cela inclut les **treize fichiers de tests manquants** et le bilan
`docs/qualite/c20-migrations.md`, conservé tel quel. Les correctifs antérieurs du
lot divers-ui sont conservés.

Pour conserver tout le lot demandé au constat 3, les tests B-1893 (provenance
absente) et B-2011 (conseil correspondant au fournisseur) ont également été repris
et exécutés au rouge avant leurs correctifs d'intégration. Il ne s'agit pas de
nouveaux candidats. La branche `c20/integration` a avancé pendant le travail avec
le lot rust-windows ; cette passe reste fondée sur sa référence initiale, sans
importer ces modifications supplémentaires. L'orchestrateur devra traiter la
position de la branche lors de l'intégration des changements non commités.

### Reproductions avant correction

Les noms de fichiers sont relatifs à la racine ; les chemins frontend commencent
par `src/frontend/`. Les lignes d'échec sont recopiées des rapports, sans les
adresses mémoire ni les piles d'appels.

| Constat | Test ajouté, étendu ou récupéré | Ligne d'échec observée avant correction | Rapport du rouge |
| --- | --- | --- | --- |
| 1 | `tests/test_b1991_fournisseur_agenda_inconnu.py::test_relecture_r1_primary_implicite_resout_le_compte_sans_detourner_la_ligne`, étendu jusqu'aux trois relectures, avec et sans cache | `AssertionError: assert [] == ['evenement-r1']` ; 2 échecs | `/tmp/divers-ui-r2-c1-rouge-final.xml` |
| 2 | Même fichier, `test_relecture_r2_primary_explicite_google_cree_et_relit` ; `test_relecture_r2_un_agenda_selectionne_absent_ne_devient_pas_un_alias` | `E       assert 400 == 200` ; `E       assert 500 == 404` ; un échec par lancement isolé | `/tmp/divers-ui-r2-c2-rouge.xml`, `/tmp/divers-ui-r2-c2-absent-rouge.xml` |
| 3 | `tests/test_c20_b1889_notes_heritees.py::test_note_rattachee_preservee_si_evenement_sans_projet` | `AssertionError: assert None == 'projet-existant'` ; 1 échec | `/tmp/divers-ui-r2-c3-rouge.xml` |
| 4 | `tests/test_c20_b1890_activites_sans_contact.py::test_migration_ajoute_contact_absent_sans_perte`, schémas standard et enrichi | `KeyError: 'contact_id'` ; 2 échecs | `/tmp/divers-ui-r2-c4-rouge.xml` |
| 5 | `src/frontend/src/components/invoices/InvoiceForm.abandonPaiement.b2014.test.tsx` et `InvoiceForm.focusAbandon.b2014.test.tsx` | `Error: expect(element).not.toBeInTheDocument()` : « Marquer comme payée » reste présent ; `Error: expect(element).toHaveFocus()` pour Tab et Maj+Tab ; 3 échecs dans deux lancements isolés | `/tmp/divers-ui-r2-c5-paiement-rouge.json`, `/tmp/divers-ui-r2-c5-focus-rouge.json` |
| 6 | `tests/test_c20_b2010_limite_cle.py::test_limite_ne_presente_pas_la_cle_comme_acceptee` | `AssertionError: assert 'acceptée' not in 'Clé accepté...de requêtes.'` ; 1 échec | `/tmp/divers-ui-r2-c6-rouge.xml` |
| 7 | `src/frontend/src/components/atelier/AgentSession.refusHttp.b2013.test.tsx`, `AgentSession.refusDestination.b2013.test.tsx`, `AgentSession.profilChange.b2012.test.tsx`, et attente d'intégration de `AgentSession.accordMoteur.test.tsx` | `Error: expect(element).toHaveTextContent()` ; reçu : « La mission n’a pas démarré : tes accords ou la destination ne peuvent pas être vérifiés. Vérifie la connexion au moteur, puis réessaie. » ; 5 échecs et 6 succès dans quatre lancements isolés | `/tmp/divers-ui-r2-c7-http-rouge.json`, `-c7-destination-rouge.json`, `-c7-profil-rouge.json`, `-c7-accord-rouge.json` |
| 8 | `tests/test_c20_b2009_motifs_ambigus.py::test_refus_ambigu_sans_attribution_inexacte`, deux expressions | `AssertionError: assert 'opinion politique' not in 'Cette donné...n politique.'` ; `AssertionError: assert 'appartenance syndicale' not in 'Cette donné...e syndicale.'` ; 2 échecs | `/tmp/divers-ui-r2-c8-rouge.xml` |
| 9 | `tests/test_c20_b1888_transaction_activites.py::test_reconstruction_preserve_la_transaction_appelante` et `tests/test_c20_b1891_reparation_transaction.py::test_reparation_preserve_la_transaction_appelante` | `AssertionError: La transaction de l’appelant a été validée.` ; `AssertionError: La réparation a validé la transaction de l’appelant.` ; un échec par lancement isolé | `/tmp/divers-ui-r2-c9-reconstruction-rouge.xml`, `/tmp/divers-ui-r2-c9-reparation-rouge.xml` |

Reproductions complémentaires, elles aussi exécutées seules avant correction :

- Constat 2 : `EventForm.test.tsx::distingue une sélection inconnue nommée primary
  de l’alias Google` et `usePrototypeMeetingData.test.tsx::désigne la ligne
  sélectionnée même si son identifiant vaut primary` échouent chacun sur
  `AssertionError: expected "vi.fn()" to be called with arguments:` ; le champ
  attendu `calendar_id_is_stored: true` manque à l'appel réel. Rapports
  `/tmp/divers-ui-r2-c2-form-rouge.json` et
  `/tmp/divers-ui-r2-c2-hook-rouge.json`.
- Constat 3, conservation de B-1893 : les deux cas de
  `tests/test_c20_b1893_provenance_sans_marque.py` échouent sur
  `AssertionError: assert 'sans_document' == 'documents'`.
  Rapport `/tmp/divers-ui-r2-c3-provenance-rouge.xml`.
- Constat 3, conservation de B-2011 :
  `tests/test_c20_b2011_cle_sans_espace.py` échoue sur
  `assert 'OpenAI' in "Ta clé Claude n'est rattachée à aucun espace de travail. Dans la Console Claude, crée une clé rattachée à un espace (par exemple « Default Workspace »)."`.
  Rapport `/tmp/divers-ui-r2-c3-espace-rouge.xml`.
- Constat 5 : `InvoiceForm.soumission.test.tsx::bloque la création pendant
  l’abandon puis reprend la même saisie` échoue sur
  `AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times`.
  Une facture valide est déjà créée malgré la question d'abandon.
  Rapport `/tmp/divers-ui-r2-c5-creation-rouge.json`.

### Correctifs et vérification des appelants

**1 et 2 — Agendas.** La lecture de l'alias en collision appelle le même résolveur
Google que la création, dans le compte demandé, avant de comparer les identifiants
d'événement. Le test de création initial vérifie maintenant la relecture sans
`calendar_id`, avec `primary`, puis avec l'identifiant réel : un seul événement
persiste, et les deux agendas préexistants gardent leur propriétaire et leur
contenu. Le refus d'une collision avec un autre agenda réel est conservé.

Le nouveau champ optionnel `calendar_id_is_stored` distingue la sélection d'une
ligne SQL de l'alias historique. Sans cet indicateur, l'alias explicite reste
compatible. Avec `true`, la ligne inconnue est refusée et une sélection disparue
rend 404 avant tout appel distant. `EventForm` et `usePrototypeMeetingData`, les
deux appelants de création de l'interface, transmettent cet indicateur. Le contrat
TypeScript et le modèle Pydantic portent le même champ. L'ancien test de refus
explicite précise désormais cette sélection ; toutes ses assertions de refus,
d'absence d'appel fournisseur et d'absence d'événement sont conservées. Les
attentes frontend existantes sont renforcées par la présence du nouvel indicateur.

**3 — Notes et conservation de l'intégration.** La requête de rattachement exige
un dossier non nul sur le rendez-vous. Elle conserve ainsi le dossier de la note
et ne pose pas la marque définitive avant de pouvoir la rattacher. Le test vérifie
également le rattachement lors d'un passage ultérieur. L'appel au démarrage dans
`models/database.py` et les chemins de notes CRM ont été relus. Les deux autres
correctifs du lot repris conservent une provenance documentaire prudente sans
marque fiable et nomment le fournisseur réel dans le conseil de rattachement de
clé. Leurs appelants dans `routers/chat.py` et `routers/config.py` ont été relus.

**4 et 9 — Activités.** Les deux accès à `contact_id` tolèrent une colonne absente,
y compris dans le DDL enrichi. La reconstruction et la réparation des liens sont
différées lorsqu'une transaction appelante est ouverte ; aucun commit préalable
ne la valide. Les tests contrôlent le rollback, le schéma, les données et les
clés étrangères. L'appel au démarrage a été relu après les changements.
Les fichiers SQLite/SQLCipher voisins couvrent également les colonnes calculées,
index, contraintes, bases déjà migrées et réparations sans verrou inutile.

**5 — Factures.** Les groupes d'actions sont masqués pendant la question d'abandon
et `handleSubmit` refuse toute soumission. Le focus va vers « Continuer la saisie »
puis revient à « Annuler » à la reprise. Le piège de focus ignore les descendants
masqués, conformément au correctif d'intégration. Les tests couvrent la création,
la mise à jour, le paiement, Tab, Maj+Tab et une reprise conservant les valeurs.
Le test de disposition du pied reprend la saisie avant d'inspecter les actions :
ses assertions de disposition sont intégralement conservées. Les gestionnaires
de soumission, de fermeture et les deux usages du piège de focus ont été relus.

**6 — Vérification de clé.** L'état `limite` reste distinct ; son message explique
que la vérification est impossible pour le moment et propose de réessayer. Une
réponse 429 ne suffit plus à annoncer une clé acceptée. La route qui compose la
réponse affichée utilise bien cette fonction.

**7 — Agents.** Les deux étapes de vérification affichent le motif métier des
refus HTTP 4xx et d'`AccordNonEnregistre`, ainsi que le geste utile après changement
de profil. Le conseil de connexion reste réservé aux erreurs de transport ou
aux erreurs indéterminées. Les tests de transport continuent de passer et aucune
mission n'est lancée après un refus. Les callbacks du dialogue et
`getAgentConsent` ont été relus. L'attente du test `accordMoteur` est restaurée
exactement comme dans l'intégration, sans retirer son contrôle d'absence de mission.

**8 — Mémoire.** Le refus prudent reste actif pour les deux expressions ambiguës,
mais le message n'attribue plus une opinion politique ou une appartenance syndicale.
Le traitement couvre aussi les listes et dictionnaires utilisés par les appelants.
Les écritures et validations de fiches dans `memory_cards.py` ont été relues ;
les tests existants de protection et de non-divulgation restent exigés.

### Conditions d'exécution des portes

Aucun réseau, serveur applicatif, fournisseur LLM réel, accès à `~/.therese` ou
`.app-loop/`, commande `rm`, dépôt annexe, bundle, `git add` ou commit. Les échanges
Google et les transports utilisés par les tests sont simulés en mémoire. Toutes
les bases sont jetables sous `/tmp`. Aucune suite complète n'a été lancée.

Deux particularités du bac à sable ont demandé des auxiliaires **uniquement
sous `/tmp/divers-ui-r2-harness`**, sans modifier les tests ni leur configuration :

1. Même `aiosqlite.connect(':memory:')` suivi de `SELECT 1` reste bloqué dans le
   sélecteur asyncio. La trace à cinq secondes montre le worker attendant le
   prochain travail et la boucle attendant son réveil. Un `sitecustomize.py`
   borne l'attente de `selectors.EpollSelector.select` à 1 ms ; le même essai
   retourne alors `[(1,)]`. Les premiers lancements voisins bloqués ont été
   interrompus et ne sont pas comptés comme des portes réussies. Une première
   borne à 50 ms rendait les fixtures inutilement lentes ; elle a été remplacée
   avant les exécutions retenues.
2. `tests/conftest.py:425` appelle `os._exit` en fin de session, ce qui peut arrêter
   pytest avant l'écriture JUnit. Le plugin temporaire `r2_reports` écrit le rapport
   avant ce hook et expose les échecs. Il ne change aucun test, aucune assertion,
   aucun statut et aucune fixture. Les rapports ont été lus après terminaison.

Vitest utilise `npm_config_offline=true`, `--configLoader runner` et `--no-cache`
pour employer les dépendances déjà présentes sans écrire dans leur répertoire
partagé. Les fichiers de tests ne dépendent d'aucun auxiliaire sous `/tmp`.


Commande backend de la porte groupée, exécutée depuis cet arbre :

```sh
PYTHONPATH=/tmp/divers-ui-r2-harness OLLAMA_BASE_URL=http://127.0.0.1:9 \
.venv/bin/python -m pytest \
  tests/test_b1991_fournisseur_agenda_inconnu.py \
  tests/test_routers_calendar.py \
  tests/test_regression_facturation_agenda.py \
  tests/test_frontiere_facturation_agenda.py \
  tests/test_c22b_caldav_ecriture.py \
  tests/test_calendar_allday_semantics.py \
  tests/test_google_calendar_civil_time.py \
  tests/test_calendar_jeton_de_version.py \
  tests/test_calendar_rappel_par_defaut.py \
  tests/test_c20_b1888_transaction_activites.py \
  tests/test_c20_b1889_notes_heritees.py \
  tests/test_c20_b1890_activites_sans_contact.py \
  tests/test_c20_b1891_reparation_transaction.py \
  tests/test_activity_migration.py \
  tests/test_b1153_migration_colonnes.py \
  tests/test_b1140_migration_sans_verrou.py \
  tests/test_b1153_rejeu_astra_v2.py \
  tests/test_r5_9_notes.py \
  tests/test_r5_6_journal.py \
  tests/test_migration_errors.py \
  tests/test_c20_b2010_limite_cle.py \
  tests/test_c20_b2011_cle_sans_espace.py \
  tests/test_b1348_verification_cle.py \
  tests/test_c20_b2009_motifs_ambigus.py \
  tests/test_c19d_b1088_securite_memoire.py \
  tests/test_r2_2_protection.py \
  tests/test_c20_b1893_provenance_sans_marque.py \
  tests/test_t4_4_historique_documents.py \
  tests/test_t4_10_finitions.py \
  -q -p no:cacheprovider -p r2_reports --timeout=120 \
  --junitxml=/tmp/divers-ui-r2.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Après les tests voisins de chaque correctif frontend, commande finale dans
`src/frontend`, limitée aux dix fichiers de tests ajoutés ou modifiés :

```sh
npm_config_offline=true npx vitest run \
  src/components/atelier/AgentSession.accordMoteur.test.tsx \
  src/components/atelier/AgentSession.profilChange.b2012.test.tsx \
  src/components/atelier/AgentSession.refusDestination.b2013.test.tsx \
  src/components/atelier/AgentSession.refusHttp.b2013.test.tsx \
  src/components/invoices/InvoiceForm.abandonPaiement.b2014.test.tsx \
  src/components/invoices/InvoiceForm.focusAbandon.b2014.test.tsx \
  src/components/invoices/InvoiceForm.pied.c19d.test.tsx \
  src/components/invoices/InvoiceForm.soumission.test.tsx \
  src/components/calendar/EventForm.test.tsx \
  src/components/prototype/usePrototypeMeetingData.test.tsx \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=json --outputFile=/tmp/divers-ui-r2-vitest.json && \
npm_config_offline=true npx tsc --noEmit && npm run lint
```

Les trois passages voisins frontend ont porté sur `InvoiceForm` et
`useDialogFocusTrap` (176 tests, 45 fichiers), `AgentSession` (32 tests,
15 fichiers), puis `EventForm` et `usePrototypeMeetingData` (34 tests,
7 fichiers), toujours avec trois workers maximum. Les 67 fichiers sont distincts :
**242 tests voisins réussis**, dont les 44 tests rejoués dans la porte finale.
Les rapports correspondants sont `/tmp/divers-ui-r2-c5-vert.json`,
`/tmp/divers-ui-r2-c7-vert.json` et `/tmp/divers-ui-r2-c2-vert.json` ; ils ont été lus.


### Résultats définitifs de la passe 2

| Porte | Périmètre | Réussis | Échecs / erreurs | Ignorés |
| --- | --- | ---: | ---: | ---: |
| Pytest | 29 fichiers touchés ou voisins ; `/tmp/divers-ui-r2.xml` | 659 | 0 / 0 | 0 |
| Vitest final | 10 fichiers de tests ajoutés ou modifiés ; `/tmp/divers-ui-r2-vitest.json` | 44 | 0 | 0 |
| Vitest voisins supplémentaires | 57 fichiers distincts, hors des dix fichiers de la porte finale | 198 | 0 | 0 |
| Ruff | `src/backend tests`, sans correction automatique, après la porte Pytest | contrôle réussi | 0 diagnostic | sans objet |
| TypeScript | `npx tsc --noEmit` | contrôle réussi | 0 diagnostic | sans objet |
| ESLint | `npm run lint` | contrôle réussi | 0 erreur, 27 avertissements | sans objet |

Le XML final a été lu après le code de sortie 0 : 659 cas, zéro `failure`, zéro
`error`, zéro `skipped`, durée 621,836 secondes. Les JSON frontend final et voisins
ont également été lus. Les 27 avertissements ESLint concernent des fichiers
non modifiés par cette passe ; aucun seuil ni règle n'a été assoupli. Aucun rouge
connu n'a été exclu d'un résultat : les fichiers signalés dans la demande ne font
pas partie du périmètre ciblé.

Les retours au vert intermédiaires comprennent 66 tests voisins de lecture agenda,
26 tests de création et de frontières agenda, 170 puis 172 tests des migrations
d'activités, 309 tests des notes, messages de clé et protections mémoire, et
53 tests pour la reprise complète de provenance et vérification de clé. Ces
exécutions ne sont pas additionnées à la porte finale.

`git diff --check` ne signale aucune erreur d'espacement. L'index est inchangé,
`HEAD` reste `41559324` et les 24 fichiers du lot migrations restent identiques à
`75498edd`. Les changements de cette passe sont tous non indexés et non commités.
La reprise du contenu est terminée ; le rebase de l'historique reste à effectuer
par l'orchestrateur, avec les droits Git nécessaires.

## Remédiation de la relecture, passe 3

Reprise du 17 novembre 2026, dans le même arbre, sur `70cce49c`. Aucun fichier
suivi n'était modifié ; les liens `.venv` et `src/frontend/node_modules` étaient
déjà non suivis. Les quatre constats sont confirmés. Les correctifs et tests
ci-dessous restent non indexés et non commités. **Le rebase de l'historique reste
bloqué par les droits du bac à sable**, comme détaillé au constat 4.

### 1. P1 : relire les événements historiques de l'alias

Test ajouté puis lancé seul :
`tests/test_c20_calendar_primary_relecture.py::test_r3_historique_primary_relu_sans_changer_de_dossier`.
La fixture utilise SQLite en mémoire, les routes FastAPI et le vrai service
Google avec un transport HTTP simulé. Elle précharge un événement sous `primary`
avant toute résolution, puis le relit par alias et par identifiant réel.

Rouge : **1 échec**, `/tmp/divers-ui-r3-c1-rouge.xml`, lu. Ligne exacte :

```text
AssertionError: assert [] == ['rendez-vous']
```

La réconciliation du cache ne rattache une ancienne ligne qu'après confirmation
de cet événement par Google dans la destination résolue et concordance du compte
de la ligne historique. Le dossier, les rappels et le motif de blocage restent
intacts. Aucune migration globale des lignes `primary` n'est effectuée.
Les trois cas de `test_r3_reconciliation_ne_deplace_pas_un_evenement_ambigu`
protègent un autre compte, un compte absent et un autre agenda du même compte.

Après correction, les 63 tests voisins initiaux et le cas de relecture passent.
Les trois nouveaux cas d'isolation avaient une différence de représentation
SQLite de `synced_at` (aware avant relecture, naïve après) : le cliché de référence
est maintenant pris après `refresh`, en conservant la comparaison de tous les
champs. Les quatre cas passent dans `/tmp/divers-ui-r3-c1-isolation-vert.xml`, lu.
La porte finale rejoue les tests voisins et ces cas ensemble.

### 2. P1 : distinguer la sélection SQL de l'alias sur toutes les opérations

Test ajouté puis lancé seul, huit variantes :
`tests/test_c20_calendar_primary_relecture.py::test_r3_selection_primary_inconnue_refusee_sur_toutes_les_operations`.
Il exerce liste, lecture unitaire, modification et suppression, avec et sans
compte, et impose un refus explicite avant tout appel Google et toute mutation
du cache. Rouge : **8 échecs**, `/tmp/divers-ui-r3-c2-rouge.xml`, lu. Ligne exacte
du cas liste avec compte :

```text
E       assert 200 == 400
```

Test frontend ajouté et lancé seul avant correction :
`src/frontend/src/services/api/calendar.selection.test.ts`. Rouge : **4 échecs,
1 succès**, `/tmp/divers-ui-r3-c2-front-rouge.json`, lu. Ligne exacte :

```text
AssertionError: expected null to be 'true' // Object.is equality
```

Les quatre appels frontend portent désormais `calendar_id_is_stored=true` quand
ils désignent un agenda sélectionné. La liste sans sélection conserve l'alias
historique. Les quatre routes vérifient cette distinction : fournisseur inconnu
refusé en 400, sélection absente en 404. Les quatre cas de
`test_r3_selection_absente_ne_devient_pas_google` couvrent aussi ce second refus.
La sélection d'une ligne SQL appelée `primary` ne peut plus désigner en silence
le calendrier principal Google. La création garde son contrat existant.

Après correction : **114 tests backend réussis**, aucun échec, erreur ou ignoré
dans `/tmp/divers-ui-r3-c2-vert.xml`, lu ; **178 tests frontend réussis** dans
29 fichiers, aucun échec ni ignoré, dans `/tmp/divers-ui-r3-front-vert.json`, lu.
Appelants relus : `CalendarPanel.loadEvents`, `EventForm`, `EventDetail`,
`usePrototypeMeetingData`, ainsi que la synchronisation backend.

### 3. P1 : modifier et supprimer la destination réelle et son cache

Tests ajoutés puis lancés séparément avant correction :
`test_r3_cycle_alias_google_met_a_jour_puis_supprime_le_cache` (alias omis et
explicite) et `test_r3_suppression_par_alias_retire_la_ligne_du_cache`, dans le
même fichier backend. Rouges : **2 échecs**, puis **1 échec**, rapports
`/tmp/divers-ui-r3-c3-cycle-rouge.xml` et
`/tmp/divers-ui-r3-c3-suppression-rouge.xml`, lus. Lignes exactes :

```text
AssertionError: assert 'Titre initial' == 'Titre modifié'
AssertionError: assert [CalendarEven...5, 55, 1559))] == []
```

Lecture, modification et suppression partagent désormais la résolution de
destination. Le contrôle du compte précède les opérations Google. Les tests
exercent création, modification, lecture unitaire, suppression, disparition SQL
et absence à la lecture suivante ; le dossier reste conservé pendant l'édition.
`test_r3_destination_google_refuse_un_autre_compte` et
`test_r3_lecture_par_alias_ne_designe_pas_un_agenda_voisin_du_meme_compte`
ferment les croisements de compte et de calendrier : avant correction,
**4 échecs et 1 succès**, `/tmp/divers-ui-r3-c3-frontieres-rouge.xml`, lu.

La relecture du correctif a identifié le cas d'une mutation historique **avant**
la première lecture : résoudre la destination sans réconcilier son cache aurait
introduit une nouvelle régression. Les six variantes ajoutées de
`test_r3_mutation_historique_sans_lecture_prealable` ont donné **2 échecs et
4 succès** avant leur correctif, `/tmp/divers-ui-r3-c3-historique-rouge.xml`, lu :

```text
AssertionError: assert ('primary', '...e', 'dossier') == ('agenda@exam...é', 'dossier')
AssertionError: assert [CalendarEven... 58, 145427))] == []
```

La même réconciliation prudente est maintenant appliquée après confirmation
Google d'une modification ou d'une suppression. Un compte absent ou différent
interdit toujours le déplacement de la ligne historique. Appelants relus :
formulaire et détail d'événement, service Google, lecture du cache dans
`dashboard.py`. Les tests voisins couvrent aussi les agendas locaux, CalDAV,
les collisions d'identifiants, les dates et les conflits de version.

### 4. P2 : reprendre B-2029 et réconcilier le contrat de migration

L'intégration locale avait déjà avancé jusqu'à `0047eb5e`, après `c127023a` :
six commits de chaque côté de la divergence. Test ajouté dans un nouveau fichier
avant toute reprise :
`tests/couverture/couverture-ecran.contrat-migration.test.mjs`, lancé seul.
Rouge : **1 échec**, `/tmp/divers-ui-r3-c4-rouge.tap`, lu. Lignes d'échec :

```text
not ok 1 - passe 3 : la migration du chat est acquittée sans autorisation réseau
    la migration doit être simulée, sans émission réseau
    +   'réseau'
```

La commande `git rebase c20/integration` a été tentée dans cet arbre, sans
contournement ni demande d'élévation. Elle n'a pas changé `HEAD` et a répondu :

```text
error: could not create temporary /data/boucle-therese-mac/Dev Synoptia/Synoptia-THERESE/.git/worktrees/gpt-c20-divers-ui/rebase-merge: Read-only file system
```

Les deux fichiers `tests/couverture/couverture-ecran.mjs` et
`tests/couverture/couverture-ecran.test.mjs` ont donc été repris de l'intégration
locale, avec B-2029 et tous ses tests de concurrence. Aucun autre fichier
d'intégration n'a été recopié. Le rebase réel reste à faire par l'orchestrateur.

Le test B-2029 de l'intégration confirme ensuite la contradiction : **1 échec et
1 succès**, `/tmp/divers-ui-r3-c4-contrat-rouge.tap`, lu, avec :

```text
    la simulation ne donne pas accès au réseau
    true !== false
```

Le contrat retenu est l'acquittement local du seul POST exact de migration,
sans autorisation réseau. `requeteAutorisee` le refuse ; `requeteASimuler` et
la garde assurent le succès local et le comptage. L'ancienne attente `true`
devient `false`, avec le test d'acquittement conservé et le nouveau test de bout
en bout de la garde : aucun cas ni contrôle existant n'a été retiré ou assoupli.
Appelants relus : installation de la garde, suivi des acquittements, fermeture
du navigateur et rapport d'interruption. Résultat : **17 succès, 0 échec,
12 cas navigateur ignorés par leur garde existante**, dans les deux fichiers
Node ; rapports `/tmp/divers-ui-r3-couverture.tap` et
`/tmp/divers-ui-r3-c4-vert.tap`, lus. Aucun navigateur ni port applicatif ouvert.

### Portes et conditions de rejeu

Les nouveaux tests totalisent **30 cas backend, 5 cas frontend et 1 cas Node**,
en plus des tests B-2029 repris de l'intégration. Aucune suite complète lancée,
aucun réseau, fournisseur LLM, accès à `~/.therese` ou `.app-loop/`, ni commande
`rm`, `git add` ou commit. Les appels Google, les routes et les navigations de
l'instrument sont simulés ; les adresses de ports réservés dans les tests Node
ne sont que des données comparées en mémoire.

Commande backend finale, depuis cet arbre :

```sh
PYTHONPATH=/tmp/divers-ui-r2-harness OLLAMA_BASE_URL=http://127.0.0.1:9 \
.venv/bin/python -m pytest \
  tests/test_c20_calendar_primary_relecture.py \
  tests/test_b1991_fournisseur_agenda_inconnu.py \
  tests/test_routers_calendar.py \
  tests/test_regression_facturation_agenda.py \
  tests/test_frontiere_facturation_agenda.py \
  tests/test_c22b_caldav_ecriture.py \
  tests/test_calendar_allday_semantics.py \
  tests/test_google_calendar_civil_time.py \
  tests/test_calendar_jeton_de_version.py \
  tests/test_calendar_rappel_par_defaut.py \
  tests/test_pluriel_agenda_google.py \
  tests/test_agenda_portes_par_identifiant.py \
  -q -p no:cacheprovider -p r2_reports --timeout=120 \
  --junitxml=/tmp/divers-ui-r3.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Les deux auxiliaires de la passe 2 sont réutilisés : réveil du sélecteur asyncio
et écriture du JUnit avant le `os._exit` du conftest. Les tests n'en dépendent pas
hors de ce bac à sable. Le XML final a été lu après terminaison : **141 cas,
0 failure, 0 error, 0 skipped**, durée 105,057 secondes, puis Ruff a été lancé.

Commande frontend depuis `src/frontend` :

```sh
npm_config_offline=true npx vitest run \
  src/services/api/calendar.selection.test.ts \
  src/services/api/caldav.test.ts \
  src/components/calendar \
  src/components/prototype/usePrototypeMeetingData.test.tsx \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=json --outputFile=/tmp/divers-ui-r3-front-vert.json
npm_config_offline=true npx tsc --noEmit
npm run lint
```

La dépendance `@playwright/test` n'est pas installée dans cet arbre. Le premier
lancement Node a échoué avant exécution et le premier TypeScript a signalé les
types manquants dans les tests e2e importés. Aucun de ces diagnostics n'est
présenté comme un rouge fonctionnel. Les exports et types réels de
`playwright/test`, déjà disponibles dans le cache npm local, ont été raccordés
sans installation ni téléchargement. Le lien temporaire `node_modules` ajouté
à la racine pour TypeScript a ensuite été déplacé sous `/tmp` ; les deux liens
de dépendances préexistants restent inchangés.

Pour Node, `/tmp/divers-ui-r3-node-loader.mjs` raccorde cette même dépendance,
transpose les chemins temporaires macOS vers `/tmp` et remplace les pipes
interdits de `spawnSync` par des fichiers temporaires. Les codes de sortie,
sorties enfant et assertions sont conservés. Le premier passage voisin avait
quatre erreurs dues aux pipes `EPERM` ; le passage final avec ces auxiliaires
les résout sans modification des tests. Commandes :

```sh
NODE_OPTIONS='--import=/tmp/divers-ui-r3-node-loader.mjs' \
  node tests/couverture/couverture-ecran.test.mjs
NODE_OPTIONS='--import=/tmp/divers-ui-r3-node-loader.mjs' \
  node tests/couverture/couverture-ecran.contrat-migration.test.mjs
```

| Porte | Périmètre | Réussis | Échecs / erreurs | Ignorés |
| --- | --- | ---: | ---: | ---: |
| Pytest | 12 fichiers touchés ou voisins ; XML relu | 141 | 0 / 0 | 0 |
| Vitest | 29 fichiers ; JSON relu | 178 | 0 | 0 |
| Node | 2 fichiers couverture ; TAP lus | 17 | 0 | 12 |
| Ruff | `src/backend tests`, sans correction automatique | réussi | 0 diagnostic | sans objet |
| TypeScript | `npx tsc --noEmit` avec dépendance locale raccordée | réussi | 0 diagnostic | sans objet |
| ESLint | `npm run lint` | réussi | 0 erreur, 27 avertissements | sans objet |

Les avertissements ESLint concernent des fichiers non modifiés par cette passe.
Aucun rouge connu de la demande ne figure dans ces fichiers ciblés. Le contenu
B-2029 et son contrat sont corrigés ; **l'historique n'est pas rebasé** et ce point
du constat 4 demeure à traiter par l'orchestrateur. `HEAD` reste `70cce49c` et
l'index reste inchangé.
