# Cycle 20 : restes du chat

Travail effectué dans l'arbre `gpt/c20-restes-chat`, sans commit ni push. Les
tests utilisent des données temporaires et des fournisseurs simulés. Une garde
de test interdit l'ouverture de sockets réseau IP.

| ID | Verdict | Test de comportement | Échec observé avant correction | Correctif |
| --- | --- | --- | --- | --- |
| B-2031 | `confirme` | `tests/test_c20_b2031_texte_diffuse_annulation.py::test_le_partiel_enregistre_correspond_au_texte_relaye` | `E   AssertionError: assert ['Dernier morceau produit.'] == []` | non commité |
| B-2032 | `confirme` | `tests/test_c20_b2032_reperes_agenda.py::test_la_mention_suit_les_reperes_reels_et_la_lecture_demandee` | `E       AssertionError: assert '- 09h : Réun...t pas de lui.' == '- 09h : Réun...retien fictif'` | non commité |

Pour B-2031, les deux variantes étaient rouges : sans texte relayé, le morceau
produit était quand même enregistré ; après un premier morceau relayé, le texte
enregistré contenait également le dernier morceau non relayé. Le test vérifie la
réponse SSE et le contenu en base. Le wrapper est utilisé par l'endpoint
`POST /api/chat/send` et appelle le producteur réel. Le correctif transmet au
producteur la liste des morceaux de texte effectivement relayés, utilisée pour
enregistrer le partiel lors de l'arrêt.

Pour B-2032, 18 des 32 variantes étaient rouges : numéros de point et dates
impossibles, durées présentées sur deux lignes, et lecture explicite associée à
une rédaction. Les tests contrôlent la réponse et le contenu en base, en flux et
hors flux. La détection est appelée par les deux voies de l'endpoint de chat.
Les dates numériques sont validées ; une durée seule ne suffit pas à former
une ligne de rendez-vous ; un verbe de rédaction ne masque plus une demande de
lecture explicite. Aucun test existant n'a été affaibli ou modifié.

Aucun candidat n'est classé `regle_a_trancher`.

## Portes ciblées

- Backend : **162 réussis, 0 échec, 0 erreur, 0 ignoré**. Noms des échecs :
  aucun. Résultat lu dans `/tmp/restes-chat-pytest.xml`. Fichiers exécutés :
  `tests/test_c20_b2031_texte_diffuse_annulation.py`,
  `tests/test_c20_b2032_reperes_agenda.py`,
  `tests/test_chat_annulation_reelle.py`, `tests/test_chat_traitement.py`,
  `tests/test_b1795_agenda_selection_stream.py`,
  `tests/test_b1797_agenda_sans_outil.py`,
  `tests/test_c20_b1799_recherche_vide.py`,
  `tests/test_c20c_budget_historique.py` et
  `tests/test_agenda_lecture_et_reperes.py`.
- Ruff, `check --no-fix src/backend tests` : **0 erreur**, code 0.
- Vitest : **0 test exécuté**, aucun fichier de test ni composant frontend
  modifié ; la suite complète n'a pas été lancée.
- TypeScript, `npx tsc --noEmit` : **0 erreur**, code 0. Une première tentative
  a échoué avant l'analyse avec une erreur macOS de trousseau et le code 139 ;
  la relance a réussi en neutralisant la configuration npm utilisateur.
- Lint frontend, `npm run lint` : **0 erreur et 27 avertissements**, code 0.
  Aucun fichier frontend n'a été modifié dans ce lot.

## Remédiation de la relecture, passe 1

Les deux constats sont confirmés. Les tests ont été écrits avant les correctifs
et exécutés isolément ; ils vérifient la réponse exacte et le message assistant
enregistré, en flux et hors flux.

- **P1 — horaires et tableaux.** Le test
  `test_horaires_et_tableaux_sans_separateur_conservent_la_reserve` couvre les
  horaires sans séparateur, en gras, les tableaux avec l'heure dans chacune des
  deux colonnes, et les durées. Avant correction, le cas isolé sans flux a donné :
  `E   AssertionError: assert '- 09:00 Réun...:00 Entretien' == '- 09:00 Réun...t pas de lui.'`
  La détection accepte ces horaires et analyse les tableaux convertis en puces,
  sans changer le texte du flux. La relecture du premier correctif a également
  révélé un faux positif sur les tableaux de durées ; les deux variantes ont été
  ajoutées avant de le corriger. Leur échec isolé comprenait :
  `E   AssertionError: assert '- Durée : 3h...t pas de lui.' == '- Durée : 3h...vité : Trajet'`
- **P2 — explication ou rédaction seule.** Le test
  `test_explication_ou_redaction_seule_ne_demande_pas_la_lecture` couvre les
  exemples de la relecture, d'autres emplois explicatifs et nominaux, et des
  instructions qui associent lecture et rédaction. Avant correction, huit des
  seize variantes alors présentes échouaient avec :
  `E   AssertionError: assert '- 09h : Réun...t pas de lui.' == '- 09h : Réun...retien fictif'`
  Le filtre distingue ces emplois des instructions de lecture et examine les
  instructions suivantes. Un test ajouté après relecture préserve également une
  lecture précédée de « Pour demain » ; il échouait avant son ajustement :
  `E   AssertionError: assert '- 09h : Réun...retien fictif' == '- 09h : Réun...t pas de lui.'`

Après chaque correctif, les deux appelants ont été relus et les tests voisins
ont été lancés. Porte finale sur les neuf fichiers backend listés ci-dessus :
**212 réussis, 0 échec, 0 erreur, 0 ignoré**, XML lu dans
`/tmp/restes-chat-r1.xml`. Ruff `check --no-fix src/backend tests` : **0 erreur**.
La première invocation de Ruff n'a pas démarré à cause de la valeur `1` de
`RUFF_NO_CACHE` ; la relance avec `true` a réussi. Aucun fichier frontend modifié,
aucune suite complète lancée.

Les tests utilisent des fournisseurs et transports factices, une garde réseau
et un répertoire de données temporaires sous `/tmp`. Le bac à sable refusant
l'envoi sur les sockets Unix de réveil d'`asyncio`, une adaptation temporaire
les remplace par des tuyaux anonymes pour les tests ; la garde continue de
bloquer le réseau IP et les chemins interdits. Les liens non suivis `.venv` et
`src/frontend/node_modules` étaient déjà présents au début et n'ont pas été modifiés.

## Limites

La reconnaissance des demandes et des horaires reste fondée sur des motifs :
un horaire isolé tel que `3h` est ambigu et n'est pas compté comme rendez-vous
sans contexte. D'autres formulations peuvent échapper à la détection. Aucun
modèle réel ni service en ligne n'a été appelé.

Le test d'annulation compare le texte remis par le générateur SSE à la base.
En cas de coupure réseau après cette remise, le serveur ne reçoit pas d'accusé
de réception prouvant que le client a effectivement affiché chaque morceau.
