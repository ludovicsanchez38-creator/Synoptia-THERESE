# Contre-revue croisée du 15 juillet 2026 (Codex exec + vérification OPT)

Contre-revue lancée par OPT sur demande de Ludo, exécutée par Codex CLI en
lecture seule, puis chaque finding vérifié dans le code par OPT avant d'être
retenu. Verdict Codex brut : NO-GO. Verdict consolidé après vérification :
**NO-GO bêta confirmé** (le verrou était de toute façon fermé), avec un lot de
correctifs cadré ci-dessous.

## Findings confirmés (vérifiés dans le code)

| Sévérité | Où | Constat vérifié | Correctif attendu |
|---|---|---|---|
| BLOQUANT contrat | `PrototypeUnifiedViewCanvas` + `EmailCompose.tsx` (bouton Envoyer) | La vue Email montée dans la coque envoie directement au clic, sans l'écran de confirmation promis par le changelog 0.40. Comportement identique au classique, donc pas une régression, mais contraire au contrat « tout effet externe confirmé » de la 0.40. | Couche de confirmation commune appliquée aux vues intégrées (Email, Agenda, Factures) quand elles tournent dans la coque. |
| BLOQUANT contrat | `PrototypeUnifiedViewCanvas` + `EventForm.tsx` (bouton Enregistrer) | Idem Agenda : création/modification réelle au clic, invitations possibles, sans confirmation intermédiaire. | Idem. |
| BLOQUANT contrat | `CommandExecutor.tsx` + `SkillPromptPanel.tsx` (commandes Images) | Le déclenchement direct du provider contourne la génération en deux étapes annoncée. | Aligner sur le flux confirmé des canevas. |
| MAJEUR données | `database.py` `ensure_alembic_stamp` (réalignement US-015) | La preuve de schéma exigée avant ré-estampillage (`validite_jours` + table `variables`) n'a PAS été étendue aux colonnes Board/Atelier ajoutées par `c8d9e0f1a2b3` et `d9e0f1a2b3c4`. Une base trackée ancienne, patchée ad-hoc mais sans ces colonnes, serait estampillée à la nouvelle tête et sauterait définitivement les deux migrations. Le commentaire du code exigeait explicitement cette extension à chaque révision. | Étendre la preuve de schéma aux colonnes des deux nouvelles révisions. |
| MAJEUR facturation | `PrototypeUnifiedViewCanvas` + `InvoiceForm.tsx` | Marquer payé / accepter / refuser en un clic sans confirmation dans la coque. | Même couche de confirmation. |
| À DOCUMENTER | migrations `c8d9e0f1a2b3` / `d9e0f1a2b3c4` (downgrade) | Le downgrade supprime les colonnes d'historique : toute donnée Board/Atelier enregistrée après l'upgrade est perdue au rollback. Mécaniquement inhérent à un downgrade de colonnes, pas un bug, mais à écrire noir sur blanc dans la procédure de retour arrière. | Paragraphe explicite dans `RECETTE-ET-RELEASE.md` (retour arrière). |
| MINEUR durcissement | `interfaceMode.ts` (verrou sur `import.meta.env.DEV`) | Théorique : `vite build` compile en production par défaut, donc le verrou tient ; mais un build lancé en `--mode development` l'ouvrirait. Durcissement peu coûteux souhaitable (double condition, ex. flag de build explicite). | Ajouter une seconde condition indépendante du mode Vite. |

## Findings nuancés ou périmés

- « Aucun downgrade n'est testé » : périmé depuis le pré-vol OPT du 15/07 au
  matin, qui a exécuté sur une copie chiffrée de la base réelle :
  `downgrade -2` (tête -> b7c8d9e0f1a2) puis `upgrade head`, comptages
  identiques à chaque étape (30 tables, 630 lignes), rc=0. Les scripts des deux
  révisions ont réellement tourné dans les deux sens.
- La critique de l'estampillage `env.py` côté bases de test reste à instruire,
  mais la couverture réelle existe désormais via le pré-vol sur copie.

## Constat de méthode (à encadrer)

La base réelle `~/.therese` était déjà à la tête `d9e0f1a2b3c4` avant tout
build candidat : le chantier a tourné en dev directement sur les données de
production de Ludo. Sans dégât ici (migrations additives, réversibilité
prouvée), mais à proscrire : le dev doit pointer un `THERESE_DATA_DIR` de
travail.

## Ordre de reprise proposé

1. Lot correctifs 1 : couche de confirmation sur les vues intégrées (Email,
   Agenda, Factures, Images) dans la coque uniquement.
2. Lot correctifs 2 : extension de la preuve de schéma `ensure_alembic_stamp`
   + durcissement du verrou `interfaceMode`.
3. Documentation : perte d'historique au rollback + règle `THERESE_DATA_DIR`
   en dev.
4. Recette visuelle Ludo (`RECETTE-VISUELLE-LUDO.md`), signature, décision du
   mode par défaut : inchangés, après les lots 1-2.
