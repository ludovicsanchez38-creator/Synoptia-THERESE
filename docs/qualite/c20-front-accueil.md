# Cycle 20, lot front-accueil

Branche `grok/c20-front-accueil`, base `4956e59f` (v0.83.0-alpha).
Chaque candidat confirmé a d'abord un test de comportement rouge, commité seul, puis le plus petit correctif.

## Verdicts

| id | verdict | test | commit du rouge | commit du correctif |
| --- | --- | --- | --- | --- |
| B-1839 | rejete | `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:1344-1348` et `navigationStore.ts:94` | aucun | aucun |
| B-1840 | confirme | `src/frontend/src/components/onboarding/ProfileStep.recharge.b1840.test.tsx::Continuer renvoie l’entreprise, l’e-mail, le contexte et le SIRET déjà enregistrés` | `8f1fe52a` | `618122f5` |
| B-1841 | confirme | `src/frontend/src/components/prototype/AtelierConversationCard.prevol.b1841.test.tsx::une branche vide empêche de préparer la mission` | `78b4abae` | `5ffe7800` |
| B-1932 | confirme | `src/frontend/src/components/onboarding/OnboardingWizard.titreUnique.b1932.test.tsx::l’accueil laisse le titre du dialogue seul au niveau 1` | `b855ca70` | `4345867a` |
| B-1933 | confirme | `src/frontend/src/components/prototype/CapabilityCenter.recherche.b1933.test.tsx::une recherche qui sort du groupe ne laisse pas le panneau au nom de ce groupe` | `9d587868` | `9dc7d1aa` |
| B-1934 | confirme | `src/frontend/src/components/prototype/AtelierConversationCard.mission.b1934.test.tsx::le champ s’appelle comme son libellé visible` | `57a6d223` | `5c54cf79` |
| B-1935 | confirme | `src/frontend/src/components/onboarding/CompleteStep.reste.b1935.test.tsx::sans IA, l’illustration n’est plus un cotillon de fête` | `9ddea913` | `15991882` |
| B-1936 | confirme | `src/frontend/src/components/onboarding/LLMStep.cloudPromesse.b1936.test.tsx::retire la promesse locale quand le modèle choisi part en ligne` | `6229e12f` | `7ecfe33e` |
| B-1937 | rejete | `src/frontend/src/components/prototype/AtelierConversationCard.mission.b1934.test.tsx::le champ s’appelle comme son libellé visible` | aucun | aucun |
| B-1938 | confirme | `src/frontend/src/components/prototype/CapabilityCenter.tabOrder.b1938.test.tsx::pendant une recherche, aucun onglet ne reste tabulable` | `9f1d564c` | `cfc23303` |
| B-1939 | regle_a_trancher | `src/frontend/src/components/prototype/CapabilityCenter.typesExpliques.test.tsx::les cartes Agenda et Email portent le nom de l’écran qu’elles ouvrent` | aucun | aucun |

Le fichier B-1841 contient aussi `un dépôt ni propre ni sale empêche de préparer la mission`.

Le fichier B-1932 contient aussi `le récapitulatif est un titre de niveau 2`.

Le fichier B-1934 contient aussi `le diff et les résultats de tests suivent les jetons de thème`.

Le fichier B-1935 contient aussi `avec une IA prête, le cotillon reste` et `le dossier de travail s’affiche en entier, et le survol aussi`.

## Rejets

B-1839. L'effet de `ConversationCanvasPrototype.tsx` (lignes 1344 à 1348, dépendance `isStreaming` ligne 1386) n'avance `derniereVueRef` que si la navigation aboutit. Une demande posée pendant le flux est rejouée quand `isStreaming` redevient faux. Le second `runAction('crm.open')` du test `ConversationCanvasPrototype.parite.test.tsx:297` ne change plus la vue : `setView` ignore une vue déjà active (`navigationStore.ts:94`). Retirer cet appel laisse le test vert. Le titre du test est tenu par l'effet, le corps ajoute un appel devenu inutile.

B-1937. Le même constat que B-1934, déjà corrigé. Le champ (`AtelierConversationCard.tsx:210`) n'a plus d'`aria-label`. Son nom accessible est le libellé visible « Mission à confier ». Le test B-1934 (lignes 66 et 67) exige ce nom et l'absence d'un champ nommé « Mission Atelier ». Le texte « Mission Atelier » qui reste à la ligne 103 est le titre de repli d'une mission passée, pas le nom du champ.

## Règle à trancher

B-1939. Le titre de la carte email (« Écrire un e-mail ») et sa description (« Lire les messages et préparer des réponses ») ne disent pas le même geste. Le code et les tests fixent le titre, pas la phrase qui doit l'accompagner.

Le titre est le verbe de l'établi (`lib/etabli.ts`, P-117) et le nom exigé par P-128 (`CapabilityCenter.typesExpliques.test.tsx`, lignes 31 à 34). L'écran ouvert par `scenario: 'email'` s'annonce « Écrire un message » (`TITRES_ETABLI.email`). `lexiqueParcours.test.ts` refuse un titre de consultation. Il n'y a pas de champ `destination` : l'identifiant de scénario est la destination, la même que les cinq verbes.

La description, elle, colle à ce que le scénario montre vraiment. La colonne principale rend `EmailInboxCard` (« Messages reçus », `ConversationCanvasPrototype.tsx:2299`). Le canevas latéral est `EmailMessageCanvas`, la rédaction. Le bandeau dit « Je prépare un message ».

Options :

1. Renommer la carte vers la lecture. Contredit P-128, le verbe de l'établi et le titre d'écran déjà figés après la dérive « Consulter mes emails ».
2. Réécrire la description pour ne parler que d'écriture. La colonne principale resterait une boîte de réception que la carte ne mentionnerait plus.
3. Garder le titre d'écriture et une description qui dit les deux gestes.

Recommandation : l'option 3. Le titre reste « Écrire un e-mail ». La description peut rester, ou devenir « Préparer une réponse à partir des messages reçus », sans renommer la carte. Aucun changement dans ce lot.

## Tests voisins alignés, sans les affaiblir

`AtelierConversationCard.test.tsx`, dans `5c54cf79`, cherche le champ par « Mission à confier » au lieu de « Mission Atelier ». L'ancien nom accessible était le défaut. Les trois scénarios (saisie, champ verrouillé pendant la mission, seconde saisie) sont inchangés.

B-857 (`CapabilityCenter.ariaSelected.c9.test.tsx`) reste : aucun onglet `aria-selected` pendant une recherche. B-1938 aligne seulement `tabIndex` sur cette même sélection. P-111 (`LLMStep.localDabord.p111.test.tsx`) garde la promesse locale quand le modèle choisi est `qwen3:8b`.

## Portée d'exécution

`ProfileStep` n'est monté qu'à l'étape 1 de `OnboardingWizard` (`OnboardingWizard.tsx:294`), lui-même monté par `App.tsx:300`. `CompleteStep` est l'étape 5, `LLMStep` l'étape 2. `WelcomeStep` est la première étape du même assistant.

`AtelierConversationCard` est rendu par `AtelierWorkspaceCanvas`, appelé depuis `ConversationCanvasPrototype.tsx`. `CapabilityCenter` est ouvert par « Plus d'outils » et rendu à la ligne 2706 de la même coque.

`setProfile` remplace toute la fiche. Le rechargement de B-1840 ne renvoie pas les champs absents du formulaire (siren, code APE, numéro de déclaration d'activité). Une saisie déjà commencée n'est pas écrasée.

## Portes

Mesurées dans cet arbre, après les correctifs. `.venv` et `node_modules` sont les liens vers le dépôt principal. Aucun fichier backend n'a été modifié.

Pytest (`OLLAMA_BASE_URL=http://127.0.0.1:9`, `tests/` hors `tests/e2e`, junit `/tmp/front-accueil-pytest.xml`) : 6606 tests, 6549 passés, 6 échecs, 0 erreur, 51 ignorés.

Échecs :

- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`
- `tests.test_typage_lot_confidentialite::test_les_quatre_diagnostics_du_lot_confidentialite_ne_reviennent_pas`

Les cinq premiers sont la référence connue de cette machine, antérieure au lot. Le sixième vient de la colorisation mypy : la session injecte `FORCE_COLOR`, donc la chaîne attendue ` error:` n'est plus contiguë. Rejoué seul sans `FORCE_COLOR` ni `NO_COLOR`, il passe. Aucun fichier backend n'a été modifié par le lot.

Ruff (`src/backend` et `tests`, `--no-fix`) : tout passe.

Vitest (`npm run test -- --run` depuis `src/frontend`) : 943 fichiers passés, 4065 tests passés, 0 échec.

TypeScript (`npx tsc --noEmit` depuis `src/frontend`) : sortie vide, succès.

ESLint (`npm run lint`, seuil `--max-warnings 27`) : 0 erreur, 27 avertissements, succès. Ces avertissements sont antérieurs au lot (aucun fichier signalé n'est dans le diff).
