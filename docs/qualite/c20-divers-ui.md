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
