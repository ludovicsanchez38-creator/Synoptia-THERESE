# Cycle 20 : lot backend-agents

Les cinq défauts confirmés sont corrigés dans l'arbre `gpt/c20-backend-agents`.
Les tests, les correctifs et ce bilan restent non commités ; l'index Git n'a
pas été modifié. Les tests rouges sont conservés pour leur rejeu par
l'orchestrateur sur la base sans correctifs.

| ID | Verdict | Test (chemin::nom) | Ligne d'échec du rouge | Correctif |
| --- | --- | --- | --- | --- |
| B-1818 | regle_a_trancher | `tests/test_mode_cabinet.py::TestLaPolitiqueEstUnique::test_une_conversation_libre_reste_ouverte_meme_en_mode_cabinet` | Sans objet | Sans objet |
| B-1819 | rejete | `tests/test_b1071_pas_de_bascule_locale_vers_le_cloud.py::test_ollama_indisponible_ne_bascule_pas_vers_un_service_en_ligne` | Sans objet | Sans objet |
| B-1824 | confirme | `tests/test_b1824_comptage_generation.py::test_texte_partiel_puis_panne_ne_referme_pas_le_circuit[429]` et `[503]` ; `::test_une_generation_reussie_compte_un_seul_succes` | `AssertionError: assert 0 == 1` pour chaque panne partielle ; `AssertionError: assert 2 == 1` pour le succès | non commité |
| B-1825 | confirme | `tests/test_b1825_mcp_echec_initialisation.py::test_echec_initialisation_arrete_processus_et_lecteurs` ; `::test_annulation_initialisation_arrete_aussi_processus_et_lecteurs` | `AssertionError: Expected 'mock' to have been called once. Called 0 times.` pour chacun | non commité |
| B-1826 | confirme | `tests/test_b1826_mcp_chemin_de_resolution.py::test_le_serveur_ne_remplace_pas_le_chemin_de_resolution[False]` et `[True]` ; `::test_commande_absente_du_chemin_de_l_application_n_est_pas_lancee` | `AssertionError: assert '…/fourni/python3' == '…/fiable/python3'` pour les deux variantes ; `AssertionError: Expected mock to not have been awaited. Awaited 1 times.` pour la commande absente | non commité |
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
- B-1826 : seule la résolution depuis le PATH enrichi de l'application choisit
  l'exécutable, même si la configuration fournit un PATH chiffré ou en clair.
  L'absence de l'exécutable dans ce PATH est une erreur, sans repli vers le
  nom nu susceptible d'être résolu avec le PATH du serveur.
- B-1903 : setup et dictée indiquent la même absence et la même installation
  optionnelle. Les tests vocaux ciblés donnent 22 réussites sur 22.
  Le test existant `tests/test_routers_voice.py::TestVoiceLocalSetup::test_setup_refuse_si_libs_absentes`
  codifiait l'ancien conseil de mise à jour ; il vérifie désormais précisément
  l'absence et la commande d'installation, en conservant le contrôle HTTP 503.
- B-1904 : le Board affiche que la recherche est coupée et transmet toujours
  cette information au conseiller. Les tests ciblés donnent 28 réussites sur 28.

## Portes

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
