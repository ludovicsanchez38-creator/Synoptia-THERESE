# Cycle 20 : lot backend-agents

Le tableau conserve le bilan de la première passe. Depuis la relecture,
B-1826 est retiré des correctifs en attente d'un arbitrage ; les autres
remédiations de la passe 2 sont décrites en fin de document.

| ID | Verdict | Test (chemin::nom) | Ligne d'échec du rouge | Correctif |
| --- | --- | --- | --- | --- |
| B-1818 | regle_a_trancher | `tests/test_mode_cabinet.py::TestLaPolitiqueEstUnique::test_une_conversation_libre_reste_ouverte_meme_en_mode_cabinet` | Sans objet | Sans objet |
| B-1819 | rejete | `tests/test_b1071_pas_de_bascule_locale_vers_le_cloud.py::test_ollama_indisponible_ne_bascule_pas_vers_un_service_en_ligne` | Sans objet | Sans objet |
| B-1824 | confirme | `tests/test_b1824_comptage_generation.py::test_texte_partiel_puis_panne_ne_referme_pas_le_circuit[429]` et `[503]` ; `::test_une_generation_reussie_compte_un_seul_succes` | `AssertionError: assert 0 == 1` pour chaque panne partielle ; `AssertionError: assert 2 == 1` pour le succès | non commité |
| B-1825 | confirme | `tests/test_b1825_mcp_echec_initialisation.py::test_echec_initialisation_arrete_processus_et_lecteurs` ; `::test_annulation_initialisation_arrete_aussi_processus_et_lecteurs` | `AssertionError: Expected 'mock' to have been called once. Called 0 times.` pour chacun | non commité |
| B-1826 | regle_a_trancher | Test retiré de la collecte ; voir la remédiation passe 2 | Sans objet | Résolution de `c20/integration` ; options : dossiers approuvés, refus de toute clé PATH, ou risque affiché |
| B-1903 | confirme | `tests/test_b1903_voix_locale_absente.py::test_setup_et_dictee_expliquent_la_meme_absence` | `AssertionError: assert 'La voix loca...ation à jour.' == 'Voix locale ...remier usage.'` | non commité |
| B-1904 | confirme | `tests/test_b1904_board_recherche_coupee.py::test_recherche_coupee_annonce_refus_et_le_transmet_au_conseiller` | `AssertionError: assert ('coupée' in '124 caractères de contexte web' or 'désactivée' in '124 caractères de contexte web')` | non commité |

## B-1818 : règle à trancher

Quelle portée donner aux agents actionnables lorsque le mode cabinet est actif ?
La requête `RunActionRequest` ne contient qu'un dictionnaire de paramètres
(`src/backend/app/routers/actions.py:27`) et le moteur transmet ces paramètres
sans identifiant de conversation ni de dossier au rassemblement de contexte
(`src/backend/app/services/action_agents.py:760`). Le résultat est rangé dans
une nouvelle conversation (`src/frontend/src/stores/actionsStore.ts:68`).
La politique existante ferme les souvenirs généraux pour une conversation
rattachée à un dossier, mais les garde visibles hors dossier
(`src/backend/app/services/cloisonnement.py:73`). Elle ne détermine pas à quel
dossier rattacher une action autonome ni comment traiter les courriels sans
rattachement.

Options : conserver l'accès global aux actions autonomes en le signalant
explicitement ; ou demander un dossier et limiter les données de l'action à ce
dossier. Recommandation : en mode cabinet, demander le dossier et ne pas
transmettre les données dont le rattachement ne peut pas être établi. Le choix
doit aussi préciser le cas où l'utilisateur veut volontairement une action
globale. Aucun changement de comportement n'a été fait pour ce candidat.

## B-1819 : preuve du rejet

Le paramètre `bascule_circuit` est conservé pour compatibilité, mais
`LLMService._resolve_with_circuit_breaker` rend toujours la configuration du
fournisseur choisi (`src/backend/app/services/llm.py:812-819`). Le test existant
ouvre le circuit Ollama et vérifie que la configuration reste locale. Les deux
tests de ce fichier ont été relancés : 2 réussis, 0 échec.

## Corrections et vérifications ciblées

- Les chemins modifiés sont actifs en production : `documents.py` et
  `skills.py` appellent `LLMService.generate_content` ; `routers/mcp.py` appelle
  `start_server` ; `main.py` monte `routers/voice.py` ; `routers/board.py`
  consomme `BoardService.deliberate`.
- B-1824 : le flux compte déjà l'issue ; la génération ne la recompte plus.
  Le fichier de régression et les cas voisins du disjoncteur et des trames
  donnent 16 réussites sur 16.
- B-1825 : après une exception ou une annulation d'initialisation, arrêt du
  processus puis attente de la fin effective des lecteurs avant le statut
  d'erreur. Le test d'annulation ajouté est rouge après le premier correctif
  partiel et vert après traitement de l'annulation. Les scénarios MCP combinés
  de B-1825 et B-1826 donnent 50 réussites sur 50.
- B-1826 : le correctif de la première passe est retiré : il restait
  contournable par l'interpréteur d'un lanceur et empêchait aussi certains
  serveurs configurés de démarrer. Le choix reste à arbitrer.
- B-1903 : setup et dictée indiquent la même absence et la même installation
  optionnelle. Les tests vocaux ciblés donnent 22 réussites sur 22.
  Le test existant `tests/test_routers_voice.py::TestVoiceLocalSetup::test_setup_refuse_si_libs_absentes`
  codifiait l'ancien conseil de mise à jour ; il vérifie désormais précisément
  l'absence et la commande d'installation, en conservant le contrôle HTTP 503.
- B-1904 : le Board affiche que la recherche est coupée et transmet toujours
  cette information au conseiller. Les tests ciblés donnent 28 réussites sur 28.

## Portes de la première passe

- Suite demandée : 6 616 cas dans `/tmp/backend-agents-pytest.xml`, dont
  **6 539 réussis, 15 échoués, 0 erreur et 62 ignorés**. Les 15 échecs sont
  tous dans les familles connues avant le lot : huit cas de
  `tests.test_b1153_bac_a_sable_commandes`, deux de
  `tests.test_b1191_commande_introuvable_nommee`, quatre variantes de
  `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches`, et un cas
  de `tests.test_securite_f2_recette_deb`.
- Parmi les 62 ignorés, 11 l'ont été explicitement pour respecter le mandat :
  neuf créent un dépôt Git ou lancent `git add` / `git commit`, et deux
  exécutent un script contenant `rm`. Les 51 autres relèvent des marques
  existantes : 47 exigent RLIMIT_AS sous Linux, deux une génération d'image
  externe, un la construction optionnelle de bundles et un le réseau.
- `.venv/bin/python -m ruff check --no-fix src/backend tests` : réussi,
  zéro diagnostic.
- Exécution sans clés héritées, avec garde réseau native, données jetables et
  redirection vers `/tmp` des seules preuves que les tests cycle 15 écriraient
  dans `.app-loop/`. Le confinement macOS imbriqué est refusé par le bac à
  sable ; une garde native a donc été utilisée pour intercepter les connexions
  et les résolutions DNS de pytest et des sous-processus compatibles. Elle ne
  constitue pas un confinement réseau par le noyau. Certains témoins socket
  utilisent leurs propres simulations. La première garde empêchait aussi la
  communication interne d'asyncio : deux essais ciblés sont restés bloqués
  avant que la garde soit corrigée. Les reprises ciblées et la suite ci-dessus
  utilisent la garde corrigée. Les deux anciens processus pytest, PID 55887 et 56836,
  étaient encore bloqués en fin de contrôle ; le bac à sable a refusé leur
  terminaison par SIGTERM (`PermissionError`).

La suite est donc rouge uniquement sur les familles déjà identifiées, mais
les 11 cas ignorés par mandat et les deux processus bloqués restent à traiter
hors de ce bac à sable. B-1818 reste une règle à trancher.

## Remédiation de la relecture, passe 2

- **Constats 1 et 4, B-1826 : règle à trancher.** La résolution de la commande
  est revenue à celle de `c20/integration`. Le test qui imposait le refus du
  PATH fourni est retiré de la collecte. La Corbeille étant inaccessible dans
  ce bac à sable, son contenu est conservé dans
  `tests/.test_b1826_mcp_chemin_de_resolution.retire`, en attendant son
  déplacement par l'orchestrateur. Le risque signalé par la relecture reste
  présent dans le comportement rétabli : un PATH fourni peut choisir un
  exécutable ou l'interpréteur d'un lanceur.

  Les trois options à trancher sont : enregistrer explicitement des dossiers
  approuvés dans l'application ; refuser toute clé `PATH` dans la configuration
  d'un serveur ; ou conserver ce paramétrage en affichant son risque.
- **Constat 2, B-1904 :** les deux interfaces conservent le contenu de
  `web_search_done` et l'affichent pendant la consultation et le résultat du
  Board ; il est remis à zéro au nouveau lancement. Les deux tests de rendu
  `BoardPanel.rechercheCoupee.test.tsx` et `BoardRechercheCoupee.test.tsx`
  étaient rouges isolément, chacun sur la ligne :
  `TestingLibraryElementError: Unable to find an element with the text: Recherche web coupée. Réactive-la dans Paramètres > Services..`
  Ils contrôlent maintenant aussi l'arrivée d'un avis après le refus.
- **Constat 3, B-1903 :** le statut et les routes de setup, dictée et synthèse
  partagent le même message ; il distingue l'application installée et le
  développement depuis les sources. L'écran des réglages affiche le message
  du statut. Les deux variantes du nouveau test backend étaient rouges avec :
  `AssertionError: assert 'Installe la ...remier usage.' == 'Voix locale ...remier usage.'`
  Les deux variantes du test de rendu étaient rouges, notamment :
  `TestingLibraryElementError: Unable to find an element with the text: Voix locale non installée. Application installée : vérifie la version de THÉRÈSE..`
- **Constat 5, B-1825 :** l'écriture et le vidage du pipe sont dans le
  `try/finally` de `_send_request`. Le test isolé couvre leurs deux échecs et
  un second démarrage réel avec processus fictifs. Pour chaque variante, le
  rouge était : `E   assert not {1: <Future pending>}`.
- **Constat 6 :** le rebase a été effectué par l'orchestrateur ;
  `c20/integration` est ancêtre de HEAD. Aucun nouveau rebase n'a été fait.

### Portes de la passe 2

- Le XML `/tmp/backend-agents-r2.xml` a été lu : **6 705 cas, 6 628 réussis,
  15 échoués, 0 erreur et 62 ignorés**. Les échecs sont les 15 cas connus :
  huit de `test_b1153_bac_a_sable_commandes`, deux de
  `test_b1191_commande_introuvable_nommee`, quatre de
  `test_refus_a_lecran_meme_sans_fiches` et un de `test_securite_f2_recette_deb`.
  Aucun autre échec. Parmi les ignorés, 11 évitent les dépôts, `git add`,
  commits et `rm` interdits ; les 51 autres sont les marques préexistantes
  pour Linux, réseau, génération d'image et bundle.
- La suite utilise des données jetables et une garde native de connexions et
  de résolution DNS ; les preuves des tests du cycle 15 sont redirigées vers
  un dossier temporaire. Le confinement macOS imbriqué a été refusé ; cette
  garde ne constitue donc pas un confinement réseau par le noyau. La première
  version bloquait aussi la communication interne d'asyncio. Le processus
  pytest de cette tentative est resté bloqué (PID 99425) et le bac à sable a
  refusé son arrêt ; la reprise utilise la garde corrigée et vérifiée.
- Frontend : **964 fichiers et 4 092 tests réussis** à la reprise. Le fichier
  `viteSecrets.c19.test.ts`, qui crée des bundles en mémoire, a été exclu
  conformément au mandat (11 cas). La première exécution a eu un délai dépassé
  dans `planDesTitres.test.tsx` ; le cas a réussi isolément et la reprise
  complète a réussi avec deux workers. `--configLoader runner` a évité
  l'écriture de configuration dans le `node_modules` lié hors de l'arbre.
- `npx tsc --noEmit` et Ruff : réussis. `npm run lint` : 0 erreur et 27
  avertissements dans des fichiers non modifiés par cette passe.
