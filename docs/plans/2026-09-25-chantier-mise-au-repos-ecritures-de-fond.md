# Chantier : mise au repos des écritures de fond

Rédigé le 25/09/2026 (cycle 13), à arbitrer par Ludo.

## Le problème

Deux opérations touchent à TOUTES les données :

- « Effacer toutes mes données » (purge RGPD) ;
- la restauration d'une sauvegarde.

Pendant ce temps, trois familles de travaux écrivent en arrière-plan :

- les créations lancées depuis le chat (contact, projet) ;
- l'indexation vectorielle des fiches importées ;
- l'indexation du profil.

Il faut ajouter l'indexation de fichiers et la synchro de dossiers, qui ne sont pas encore couvertes.

La purge et la restauration doivent tenir deux promesses :

- **I1** : après la réponse 200 d'une purge, plus rien n'arrive dans la base ni dans l'index. C'est l'effacement RGPD.
- **I2** : une opération qui n'aboutit pas (refus 503, annulation, erreur 500) laisse tout intact, lignes ET index. Aucune fiche ni aucun profil enregistré ne reste hors de l'index pour de bon.

## Où on en est

Le mécanisme a grandi par couches, au fil de sept passes de revue adverse du 25/09. Chaque correctif a fermé un cas et en a ouvert un voisin (une réparation sur trois a produit sa propre régression) :

| Couche | Bug | Ce qu'elle fait |
|---|---|---|
| Attente des créations du chat | B-1260, B-1270, B-1276, B-1284 | Suspension des nouvelles créations pendant la purge et la restauration, puis attente de celles en vol, sans jamais les annuler. |
| Arrêt des fiches | B-1222, B-1234, B-1249, B-1255, B-1283 | Drapeau lu entre deux fiches. Les fiches restantes sont rendues puis relancées si l'attente échoue. |
| Arrêt du profil | B-1251, B-1282, B-1292 | Génération avancée sous le verrou ; vecteur retiré si le profil a disparu pendant son calcul. |
| Plafond | B-1277 | 120 s ; au-delà, 503 « rien n'a été modifié ». |

La passe 7, ciblée, a mesuré la matrice étape × événement (annulation, plafond expiré, écriture concurrente). Elle est dans `docs/plans/revues/2026-09-25-revue-diff-c13-passe7.md`.

Toutes les cases de l'attente elle-même sont désormais vertes. Restent **les cas où l'opération échoue APRÈS l'attente** : purge annulée avant son commit, restauration annulée pendant la fermeture des moteurs, archive de sécurité en échec, extraction en échec suivie d'un retour arrière. Dans ces quatre cas, les fiches rendues par l'arrêt ne sont jamais réindexées (B-1291).

## Défauts rattachés (tous différés)

| Bug | Gravité | Constat |
|---|---|---|
| B-1291 | moyenne | Opération échouée ou annulée après l'attente : fiches rendues et profil de l'étape 3 jamais réindexés. |
| B-1293 | faible | Le drapeau d'arrêt retombe à la fin de son étape : une fiche importée ensuite est indexée après le 200, puis retirée. |
| B-1295 | faible | `begin()` (mode maintenance) attend sans plafond les requêtes en cours. |
| B-1266 | faible | Une réponse en flux (chat) libère le mode maintenance dès ses en-têtes. |
| B-1265 | moyenne | La purge n'attend ni l'indexation de fichiers ni la synchro de dossiers. |
| B-1136 | moyenne | La purge efface les travaux sans les annuler. |

Aucun n'efface de données de l'utilisateur. Le pire effet mesuré : des fiches qui ne ressortent plus à la recherche sémantique jusqu'à leur prochaine modification, ou un vecteur transitoire après le 200.

## Conception proposée

Il faut une seule pièce, « la mise au repos », détenue par l'opération du début à la fin, au lieu de trois primitives qui retombent chacune à la fin de leur étape.

1. **Entrée** : la purge ou la restauration ouvre la mise au repos. Celle-ci suspend les créations du chat, les imports, les sauvegardes de profil, les indexations de fichiers et la synchro. Tout reste suspendu jusqu'à la sortie, pas jusqu'à la fin d'une étape (B-1293).
2. **Attente** : tout ce qui est en vol est attendu, sous un plafond unique qui couvre aussi `begin()` (B-1295). Rien n'est annulé en vol.
3. **Sortie** :
   - si l'opération aboutit : rien à relancer, tout a été effacé ou remplacé ;
   - si elle n'aboutit pas, quelle qu'en soit la raison (503, annulation, 500 à n'importe quelle étape) : relance de ce qui a été laissé en route, puis réindexation du profil relu en base (B-1291).
4. **Réponses en flux** : l'admission au mode maintenance est tenue jusqu'à la fin du corps, sous le même plafond, pour ne jamais bloquer la restauration indéfiniment (B-1266).
5. **Fichiers** : l'indexation de fichiers et la synchro de dossiers passent par la même porte (B-1265, B-1136).

Tests d'acceptation : la matrice de la passe 7, étendue aux étapes postérieures à l'attente, écrite dans le dépôt. Chaque case vérifie les lignes ET l'index.

Effort estimé : une demi-journée à une journée en TDD, avec une revue adverse du design AVANT le code (règle `feedback_design_avant_code`) puis une du diff.

## Décision attendue

- **Recommandation : OUI, en chantier dédié avant la prochaine release.** Le rapiéçage étape par étape a atteint sa limite : chaque passe trouve le cas voisin.
- Alternative : livrer en l'état. Les cas restants exigent une annulation ou une erreur précise pendant une purge ou une restauration, et n'effacent rien.
