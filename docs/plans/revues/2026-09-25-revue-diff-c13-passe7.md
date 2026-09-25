# Revue ciblée, cycle 13, passe 7 (d6f4ba19)

Relecteur : rôle Claude indépendant (da-relecteur), environ 243 000 tokens. Cibles : la matrice annulation × étape de la purge et de la restauration, et B-1281. Verdict : NO-GO, 6 constats (1 P2, 5 P3).

## Tri

Seuil convenu avant la passe (avis) : un P2 de plus sur la purge après les deux règles de conception = arrêter de rapiécer et cadrer un chantier. Il est atteint : les constats 1, 3 et 5 rejoignent B-1136, B-1265 et B-1266 dans `docs/plans/2026-09-25-chantier-mise-au-repos-ecritures-de-fond.md`.

| Constat | Bug | Suite donnée |
|---|---|---|
| 1 (P2, échec ou annulation après l'attente) | B-1291 | différé au chantier |
| 2 (P3, vecteur de profil orphelin après le 200) | B-1292 | corrigé : relecture du profil après son vecteur, comme les fiches |
| 3 (P3, drapeau des fiches retombé trop tôt) | B-1293 | différé au chantier |
| 4 (P3, message « Effacement » en restauration) | B-1294 | corrigé : message neutre |
| 5 (P3, begin() sans plafond) | B-1295 | différé au chantier |
| 6 (P3, sophie-02 : recherche retapée) | B-1296 | corrigé : clé sur le numéro de réponse |

B-1281 : aucune régression mesurée, et son test est un vrai garde (rouge 5 fois sur 5 sur le code d'avant).

## Rapport brut et matrice

1. P2 - src/backend/app/routers/data.py:602-629 (et :633-700, :1556-1624) - L'invariant I2 est rompu quand l'opération échoue ou est annulée APRÈS le retour de `_arreter_les_travaux_de_fond`. B-1283 ne relance les fiches rendues que si l'attente elle-même échoue (data.py:623-626). Au-delà, la liste `rendues` est perdue, et la génération du profil avancée à l'étape 3 rend définitive la renonciation d'un profil enregistré pendant cette étape. Le titre de B-1283 (« les fiches laissées en route par l'arrêt reprennent si l'opération n'a pas lieu ») n'est donc pas tenu sur quatre chemins mesurés : la purge annulée après le retour de l'arrêt, pendant le journal d'audit et avant la première suppression (la fenêtre non couverte va jusqu'au commit), la restauration annulée pendant `close_db()`, la restauration en 500 « pendant l'archive de sécurité (restauration annulée) » (disque plein), et la restauration en 500 après une extraction en échec suivie d'un retour arrière réussi, qui répond « Données restaurées à l'état précédent. » (data.py:1383, détail complet relevé en run4) - mesuré (scratchpad/p7, fiches Fiche1 à Fiche3 en cours d'indexation, Fiche1 en vol pendant l'arrêt, rejoué en run3 avec le même résultat) : sur les quatre chemins, `sql_contacts ['Chat1','Fiche1','Fiche2','Fiche3']`, index final `['Chat1','Fiche1','ProfilInitial']`, `sql_non_indexes ['Fiche2','Fiche3']` ; drapeaux, suspension, verrou et maintenance sont bien retombés. Profil enregistré pendant l'étape 3, puis purge annulée pendant le journal d'audit : `sql_profil 'ProfilTardif'`, index `'ProfilInitial'`, donc « qui suis-je ? » rend l'ancien nom, et `sql_non_indexes ['Fiche2','Fiche3','ProfilTardif']`. Aucune route ne réindexe les fiches : `_lancer_l_indexation` n'est appelée que par les imports et par les deux relances (memory.py:128-153), et rien ne réindexe au démarrage (grep « reindex » : seulement les conversations) - `_arreter_les_travaux_de_fond` doit rendre `rendues` à l'appelant. La purge et la restauration enveloppent tout ce qui suit l'arrêt dans un `try/except BaseException`, qui couvre aussi les chemins 500, pour relancer les fiches rendues et réindexer le profil courant, relu en base, dès que l'opération n'aboutit pas. Contre-épreuves à ajouter : annulation pendant `close_db`, `_create_archive` en échec, extraction en échec avec retour arrière réussi, annulation entre l'arrêt et le commit, avec une assertion sur l'index et pas seulement sur les lignes SQL.
2. P3 - src/backend/app/services/user_profile.py:326-351 (et src/backend/app/routers/data.py:633-700) - I1 est rompu de façon durable. Un profil enregistré entre la fin de l'étape 3 et la première suppression SQL reçoit une génération neuve, donc il n'y a pas de renonciation. Son vecteur arrive après la purge Qdrant et après le 200, puis rien ne le retire. Après « supprimées conformément au RGPD », l'index garde owner_profile (nom, courriel, entreprise, rôle), alors que la ligne Preference est effacée. Les fiches se relisent en base après le vecteur et le retirent si la fiche a disparu (memory.py:196-201) ; le profil ne le fait pas. La fenêtre est étroite : c'est le point de sauvegarde et le refresh de `log_activity` - mesuré sans élargir la fenêtre (sauvegarde lancée à la sortie exacte de l'étape 3), rejoué en run3 : `issue 200` à 1,843 s, journal `[1.841, PURGE] [2.324, add, ProfilTardif]`, `sql_profil None`, index final `['ProfilTardif']` - dans `_indexer_en_arriere_plan`, relire la Preference après `_embed_profile` et retirer owner_profile si elle a disparu, comme `_indexer_une_fiche`. Autre voie : avancer à nouveau la génération sous le verrou après le commit de la purge et avant la purge Qdrant, ou refuser les enregistrements de profil pendant la purge, comme B-1276 le fait pour le chat.
3. P3 - src/backend/app/routers/memory.py:227-230 - I1 est rompu de façon transitoire. Le drapeau d'arrêt retombe à la fin de l'étape 2, dans le `finally` de `arreter_les_indexations_de_fiches`. Une fiche importée pendant l'étape 3, ou avant les suppressions, est donc indexée librement : son vecteur entre dans l'index après le 200, puis la relecture le retire (memory.py:196-201). Si ce retrait échoue, l'exception est avalée (memory.py:299) et le point reste - mesuré (purge, étape 3, événement c) : PURGE à 1,842 s, 200 à 1,844 s, `[2.026, add, Import1]` puis `[2.030, del, Import1]`, index final vide ; même trace dans le cas « après l'étape 3 » - garder le drapeau posé jusqu'à la fin de l'opération : c'est l'appelant qui le lève, dans son `finally`, ce qui lui donne aussi la main pour le point 1.
4. P3 - src/backend/app/services/memory_tools.py:1254-1262 - B-1284 réutilise le verrou de la purge sans en adapter le message. Pendant une restauration, le chat répond « Effacement de toutes les données en cours : rien n'a été créé. », ce qui est faux et alarmant pour quelqu'un qui restaure - mesuré (restauration, étapes 1, 2 et 3 et `close_db`, événement c) : `{"success": false, "error": "Effacement de toutes les données en cours : rien n'a été créé. ..."}` dans les quatre cellules - formulation neutre (« Une opération sur tes données est en cours (effacement ou restauration) : rien n'a été créé »), ou motif passé à `suspendre_les_creations_du_chat`.
5. P3 - src/backend/app/services/maintenance.py:61-62 (et src/backend/app/routers/data.py:1533) - `begin()` échappe au plafond B-1277. Il attend sans limite les requêtes suivies, et pendant ce temps le mode maintenance refuse toute l'API en 503. L'écran de restauration n'a pas de délai (src/frontend/src/services/api/data.ts:115, `timeoutMs: null`). C'est justement la situation que B-1277 voulait borner (« l'écran n'a plus de délai ; le serveur plafonne donc ses attentes »). Il reste à vérifier quelles requêtes suivies peuvent durer longtemps, par exemple l'indexation d'un gros fichier - mesuré (plafond abaissé à 0,3 s, une requête suivie tenue 2,5 s) : première étape atteinte à 2,536 s, `maintenance_active_pendant_begin: true`, durée totale 2,806 s avant un 503 à l'étape 2 - soumettre l'attente de `begin()` au même plafond. Au-delà, `_active = False`, puis 503 « rien n'a été modifié ».
6. P3 - src/frontend/src/components/prompts/PromptLibrary.tsx:482-485 - B-1281 ne cause aucune régression : sophie-02 et les autres parcours sont identiques avant et après. En revanche, sophie-02 n'est pas entièrement réglé (défaut préexistant). Si l'on retape la même requête (même texte une fois nettoyé, par exemple avec une espace finale), ni la clé (`resultsQuery` inchangée) ni `defaultOpen` (toujours vrai) ne changent. Une catégorie repliée dans les résultats reste donc repliée, et l'écran annonce un résultat qu'il ne montre pas - mesuré (T4, au HEAD comme avec l'ancien `useEffect`) : `appels_recherche 2`, Email `aria-expanded "false"`, en-tête `1 résultat pour "relance"`, `prompt_visible false` - faire suivre à la clé un compteur de recherches abouties plutôt que le texte, ou rouvrir sur chaque nouvelle réponse de recherche.

Matrice mesurée (scratchpad/p7/test_zz_matrice_p7.py et test_zz_cibles_p7.py ; mesures dans mesures-matrice-run1.jsonl, mesures-cibles-run1.jsonl, mesures-run3.jsonl et mesures-run4.jsonl ; chaque cellule vérifie la trace d'entrée et de sortie des étapes)

| Op. | Étape | Év. | Issue | Invariant | Mesure clé |
|---|---|---|---|---|---|
| Purge | 1 gestes | a | annulée | I2 OK | tout indexé (Chat1, Fiche1-3, ProfilInitial), état propre |
| Purge | 1 | b | 503 | I2 OK | idem |
| Purge | 1 | c | 200 | I1 OK | chat refusé, import et profil effacés, aucun ajout après le 200, index vide |
| Purge | 2 fiches | a | annulée | I2 OK | Fiche2 et Fiche3 indexées (2,42 et 3,63 s) par la tâche d'origine, le drapeau étant retombé |
| Purge | 2 | b | 503 | I2 OK | idem |
| Purge | 2 | c | 200 | I1 OK | aucun ajout après le 200, index vide |
| Purge | 3 profil | a | annulée | I2 OK | Fiche2 et Fiche3 relancées (2,71 et 3,93 s), profil indexé |
| Purge | 3 | b | 503 | I2 OK | idem |
| Purge | 3 | c | 200 | I1 KO transitoire | Import1 ajouté puis retiré après le 200 (point 3) ; profil tardif renoncé puis effacé |
| Purge | après 3 (journal, avant suppressions) | a | annulée | I2 KO | Fiche2 et Fiche3 jamais indexées ; profil de l'étape 3 : SQL ProfilTardif, index ProfilInitial (point 1) |
| Purge | après 3 (journal, avant suppressions) | c | 200 | I1 KO durable | ProfilTardif orphelin dans l'index, même sans élargir la fenêtre (point 2) |
| Restau. | 1 | a / b | annulée / 503 | I2 OK | tout indexé, maintenance levée, suspension à 0 |
| Restau. | 1 | c | 200 | I1 OK | chat refusé avec le message « Effacement » (point 4) ; import et profil : 503 maintenance ; aucun ajout après la réponse |
| Restau. | 2 | a / b | annulée / 503 | I2 OK | Fiche2 et Fiche3 indexées par la tâche d'origine |
| Restau. | 2 | c | 200 | I1 OK | comme étape 1 c |
| Restau. | 3 | a / b | annulée / 503 | I2 OK | Fiche2 et Fiche3 relancées, profil indexé |
| Restau. | 3 | c | 200 | I1 OK | comme étape 1 c |
| Restau. | 4 begin() | a | annulée | I2 OK | maintenance levée, aucune suspension posée, tout indexé |
| Restau. | 4 begin() | b | sans plafond | écart | begin() attend 2,5 s au-delà d'un plafond de 0,3 s, maintenance active (point 5) ; ensuite 503 à l'étape 2, I2 OK |
| Restau. | 4 begin() | c | 200 | I1 OK | création du chat acceptée (pas encore suspendue), attendue à l'étape 1, puis remplacée par la restauration |
| Restau. | 4 close_db | a | annulée | I2 KO | Fiche2 et Fiche3 jamais indexées (point 1) |
| Restau. | 4 close_db | b | sans objet | - | le plafond ne couvre plus cette étape |
| Restau. | 4 close_db | c | 200 | I1 OK | chat refusé (message « Effacement »), aucun ajout après la réponse |
| Restau. | 4 extraction | a / b / c | sans objet | - | lecture : code synchrone dans la boucle, rien ne peut s'intercaler (non mesuré) |
| Restau. | 4 archive de sécurité | 500 | 500 | I2 KO | Fiche2 et Fiche3 jamais indexées (point 1) |
| Restau. | 4 extraction en échec | 500 | 500 « Données restaurées à l'état précédent. » | I2 KO | Fiche2 et Fiche3 jamais indexées (point 1) |

Toutes les cellules : `_CREATIONS_SUSPENDUES 0`, `_ARRET_DES_INDEXATIONS false`, `_FICHES_RENDUES []`, `maintenance_mode.active false`, `_VERROU_INDEXATION.locked() false`. Pour la restauration en 200, l'index factice n'est pas remplacé par l'archive : I1 y est jugé sur les seuls ajouts postérieurs à la réponse (aucun).

Cible 2 (B-1281, hors dépôt : greffon vite `load` dans scratchpad/p7/front, le fichier suivi n'est pas touché)

| Cas | HEAD | Ancien `useEffect` (sabotage) |
|---|---|---|
| PromptLibrary.clicAvantEffets.test.tsx | vert 6/6 | rouge 5/5 (et 1/1 en run complet) : c'est un vrai garde |
| cycle6 sophie-02 | vert 6/6 | rouge 1/6 (l'instabilité reproduite) |
| T1 : Email repliée, puis recherche, puis vidage | ouverte pendant la recherche ; après vidage, Email ouverte et Vente fermée | identique |
| T2 : repliée dans les résultats, puis vidage | Email ouverte | identique |
| T3 : Vente ouverte à la main, recherche, vidage | Vente refermée (état par défaut, remontage par la clé) | identique |
| T4 : même requête retapée | Email repliée, « 1 résultat », prompt invisible (point 6) | identique |
| Bloc d'ajustement retiré en entier | 10/10 tests PromptLibrary verts : le bloc n'est gardé par aucun test ; aucun chemin connu ne change `defaultOpen` sans changer la clé | - |
| Autre usage de `defaultOpen` | aucun : `CategoryAccordion` est local ; `AdvancedTab.tsx:23-30` a son propre `CollapsibleSection`, que le diff ne touche pas | - |

VERDICT : NO-GO
Estimation : environ 230 000 tokens consommés.
