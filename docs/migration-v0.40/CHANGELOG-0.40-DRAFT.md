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
- Sources web, provider, modèle et usage conservés dans l’historique local.
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
- Plan, phases, tests, explication, sorties agents, branche de base et commit
  conservés pour reconstruire une mission après fermeture.
- Profils autonomes maintenus en lecture/recherche. OpenClaw est exclu du canevas
  et son bridge est limité à la lecture tant qu’il n’a pas de confirmation 0.40.

## Maîtrise et confiance

- Distinction visible entre lecture, brouillon et effet externe.
- Confirmation avant envoi, création externe, suppression ou publication.
- Retour possible à l’interface classique pendant la période de migration.
- Centre des 30 capacités relié à des canevas, vues, actions ou réglages réels.
- Reprise explicite dans le chat sans placer le texte de la demande dans l’URL.
- Personnalisation reliée aux réglages réels de mode, démarrage et accessibilité.
- Export et purge RGPD globaux, ainsi que création, restauration et suppression
  des sauvegardes, disponibles depuis Confidentialité avec confirmations.

## Images, relances et voix

- Studio Images relié au statut provider, à l’historique, à l’aperçu, au
  téléchargement et à la génération confirmée.
- File des relances email avec filtres, modification d’échéance et note,
  clôture, réouverture et suppression confirmée.
- Import audio avec moteur local ou cloud annoncé, confirmation avant
  transcription, texte éditable et reprise dans le chat.
- Synthèse vocale locale Piper avec lecture et enregistrement du WAV.

## Livrables et suivi client

- Lecture unifiée par projet des livrables, échéances et tâches restantes.
- Facturation du contact relié affichée séparément, sans prétendre qu’une facture
  est liée à un livrable précis.
- Dégradation partielle si Contacts, Tâches ou Facturation sont indisponibles.
- Chargement ciblé par projet et protection contre les réponses obsolètes lors
  d’un changement rapide de sélection.
- Limites de 200 projets, 100 documents et 1 000 tâches rendues visibles.
- Aucune création, validation, suppression ou synchronisation depuis ce canevas.

## Calculateurs

- Canevas unique pour ROI, ICE, RICE, VAN et seuil de rentabilité.
- Formule, hypothèses et résultat visibles ; aucun recours à un modèle IA.
- Validation des bornes, prévention du double déclenchement et refus explicite
  des résultats numériques hors limites.
- Aucun historique ni enregistrement des hypothèses dans ce premier lot.

## Rendez-vous et Agenda

- Prochains événements réels agrégés depuis les calendriers local, Google et
  CalDAV, sans création implicite ni modification du store classique à l’ouverture.
- Préparation factuelle à partir de l’événement, des participants, des contacts
  reliés par email exact et de leurs activités CRM disponibles.
- Création en deux étapes avec destination, provider, compte, horaires, fuseau et
  participants visibles avant confirmation.
- Même garde de confirmation pour les créations demandées au LLM, par `/rdv` ou
  par directive `[rdv: ...]`.
- Notes de rendez-vous ajoutées au CRM uniquement après confirmation séparée.

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
- PDF ouvert localement. Conversion, paiement, suppression et envoi restent hors
  du canevas tant que leurs contrats ou confirmations ne sont pas fiabilisés.

## Compatibilité

- Données et services existants conservés.
- Même base et mêmes identifiants que l’interface historique.
- Deux migrations Alembic additives conservent les métadonnées historiques du
  Board et de l’Atelier ; leur validation sur copie réelle reste un prérequis de
  bêta.
- Procédure de retour arrière testée avant publication.
