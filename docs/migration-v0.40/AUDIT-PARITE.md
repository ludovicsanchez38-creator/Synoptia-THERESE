# Audit indépendant de parité

Date : 13 juillet 2026  
Portée : dépôt local 0.32.1 et prototype conversation-canvas  
Méthode : croisement indépendant des composants, stores, API frontend, routeurs,
services backend, configuration Tauri et documents de migration.

## Verdict

Les 30 capacités couvrent les grands domaines métier. La parité n’est toutefois
pas acquise : plusieurs fonctions sont seulement disponibles par API et certaines
sont partielles. Le contournement de la coquille applicative identifié pendant
l’audit a été corrigé localement, sans rendre le prototype distribuable.

## Bloquants avant une bêta

| Priorité | Constat vérifié | Décision 0.40 |
|---|---|---|
| P0 traité localement | Le prototype était rendu avant le bootstrap applicatif | `ApplicationBootstrap` est partagé ; recette Tauri et premier démarrage encore requis |
| P0 traité localement | Les confirmations d’outils vivaient dans le chat classique | couche de confirmation commune ajoutée et couverte par test |
| P0 | La conversation combine état local, backend, éphémère, brouillons et streaming | réutiliser les contrats et identifiants existants |
| P0 | L’envoi de facture retourne HTTP 501 | masquer ou désactiver l’action tant qu’elle n’est pas implémentée |
| P0 traité localement | L’Atelier changeait le checkout utilisateur, relisait le mauvais diff et pouvait laisser des processus actifs | worktree isolé, diff de la branche de tâche, annulation backend et nettoyage en `finally` |
| P0 traité localement | OpenClaw pouvait exécuter des actions métier sans confirmation | hors du canevas 0.40 et bridge limité aux outils de lecture |
| P1 | Plusieurs capacités n’ont pas de parcours UI complet | afficher leur statut réel et prévoir un repli classique |

## États fonctionnels à ne pas surévaluer

| Fonction | État observé | Preuve principale |
|---|---|---|
| Calculateurs | API uniquement, aucune surface dédiée trouvée | `services/api/calculators.ts`, `routers/calculators.py` |
| Juridique | corpus déterministe injecté dans le chat, pas de canevas autonome | `services/legal_corpus.py`, `routers/chat.py` |
| Relances | backend CRUD et synthèse Accueil, pas de client CRUD dédié | `routers/follow_ups.py`, `TodayPanels.tsx` |
| Factures | création et PDF présents ; ouverture PDF incomplète ; envoi indisponible | `InvoicesPanel.tsx`, `routers/invoices.py` |
| Images | API de génération et historique ; historique sans surface dédiée | `services/api/images.ts`, `routers/images.py` |
| Voix | dictée/transcription raccordées ; synthèse vocale sans parcours trouvé | `services/api/voice.ts`, `routers/voice.py` |
| Actions guidées | UI et backend présents, fiabilité à auditer avant migration | `ActionPanel.tsx`, `action_agents.py` |
| Sauvegardes globales | backend complet, parcours frontend global incomplet | `routers/data.py` |
| Entités détectées | extraction asynchrone journalisée, résultat non renvoyé au frontend | `routers/chat.py`, `EntitySuggestion.tsx` |

## Fonctions transverses ajoutées à la parité

- cycle de vie complet des conversations et brouillons ;
- confirmations, consentement, erreurs et état de connexion ;
- sauvegarde, restauration, import, export et traçabilité ;
- gestion détaillée des fichiers et rattachement aux projets ;
- distinction entre toasts et notifications persistantes ;
- OAuth, IMAP/SMTP, CalDAV, Google, ICS, CSV, JSON, VCF et CRM Sheets ;
- sidecar, fenêtre, permissions Tauri, CSP et mise à jour ;
- accessibilité, modes standard/contributeur et masquage de démonstration.

## Corrections déjà intégrées après audit

- prototype forcé en développement local, build distribuable forcé en classique ;
- bootstrap commun aux interfaces classique et 0.40 ;
- erreurs globales, accessibilité, notifications, updater et onboarding partagés ;
- confirmations sensibles remontées dans la coquille commune et couvertes par test ;
- matrice transversale ajoutée ;
- inventaire exact des 30 capacités verrouillé par test ;
- mention SQLCipher remplacée par la réalité : secrets chiffrés ;
- RAG juridique autonome reformulé en corpus juridique ;
- balises parasites retirées d’une entrée du corpus et protégées par un test ;
- limites factures, relances, images et entités rendues visibles dans la matrice.
- validation de chemin Atelier corrigée, commandes directes resserrées et fichiers
  sensibles refusés ;
- historique, préflight, progression, artefacts et revue Atelier raccordés sans
  chiffres simulés ;
- repli classique Atelier confirmé avant lancement et application.

## Points techniques à traiter dans des lots dédiés

L’audit a également relevé des incohérences possibles dans le contexte des actions
guidées, la persistance de leurs tâches, les raccourcis personnalisés et certaines
promesses de l’écran Confidentialité. Ces sujets doivent être reproduits et
testés séparément avant correction. Ils ne sont pas déclarés résolus par ce
document.
