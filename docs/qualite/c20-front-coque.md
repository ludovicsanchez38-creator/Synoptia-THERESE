# Cycle 20, lot front-coque

Branche `grok/c20-front-coque`, départ `bc8baf54` (v0.83.0-alpha, le lot suit le rapport front-chat déjà sur la branche). Chaque `confirme` a un test de comportement rouge, commité seul, puis le plus petit correctif. Rien n'a été poussé.

`ConversationCanvasPrototype` est la coque montée par `App.tsx`. Les cartes e-mail et agenda sont celles qu'elle rend.

## Verdicts

| id | verdict | test (chemin::nom) | commit du rouge | commit du correctif |
| --- | --- | --- | --- | --- |
| B-1842 | confirme | `src/frontend/src/components/prototype/ConversationCanvasPrototype.raccourciMemoire.b1842.test.tsx`::`ferme la mémoire, aligne le store, et la même vue se rouvre` ; `…`::`une saisie en cours retient le raccourci : la mémoire reste affichée` | `18acef88` | `f940c6b9` |
| B-1843 | confirme | `src/frontend/src/components/prototype/ConversationCanvasPrototype.parcoursDepuisVue.b1843.test.tsx`::`Écrire depuis l’agenda affiche le parcours et l’agenda se rouvre ensuite` | `98467ed2` | `8444c22c` |
| B-1940 | confirme | `src/frontend/src/components/prototype/EmailConversationCard.redactionLibre.b1940.test.tsx`::`la section, le champ et les réglages de génération s’effacent` | `793ba5b0` | `2a3c7dab` |
| B-1941 | confirme | `src/frontend/src/components/prototype/EmailConversationCard.erreur.b1941.test.tsx`::`le bloc d’erreur garde Réessayer, l’en-tête garde l’ouverture` | `dbd56650` | `ce12227b` |
| B-1942 | confirme | `src/frontend/src/components/prototype/MeetingConversationCard.points.b1942.test.tsx`::`objectif, lieu et participants absents portent une alerte` ; `…`::`quand tout est renseigné, la ligne porte une coche` | `ff94e26a` | `31c8145c` |
| B-1943 | confirme | `src/frontend/src/components/prototype/ConversationCanvasPrototype.controlesVisibles.b1943.test.tsx`::`Contrôle des données s’ouvre, il n’est pas retiré de l’écran` ; `…`::`le nom d’espace reste annonçable` | `b30123e5` | `5c95daa0` |
| B-1944 | rejete | Preuve déjà en place : `src/frontend/src/components/prototype/ConversationCanvasPrototype.da.test.tsx` lignes 82-87 et 92-93, `ConversationCanvasPrototype.tsx` ligne 2119 | aucun | aucun |
| B-1945 | rejete | Même preuve que B-1944 (doublon de lecture) | aucun | aucun |
| B-1946 | rejete | Preuve déjà en place : `ConversationCanvasPrototype.tsx` lignes 2238 et 2446, `MeetingConversationCard.tsx` lignes 284-285 et 431, `docs/plans/2026-08-28-onze-upgrades-ux.md` lignes 68-70, `AccueilMoinsCharge.test.tsx` lignes 8-10 | aucun | aucun |
| B-1947 | rejete | Preuve déjà en place : `src/backend/app/services/email/provider_factory.py` ligne 18, `tests/test_email_setup_status_imap.py`::`test_un_compte_imap_compte_comme_messagerie_configuree`, ternaire `ConversationCanvasPrototype.tsx` ligne 2427 | aucun | aucun |
| B-1948 | rejete | Déjà couvert par le correctif B-1943 : `ConversationCanvasPrototype.tsx` lignes 2086 et 2089, test `ConversationCanvasPrototype.controlesVisibles.b1943.test.tsx`::`Contrôle des données s’ouvre, il n’est pas retiré de l’écran` | aucun | aucun |

## Règle à trancher

Aucune.

## Rejets

B-1944 et B-1945 décrivent le même `aria-current`. Le test `le rail dit où l’on est` (`ConversationCanvasPrototype.da.test.tsx` lignes 82-87) verrouille le geste : après le verbe « Retrouver », Accueil garde `aria-current=page`, parce qu’un verbe de l’établi laisse la coque sur l’accueil. `IconButton` ligne 2119 (`active={!chatOpen && !embeddedView}`) suit cet état de coque. Quand la vue Projets s’ouvre, le même test retire `aria-current` d’Accueil (lignes 92-93).

B-1946. La phrase du scénario agenda (ligne 2238) borne la consultation : Thérèse s’appuie sur les événements et le CRM réellement reliés, « sans rien inventer ». La carte le répète ligne 431 : « Aucun contexte absent n’est inventé. » « Préparer un événement » (ligne 284) et la puce « Écriture confirmée » (ligne 2446) décrivent une écriture que tu confirmes. Ligne 285 : « Aucune donnée n’est écrite avant la confirmation finale. » Le plan du 28 août (lignes 68-70) et `AccueilMoinsCharge.test.tsx` (lignes 8-10) gardent ces puces : chacune dit ce que le parcours peut faire.

B-1947. Les comptes persistés ont deux types. `provider_factory.py` ligne 18 : `EmailProviderType = Literal["gmail", "imap"]`. Outlook et Yahoo y sont des préréglages IMAP (lignes 98 et 107), pas une valeur de `account.provider`. Le test IMAP cité traite un compte IMAP comme une messagerie configurée. Le ternaire ligne 2427 (`gmail` donne « Gmail », le reste donne « IMAP ») suit ce modèle.

B-1948 vise la même moitié de bouton que B-1943, déjà corrigée. Ligne 2086, la classe est `mr-1 flex h-9 … sm:flex whitespace-nowrap shrink-0`, sans `hidden`. Le mot est dans `<span className="max-sm:sr-only">` (ligne 2089). Le test B-1943 prouve que le bouton reste dans l’arbre et ouvre le Centre de confiance.

## Portes

Commandes lancées dans cet arbre, après le dernier correctif `5c95daa0`.

- pytest : `OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/ --ignore=tests/e2e -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/front-coque-pytest.xml`. Exit 1. 6549 passés, 6 échoués, 51 ignorés, 6606 au total. Échecs :
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]`
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]`
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]`
  - `tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`
  - `tests.test_typage_lot_confidentialite::test_les_quatre_diagnostics_du_lot_confidentialite_ne_reviennent_pas`
- Les cinq premiers sont la référence connue de ce Mac, hors lot. Le sixième cherche la chaîne ` error:` dans la sortie de mypy. Le shell de la porte colore cette sortie, donc la chaîne est absente alors que mypy a bien tourné. Relancé seul, sans variable de couleur : 1 passé. Le diff `bc8baf54..5c95daa0` ne contient aucun fichier Python.
- ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests`. Exit 0. `All checks passed!`
- vitest : `cd src/frontend && npm run test -- --run`. Exit 0. 4086 passés, 0 échoué, 955 fichiers.
- tsc : `cd src/frontend && npx tsc --noEmit`. Exit 0. 0 erreur.
- eslint : `cd src/frontend && npm run lint`. Exit 0. 0 erreur, 27 avertissements, sous le plafond `--max-warnings 27`.

## Incertitudes

- L’état « Aucun compte email connecté », `EmailConversationCard.tsx` ligne 117, garde un second `BoutonOuvrirLaVue`. B-1941 visait le bloc d’erreur. Ce bouton n’a pas bougé.
- jsdom n’applique pas Tailwind. Le test B-1943 pose `.hidden { display: none !important }` et vérifie l’arbre d’accessibilité. Le repli `sr-only` sous les paliers sm et md n’a pas été vu dans un navigateur : aucun outil navigateur dans cette session.
