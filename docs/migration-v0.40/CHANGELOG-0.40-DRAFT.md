# THÉRÈSE 0.40.0-alpha

> Brouillon de notes de version. Aucun élément de cette page ne doit être
> présenté comme livré avant validation de la recette, signature du build et GO
> explicite. Le chantier reste local.

## Nouvelle interface unifiée

- Conversation comme point d’entrée principal.
- Canevas contextuel pour consulter, modifier et valider sans multiplier les
  panneaux.
- Centre des capacités organisé autour de six intentions métier.
- Accès conservé aux fonctionnalités historiques pendant la transition.

## Board de décision

- Historique et détail reliés aux décisions réellement sauvegardées.
- Préparation d’une question, choix cloud ou souverain et confirmation visible
  avant tout appel de conseiller.
- Progression SSE, fournisseurs réellement reçus pendant le flux, avis,
  divergences et synthèse réunis dans le canevas.
- Mode souverain strictement limité à Ollama, sans repli cloud.
- Fermeture et annulation propagées aux tâches encore actives.
- Succès affiché seulement après sauvegarde puis relecture de la décision.
- Export PDF, reprise en arrière-plan et transformation automatique en plan
  d’action restent hors du canevas initial.

## Atelier d’agents

- Historique local des missions `AgentTask` et états réels dans la conversation.
- Préflight visible : dépôt autorisé, branche, propreté Git, modèles configurés,
  permissions et transmission possible d’extraits de code au fournisseur.
- Double validation : lancement de la mission, puis application ou refus du diff.
- Exécution dans un worktree temporaire isolé ; la branche et le clone de travail
  de l’utilisateur ne sont plus changés pendant la mission.
- Plan SSE, agents réellement actifs, outils appelés, résultats de vérification,
  fichiers et diff réunis dans le canevas sans compteur ni coût inventé.
- Annulation propagée au backend et aux processus descendants ; fermeture sûre du
  canevas et du panneau classique.
- Approbation, refus et rollback vérifiés par relecture backend avant succès.
- Profils autonomes maintenus en lecture/recherche. OpenClaw est exclu du canevas
  et son bridge est limité à la lecture tant qu’il n’a pas de confirmation 0.40.

## Maîtrise et confiance

- Distinction visible entre lecture, brouillon et effet externe.
- Confirmation avant envoi, création externe, suppression ou publication.
- Retour possible à l’interface classique pendant la période de migration.

## Email

- Consultation de la boîte Gmail ou IMAP connectée avec états chargement, vide,
  erreur et compte absent.
- Lecture du message complet dans le canevas et repli vers la vue Email
  historique.
- Réponse générée ou écrite manuellement, entièrement modifiable.
- Création du brouillon uniquement après confirmation explicite. Aucun bouton
  d’envoi n’est exposé dans la 0.40 à ce stade.

## Devis et factures

- Liste et détail des documents réellement enregistrés, avec contact, statut,
  lignes, dates, montants et devise d’origine.
- Création d’un devis brouillon à partir d’un contact réel, avec plusieurs lignes,
  calcul HT, TVA et TTC puis confirmation explicite.
- Protection contre le double clic afin de ne créer qu’un document et de ne
  consommer qu’un numéro.
- PDF, conversion, paiement, suppression et envoi gardés hors du canevas tant que
  leurs contrats ou leurs confirmations ne sont pas entièrement fiabilisés.

## Compatibilité

- Données et services existants conservés.
- Aucun nouveau schéma de données requis pour la coque initiale.
- Une migration Alembic ultérieure est préparée conceptuellement pour persister
  le plan, les phases, les tests structurés, les permissions et le hash de merge
  de l’Atelier, sans la lancer pendant ce chantier local.
- Procédure de retour arrière testée avant publication.
