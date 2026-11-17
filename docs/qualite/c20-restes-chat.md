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

## Remédiation de la relecture, passe 2

Les quatre constats sont confirmés. Les variantes ajoutées à
`tests/test_c20_b2032_reperes_agenda.py` ont été lancées isolément avant chaque
correctif. Elles comparent la réponse exacte et le message assistant enregistré,
en flux et hors flux.

- **1 — plages horaires après un libellé ou dans un tableau.** Les six variantes
  isolées étaient rouges. Ligne d'échec :
  `E   AssertionError: assert '- Réunion cl...: 14:00–15:00' == '- Réunion cl...t pas de lui.'`
  La détection reconnaît une plage complète après le libellé, notamment dans
  chacune des colonnes d'un tableau et avec les heures en gras.
- **2 — lecture après une explication.** Quatre des huit variantes isolées
  étaient rouges lorsque le repère temporel précédait le verbe. Ligne d'échec :
  `E   AssertionError: assert '- 09h : Réun...retien fictif' == '- 09h : Réun...t pas de lui.'`
  Le filtre explicatif examine la proposition après « puis » ou « ensuite » ;
  les deux positions de « demain » et les explications seules restent testées.
- **3 — tableaux de durées.** Huit des dix variantes isolées étaient rouges pour
  les en-têtes en gras, au pluriel ou en italique. Ligne d'échec :
  `E   AssertionError: assert '- **Durée** ...t pas de lui.' == '- **Durée** ...vité : Trajet'`
  Les libellés sont normalisés pour la détection, sans modifier le texte affiché.
  La relecture a aussi révélé une puce étoilée devant un libellé en gras : deux
  de ses quatre variantes étaient rouges, avec la ligne
  `E   AssertionError: assert '* **Durée** ...t pas de lui.' == '* **Durée** ...*Durée** : 2h'`.
  La normalisation conserve désormais la puce ; un tableau mêlant durées et vrais
  horaires et une puce horaire restent testés.
- **4 — « liste » nominale avec adjectifs coordonnés.** Six des douze premières
  variantes isolées étaient rouges. Ligne d'échec :
  `E   AssertionError: assert '- 09h : Réun...t pas de lui.' == '- 09h : Réun...retien fictif'`
  Le contrôle nominal conserve les adjectifs coordonnés. Une relecture a ajouté
  des adjectifs intensifiés et une seconde coordination ; quatre des six variantes
  correspondantes étaient rouges avant leur ajustement. Elle a également mis en
  évidence une régression sur les ordres « et après », « et vite » et « et de
  suite » : les six variantes étaient rouges avec la ligne
  `E   AssertionError: assert '- 09h : Réun...retien fictif' == '- 09h : Réun...t pas de lui.'`.
  Les ordres de lecture coordonnés à une rédaction sont conservés.

Après chaque correctif, les appelants avec et sans flux ont été relus et les
tests voisins ont été exécutés. Porte finale sur les neuf fichiers backend listés
plus haut : **266 réussis, 0 échec, 0 erreur, 0 ignoré** ; le XML
`/tmp/restes-chat-r2.xml` a été lu et ne contient aucun échec. Ruff
`check --no-fix src/backend tests` : **0 erreur**. Aucun fichier frontend modifié
et aucune suite complète lancée. Les mêmes garde réseau et adaptation temporaire
du réveil `asyncio` que pour la passe 1 ont été utilisés.

## Remédiation de la relecture, passe 3

Les trois constats sont confirmés. Les variantes ont été ajoutées à
`tests/test_c20_b2032_reperes_agenda.py` et exécutées isolément avant chaque
correction. Elles comparent le texte reçu et le message assistant enregistré,
en flux et hors flux ; les tests existants n'ont pas été affaiblis.

- **1 — listes et bornes en gras.** Huit des dix variantes isolées étaient
  rouges pour les listes numérotées et les tableaux avec chaque borne en gras ;
  les deux variantes de durées numérotées passaient déjà. Ligne d'échec :
  `E   AssertionError: assert '1. Réunion c...etien : 14:00' == '1. Réunion c...t pas de lui.'`
  La détection accepte les libellés numérotés et normalise chaque borne pour
  l'analyse, sans modifier le texte affiché. La relecture a ajouté la notation
  Markdown `__` : les deux variantes échouaient avant leur correction, avec :
  `E   AssertionError: assert '- Rendez-vou...0__–__15:00__' == '- Rendez-vou...t pas de lui.'`
- **2 — ordre après rédaction.** Huit des quatorze variantes isolées étaient
  rouges, notamment avec « et enfin » et « et à présent ». Ligne d'échec :
  `E   AssertionError: assert '- 09h : Réun...retien fictif' == '- 09h : Réun...t pas de lui.'`
  La construction verbale avec objet direct est distinguée de la liste
  nominale ; les variantes nominales et l'adverbe après le verbe sont testés.
- **3 — instruction citée.** Vingt des vingt-six variantes isolées étaient
  rouges. Ligne d'échec :
  `E   AssertionError: assert '- 09h : Réun...t pas de lui.' == '- 09h : Réun...retien fictif'`
  Le texte cité à expliquer ou résumer est écarté de l'analyse, y compris ses
  dates et actions, tandis qu'une lecture indépendante reste prise en compte.
  Les tests couvrent plusieurs guillemets, les apostrophes et la lecture d'un
  objet ou d'une date cités. La relecture a trouvé dix variantes rouges sur
  seize pour des objets ou dates cités dans une lecture indépendante :
  `E   AssertionError: assert '- 09h : Réun...retien fictif' == '- 09h : Réun...t pas de lui.'`
  Elle a aussi trouvé six variantes rouges sur six pour « la liste » ou « je
  consulte » dans l'explication, puis quatre sur six pour une lecture décrite
  par un tiers ; leur ligne d'échec était celle du faux positif ci-dessus.

Après chaque correction, les deux appelants ont été relus et les tests voisins
exécutés. La porte finale réunit les neuf fichiers backend listés dans les
portes ciblées ci-dessus et `tests/test_F11_recaps_lisibles.py` : **353 réussis,
0 échec, 0 erreur, 0 ignoré**. Le XML `/tmp/restes-chat-r3.xml` a été lu.
Ruff `check --no-fix src/backend tests` : **0 erreur**. Aucune suite complète
ni vérification frontend n'a été lancée ; aucun fichier frontend n'a changé.
Les tests ont utilisé les mêmes garde réseau et adaptation temporaire du réveil
`asyncio` que pour les passes précédentes.

## Limites

La reconnaissance des demandes et des horaires reste fondée sur des motifs :
un horaire isolé tel que `3h` est ambigu et n'est pas compté comme rendez-vous
sans contexte. D'autres formulations peuvent échapper à la détection. Aucun
modèle réel ni service en ligne n'a été appelé.

Le test d'annulation compare le texte remis par le générateur SSE à la base.
En cas de coupure réseau après cette remise, le serveur ne reçoit pas d'accusé
de réception prouvant que le client a effectivement affiché chaque morceau.

## Remédiation de la relecture, passe 4

Les trois constats de B-2032 sont confirmés et corrigés (issue **a**). Chaque
test a été ajouté puis exécuté seul avant son correctif. Les nouvelles variantes
vérifient la réponse exacte et le message enregistré, en flux et hors flux.

| Constat | Issue | Test et échec constaté avant correction |
| --- | --- | --- |
| 1 — lecture coordonnée et citation | a | `test_citation_apres_propositions_coordonnees` : `E   AssertionError: assert '- 09h : Réun...retien fictif' == '- 09h : Réun...t pas de lui.'` |
| 2 — libellé en gras ou complément | a | `test_libelles_en_gras_et_complements_apres_horaire` : `E   AssertionError: assert '- **Réunion ...etien :** 14h' == '- **Réunion ...t pas de lui.'` |
| 3 — instruction citée à écrire ou reformuler | a | `test_instructions_citees_a_ecrire_ou_reformuler` : `E   AssertionError: assert '- 09h : Réun...t pas de lui.' == '- 09h : Réun...retien fictif'` |

1. La lecture coordonnée conserve les objets et dates cités après une rédaction
   ou un résumé, sans confondre la proposition avec une liste nominale. Le cas
   exact du relecteur échouait avant correction. Les 20 variantes ajoutées
   comprennent les objets et dates cités, les dates numériques, les adverbes
   et des listes nominales à ne pas interpréter comme des ordres.
2. Les libellés dont le deux-points est en gras sont normalisés pour l'analyse,
   et un complément après l'heure est accepté. L'autre exemple du relecteur
   échouait aussi avec :
   `E   AssertionError: assert '- Réunion : ... 14h, salle B' == '- Réunion : ...t pas de lui.'`
   Huit des 14 variantes isolées étaient rouges ; les durées en gras ou suivies
   d'un complément restent exclues.
3. L'analyse des citations s'applique aussi à « rédige », « écris » et
   « reformule », tout en conservant les lectures indépendantes et leurs objets
   ou dates cités. Dix-huit des 32 variantes isolées étaient rouges avant
   correction, notamment les deux phrases signalées par la relecture.

Les appelants et tests voisins ont été vérifiés après les correctifs :
**311**, puis **325**, puis **412 réussis**. La porte finale sur les neuf
fichiers backend énumérés plus haut indique **0 échec, 0 erreur, 0 ignoré** ;
le XML `/tmp/restes-chat-r4.xml` a été lu. Ruff
`check --no-fix src/backend tests` : **0 erreur**. Aucun fichier frontend modifié
et aucune suite complète lancée. La garde réseau et les fournisseurs simulés
ont été utilisés pour les tests.
