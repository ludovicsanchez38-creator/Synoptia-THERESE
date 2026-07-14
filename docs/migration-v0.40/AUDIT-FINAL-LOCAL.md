# Audit final local de la v0.40

Date : 14 juillet 2026

Statut : **fonctionnel en local, non publiable**. La version applicative reste
`0.32.1` et tout build non-développement continue de forcer l’interface
classique. Aucun bump, tag, paquet signé ou canal bêta n’est autorisé par ce
constat.

## Preuves de complétude fonctionnelle locale

| Exigence | Preuve actuelle | Verdict local |
|---|---|---|
| Une seule interface principale | `ConversationCanvasPrototype` porte le fil, les canevas, les vues historiques intégrées, les réglages et les panneaux communs sans rechargement normal | atteint |
| Conversation réelle | `PrototypeChatSurface`, store et API existants ; historique, renommage, export et suppression backend dans le tiroir | atteint |
| Aucun abandon pendant le streaming | navigation, fermeture, nouvelle conversation, changement de vue et reprise de prompt sont refusés pendant une réponse active | atteint |
| 30 capacités conservées | catalogue de 30 identifiants uniques ; exactement une destination par capacité ; aucune destination `pending` | atteint |
| Parcours métier existants préservés | Accueil, Mémoire, CRM, Email, Agenda, Tâches, Factures, Fichiers, Projets et Documents se montent dans la coque via leurs composants réels | atteint |
| Parcours spécialisés | Calculateurs, Livrables, Images, Relances et Voix ont leurs canevas reliés aux API réelles | atteint |
| Board reconstructible | question confirmée, SSE, annulation, souverain strict, relecture après sauvegarde, sources, provider, modèle et usage persistés | atteint |
| Atelier reconstructible et sûr | préflight, worktree isolé, plan, phases, agents, tests, explication, événements, branche, commit, diff et revue confirmée persistés | atteint |
| Effets externes maîtrisés | couche de confirmation commune ; brouillons Agenda, Email et Devis en deux étapes ; envoi de facture indisponible masqué | atteint |
| Données et RGPD | export global exhaustif sans secrets, purge globale doublement confirmée, sauvegarde, restauration et suppression depuis Confidentialité | atteint |
| Identité visuelle authentique | atlas généré utilisé pour Thérèse, les conseillers du Board, Katia et Zézette ; aucune carte de démonstration résiduelle | atteint |
| Accessibilité et thème | bootstrap commun, taille, contraste, mouvement réduit, thème clair/sombre par tokens, dialogues annoncés et focus contenu/restauré | atteint techniquement |
| Migration | migrations additives `c8d9e0f1a2b3` et `d9e0f1a2b3c4`, tête Alembic vérifiée et bootstrap legacy couvert | atteint sur bases de test |
| Réversibilité | mode classique conservé et verrouillé comme défaut de tout build non-développement | atteint localement |

## Recette consolidée

| Contrôle | Résultat |
|---|---|
| Backend principal | 1 568 réussis, 3 ignorés, 1 succès inattendu sur 1 572 cas |
| Backend complémentaire | 159 réussis |
| Frontend | 541 réussis dans 96 fichiers |
| Navigateur | 15 parcours réussis : Agenda, vues intégrées, réglages, chat, conversations, Office, Calculateurs, Images, Relances, Voix, Actions et Livrables |
| Qualité | Ruff sans défaut ; ESLint sans erreur, 25 avertissements historiques tolérés |
| Typage et build | TypeScript sans erreur, build Vite réussi |
| Application native | `cargo check` réussi |
| Migrations | tête Alembic et scénarios legacy/chiffrés réussis |

## Garde de bêta encore fermée

Les points suivants ne remettent pas en cause le fonctionnement local, mais
interdisent de qualifier la v0.40 de bêta distribuable :

1. construire le paquet Tauri candidat avec son sidecar ;
2. signer l’application et vérifier le premier démarrage macOS ;
3. exécuter la recette visuelle manuelle en clair, sombre et fenêtre minimale ;
4. tester migration, sauvegarde et retour arrière sur une copie représentative ;
5. décider du mode par défaut, du canal bêta et obtenir le GO explicite de Ludo.

Améliorations recommandées avant distribution, sans bloquer l’usage local :
alléger les planches d’images, mesurer le coût réel des missions Atelier avant de
l’afficher, puis décider si les Action Agents méritent un canevas spécialisé.
