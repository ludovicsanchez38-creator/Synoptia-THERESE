# Audit indépendant de parité

Date : 14 juillet 2026
Portée : dépôt local 0.32.1 et prototype conversation-canvas  
Méthode : croisement indépendant des composants, stores, API frontend, routeurs,
services backend, configuration Tauri et documents de migration.

## Verdict

Les 30 capacités ont désormais un débouché réel et testable. La parité de
navigation est acquise localement ; la parité métier complète reste limitée par
quelques fonctions historiques ou expérimentales, notamment Action Agents. Les
P0 de bootstrap, conversation, streaming, confirmations, Agenda, facturation et
Atelier ont été corrigés localement, sans rendre la préparation distribuable.

## Bloquants avant une bêta

| Priorité | Constat vérifié | Décision 0.40 |
|---|---|---|
| P0 traité localement | Le prototype était rendu avant le bootstrap applicatif | `ApplicationBootstrap` est partagé ; recette Tauri et premier démarrage encore requis |
| P0 traité localement | Les confirmations d’outils vivaient dans le chat classique | couche de confirmation commune ajoutée et couverte par test |
| P0 traité localement | La conversation combinait état local, backend, éphémère, brouillons et streaming | vrai fil, vrais identifiants, historique backend et navigation verrouillée pendant le streaming |
| P0 traité localement | L’envoi de facture retourne HTTP 501 | action masquée ; PDF local conservé |
| P0 traité localement | L’Atelier changeait le checkout utilisateur, relisait le mauvais diff et pouvait laisser des processus actifs | worktree isolé, diff de la branche de tâche, annulation backend et nettoyage en `finally` |
| P0 traité localement | OpenClaw pouvait exécuter des actions métier sans confirmation | hors du canevas 0.40 et bridge limité aux outils de lecture |
| P0 traité localement | Ouvrir Rendez-vous pouvait créer un calendrier et `/rdv` écrivait sans confirmation | listing pur, read-model isolé et confirmation commune pour toutes les créations Agenda |
| P0 traité localement | Les cartes sans canevas pouvaient lancer un prompt ambigu et transporter son texte dans l’URL | destinations explicites, liste fermée, reprise chat à usage unique dans `sessionStorage` et capacités non fidèles désactivées |
| P0 traité localement | Les calculateurs extrêmes pouvaient produire des flottants non finis sérialisés en résultat nul | contrôles frontend/backend, erreur explicite et tests de dépassement |
| P1 résiduel | Certaines fonctions historiques n’ont pas encore un canevas spécialisé | elles sont montées dans la coque ou signalées comme expérimentales, sans faux résultat |

## États fonctionnels à ne pas surévaluer

| Fonction | État observé | Preuve principale |
|---|---|---|
| Calculateurs | canevas déterministe raccordé aux cinq endpoints, sans LLM ni persistance | `CalculatorWorkspaceCanvas.tsx`, `services/api/calculators.ts`, `routers/calculators.py` |
| Livrables | canevas de lecture raccordé aux projets, livrables, tâches et facturation ; aucune mutation exposée | `DeliverablesWorkspaceCanvas.tsx`, `usePrototypeDeliverablesData.ts`, `crm-extended.ts` |
| Juridique | corpus déterministe injecté dans le chat, pas de canevas autonome | `services/legal_corpus.py`, `routers/chat.py` |
| Relances | canevas CRUD des échéances email et création depuis le détail d’un message | `FollowUpsWorkspaceCanvas.tsx`, `routers/follow_ups.py` |
| Factures | création et ouverture PDF présentes ; envoi indisponible et masqué | `InvoicesPanel.tsx`, `routers/invoices.py` |
| Images | génération confirmée, historique, aperçu et téléchargement raccordés | `ImagesWorkspaceCanvas.tsx`, `routers/images.py` |
| Voix | import, transcription local/cloud et synthèse Piper locale raccordés | `VoiceWorkspaceCanvas.tsx`, `routers/voice.py` |
| Actions guidées | UI et backend présents, fiabilité à auditer avant migration | `ActionPanel.tsx`, `action_agents.py` |
| Sauvegardes et RGPD global | export exhaustif sans secrets, purge et gestion des sauvegardes raccordés | `PrivacyTab.tsx`, `routers/data.py` |
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
- données fictives de Rendez-vous retirées ; association CRM par email exact,
  provider Agenda exposé et calendrier local utilisable sans compte email ;
- dates, ordre début/fin, fuseau et emails participants validés avant création ;
- création Agenda du LLM, de `/rdv` et de `[rdv: ...]` bloquée derrière la même
  carte de confirmation consommable une seule fois.
- les 30 capacités disposent d’un scénario ou d’une destination explicite ; la
  navigation ne contient plus de carte sans débouché ;
- les reprises dans le chat ne transitent plus par l’URL et sont consommées une
  seule fois ; les onglets contributeur ouverts directement restent visibles ;
- ROI, ICE, RICE, VAN et seuil de rentabilité disposent d’un canevas réel ; les
  champs visibles sont transmis au bon moteur et les résultats non finis sont
  refusés des deux côtés de l’API.
- Livrables compose cinq sources en lecture seule et rend explicite que la
  facturation est reliée au contact du projet, faute de clé facture-livrable.
- les lectures Livrables sont ciblées après sélection du projet, les erreurs des
  sections ne deviennent pas des listes vides et les réponses obsolètes sont
  ignorées ; les limites de pagination sont visibles ;
- Personnalisation ouvre l’onglet Avancé réellement consommé, avec transmission
  de l’onglet par le store malgré le chargement différé de la modale.
- la surveillance du backend ne s’arrête plus après cinq échecs : elle avertit
  une seule fois, poursuit les contrôles à cadence réduite et détecte une reprise
  tardive sans redémarrage de THÉRÈSE.
- l’interface 0.40 réutilise le vrai fil, les conversations backend et leurs
  opérations ; toute navigation est refusée pendant une réponse en streaming ;
- l’export RGPD global couvre toutes les tables métier auditées sans exporter les
  secrets, et Confidentialité expose sauvegarde, restauration et purge confirmée ;
- les historiques Board et Atelier conservent désormais les métadonnées utiles à
  leur reconstruction après fermeture ;
- Images, Relances et Voix possèdent leurs surfaces spécialisées et leurs tests
  navigateur représentatifs ;
- les dialogues du centre, de la confiance et de la recherche annoncent leur rôle,
  piègent la tabulation et rendent le focus à l’élément d’origine.

## Points techniques à traiter dans des lots dédiés

La coque utilise désormais les tokens clair/sombre, y compris pour ses teintes
sémantiques, avec un contrat automatisé contre le retour des principaux neutres
figés. L’audit laisse ouverts la revue visuelle manuelle des deux thèmes, la
mesure de coût de l’Atelier, un canevas spécialisé pour les Action Agents et la
recette du sidecar empaqueté. Ils restent des critères de bêta, pas des
fonctionnalités présentées comme terminées par ce document.
