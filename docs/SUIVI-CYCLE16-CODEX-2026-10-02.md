# Cycle 16 Codex — ouvert le 2 octobre 2026

Cycle distinct ouvert normalement à 12:07:46 UTC, depuis le commit documentaire
`8bc700115794dea9909777e69d275e62c26b2db2` sur la branche `codex/cycle-16`.
Le cycle 15 est clôturé normalement ; son reçu final est
`.app-loop/cycles/15/reprise/release-go/final-sync-root/receipt.json`.
Ses preuves historiques, ses 34 corrections et ses 7 754 tests distincts restent
rattachés à leurs versions. Les quatre messages Discord ne sont pas republiés.

Ludo a autorisé le temps nécessaire au cycle 16 le 2 octobre à 11:54:21 UTC
(message `Sentinel_ba1d5c1be3788191b1d26f9890bbbb6d`). Le budget opérationnel
séparé est de 48 heures, avec les plafonds de modèles documentés dans
`.app-loop/cycles/16/budget-opening-receipt.json`. Les compteurs d'usage Codex
sont des estimations explicitement nommées ; aucun token Claude n'est inventé.

## Instrument et accès

L'adaptation locale approuvée à 12:21:38 UTC
(`Sentinel_ae44438e89e48191b98d3bae78bad1c4`) reconnaît le compteur du modèle
réel pour quitter MAP. Couverture complète, contrôle zéro tokens et toutes les
autres portes restent conservés. Le script Claude canonique est inchangé.
Source, diff, dix comparaisons synthétiques et autorisation sont conservés sous
`.app-loop/cycles/16/proposition-compatibilite-codex` et `outils`.
Le compteur historique est resté à 23 ; aucun nouveau forçage.

La pile neuve utilise un HOME et des données privés, sous
`/private/tmp/therese-c16-codex-runtime-cca75zry`. Le backend hors ligne est
sur 17493, le frontend sur 5173. Le premier choix 1440 a été refusé par
l'origine d'authentification ; cette tentative est conservée, sans modification
de la liste des origines du produit. L'instrument écran a une copie qualifiée
pour les deux ports choisis, gardant le refus de 17293 et des sorties réseau.
L'accès Chrome natif a immobilisé l'outil environ 28 minutes ; le contrôle a
ensuite abouti dans une fenêtre Chrome Invité du Mac, sur l'accueil avec
« Moteur actif » et un état vide cohérent avec le profil neuf.

Les cinq instruments de base et la couverture écran ont passé leurs témoins
rouges/verts propres au cycle 16. Reçu de consolidation :
`.app-loop/cycles/16/calibration-accepted.json` ; summary passé :
`.app-loop/cycles/16/reprise/runtime/all-20261002T130232.405203Z/calibration-summary.json`.
Une nouvelle calibration reste obligatoire après la modification visuelle.

## Défauts reproduits et correctifs ciblés

| Fiche | Déclencheur et résultat du correctif | Preuve avant / après |
| --- | --- | --- |
| B-1769 | La réponse tardive de A composait à B le texte de A. Compte, message, ouverture et appel courant gardent désormais le résultat utilisable ; erreurs/finally obsolètes sont ignorés. Aucun envoi exercé. | `lecteur-interface/contamination-rouge.xml`, `reparation-interface/production-cibles.xml` |
| B-1770 | Une réponse de sauvegarde remettait de-DE malgré une saisie it-IT admise pendant l'attente. Les nouvelles saisies restent affichées et à enregistrer ; reset/import concurrents sont retenus. | `lecteur-interface/export-rouge.xml`, `reparation-interface/production-cibles.xml` |
| B-1771 | Trois noms de callbacks du test modal ne correspondaient pas au hook. Le test corrigé est vert sur le hook sain et rouge sur une copie laissant t/p/o traverser le dialogue. | `lecteur-interface/shortcut-pouvoir-echec.xml`, `reparation-interface/shortcut-power-receipt.json` |
| B-1772 | Après remplacement de la base et de sa clé par B, le cache gardait A. L'instance existante est invalidée sans IO avant réouverture, y compris après retour arrière. | `reproduction-securite/receipt.json`, `reparation-cle/ast-vert-receipt.json`, `reparation-cle/vert-voisins.xml` |
| B-1773 | DELETE réussi puis GET rejeté produisait une notification de charte restaurée avec l'ancienne valeur. La relecture rend désormais son résultat ; l'échec est expliqué à l'écran. | `lecteur-interface/relecture-correctifs/complement.xml`, `reparation-interface/production-cibles.xml` |
| B-1686 (historique repris) | Une annulation à l'un des deux await sautait les nettoyages et la finalisation tardive de l'archive de sécurité. La finalisation synchrone précède les await, sans doubler celle des handlers ; un finally interne protège reprise chat, sortie de maintenance et temporaire. L'annulation remonte toujours. | `reproduction-annulation/rouge.stdout`, `safety-memory/rouge.stdout`, `reparation-annulation/safety-regression-v2/receipt.json` |

Les chemins du tableau sont relatifs à `.app-loop/cycles/16/`. Les premiers
contrôles ciblés couvrent 12 cas frontend et 37 backend, dont cinq nouveaux
contrôles mémoire B-1772. Ils ne s'additionnent pas aux répétitions ni aux
futures suites complètes. Les deux lecteurs ont relu séparément le diff et les
limites. La relecture a trouvé B-1773 avant stabilisation.

## Limites et prochaines portes

La reproduction HTTP complète de restauration entre profils a été refusée par
la revue automatique pour un risque de cybersécurité signalé. Elle n'a pas été
exécutée. Le témoin conservé exécute la source extraite par AST et SQLCipher
réel, avec archive ancienne `.tar.gz`, probe d'init_db et dépendances annexes
factices. Il n'atteste pas une restauration TestClient entre profils, une archive
chiffrée par passphrase ni un trousseau réel. Les contrôles unitaires mémoire
et les tests voisins restent distincts de ce témoin.

À cette étape : correctifs ciblés appliqués, portes complètes, carte différentielle,
recalibration et deux rondes indépendantes encore à achever. Aucun plateau du
cycle 15 n'est recyclé. Les dettes différées historiques restent documentées.
Le profil réel et le port 17293 ne sont pas utilisés par le cycle 16 ; l'incident
natif du cycle 15 reste conservé, sans affirmer l'intégrité globale de ce profil.
La 0.77.1 est signée ad hoc ; aucune notarisation attestée, updater N vers N+1
non exercé. Toute nouvelle publication ou annonce Discord exige un GO propre
au cycle 16.
