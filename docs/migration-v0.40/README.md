# Préparation de THÉRÈSE 0.40

Statut : **LOCAL UNIQUEMENT, aucune diffusion autorisée**  
Version du dépôt au démarrage du chantier : **0.32.1**  
Version applicative cible proposée à terme : **0.40.0**. La bêta ne commencera
qu’après signature des builds/apps et GO explicite de Ludo.

Ce dossier prépare une migration progressive vers l’interface conversationnelle
validée en prototype. Il ne transforme pas le prototype en produit fini et ne
change pas la version de l’application.

## Garde-fou de diffusion

Tant que ce statut n’est pas modifié explicitement :

- pas de bump vers 0.40 ;
- pas de tag Git ;
- pas de publication GitHub, updater, landing ou canal de test ;
- pas de build distribué, même présenté comme préversion ;
- pas de commit de release.

Le code et les documents restent sur la machine locale. La future bêta aura son
propre GO après signature et vérification du build candidat.

Garde-fou technique actuel : tout build non-développement force l’interface
classique, quels que soient l’URL, la variable d’environnement ou le stockage
local. Le bootstrap commun est déjà intégré localement, mais ce verrou ne sera
retiré qu’après la recette Tauri, la signature du build candidat et le GO bêta.

## État local du socle

La sélection de l’interface intervient maintenant dans un démarrage partagé. Les
deux coques passent par la préparation du backend, l’authentification,
l’onboarding, les réglages d’accessibilité, la gestion globale des erreurs, les
notifications, l’updater et les confirmations sensibles.

Cette fondation a été validée dans le navigateur local après un rechargement à
froid. Elle ne constitue pas encore une validation du cycle complet Tauri. Les
données du brief du jour, de Contacts et mémoire, d’Email, de Devis et factures,
du Board et de l’Atelier sont maintenant reliées au backend et aux stores existants. Le
Board vérifie le consentement cloud, interdit le repli cloud en mode souverain,
annule les tâches actives à la fermeture et relit toute décision annoncée comme
sauvegardée. L’Atelier relit l’historique `AgentTask`, affiche le dépôt et les
modèles configurés, exécute dans un worktree isolé et relit le diff avant toute
application. Le scénario rendez-vous reste à remplacer par son contrat réel.

## Intention produit

THÉRÈSE conserve ses fonctionnalités, mais les présente dans une interface
principale unique :

- une conversation comme point d’entrée ;
- un canevas contextuel pour voir, comparer, éditer et valider ;
- un centre des capacités organisé par intentions métier ;
- une couche de confiance visible avant toute action ayant un effet externe ;
- Board et Atelier intégrés comme deux canevas spécialisés, et non comme deux
  applications séparées.

La coque couvre les parcours journée, contacts, email, rendez-vous, facturation,
Board et Atelier. Journée, contacts, email, facturation, Board et Atelier utilisent
déjà leurs données réelles. Rendez-vous conserve encore une présentation simulée
et doit être branché progressivement sur ses services existants.

## Principes non négociables

1. L’interface 0.32.1 reste disponible jusqu’à la parité fonctionnelle vérifiée.
2. Aucune migration de données n’est requise pour introduire la nouvelle coque.
3. Les opérations externes restent soumises à confirmation explicite.
4. `actionRegistry.ts` devient le contrat d’adaptation commun entre les deux UI.
5. Un lot peut être désactivé sans restaurer une base de données ni réinstaller
   l’application.
6. La 0.40 n’est publiée qu’après recette des parcours critiques et test réel de
   retour à l’interface classique, puis signature du build candidat.

## Activation contrôlée

L’ordre de priorité est volontairement simple : URL, build, préférence locale,
puis interface classique.

| Besoin | Activation |
|---|---|
| Revue ponctuelle | `?interface=conversation-canvas` |
| Compatibilité du prototype | `?prototype=conversation-canvas` |
| Démarrage local du prototype | `VITE_THERESE_INTERFACE_MODE=conversation-canvas` |
| Bêta persistante locale | `localStorage.setItem('therese-interface-mode', 'conversation-canvas')` |
| Retour arrière immédiat | `?interface=classic` |
| Retour durable | `localStorage.setItem('therese-interface-mode', 'classic')` |

La variable de build est documentée dans `src/frontend/.env.example`. Aucun de
ces mécanismes n’active la nouvelle interface par défaut dans la version actuelle.

## Dossier de préparation

- [Architecture cible](ARCHITECTURE-CIBLE.md)
- [Couverture des 30 capacités](COUVERTURE-FONCTIONNELLE.md)
- [Socle transversal à préserver](SOCLE-TRANSVERSAL.md)
- [Audit indépendant de parité](AUDIT-PARITE.md)
- [Plan de migration](PLAN-DE-MIGRATION.md)
- [Recette et préparation de release](RECETTE-ET-RELEASE.md)
- [Décisions et arbitrages](DECISIONS.md)
- [Notes de version 0.40, brouillon](CHANGELOG-0.40-DRAFT.md)

## Définition de « prête à migrer »

- les 30 capacités ont un propriétaire technique et un statut de couverture ;
- les parcours critiques ont des tests d’acceptation reproductibles ;
- l’ancienne et la nouvelle interface utilisent les mêmes données et API ;
- une action sensible affiche sa portée, sa destination et demande confirmation ;
- le passage 0.32.1 vers 0.40 et le retour arrière sont documentés et testés ;
- les sources de version, badges et lockfiles sont synchronisés ;
- les données réelles de l’utilisateur ne sont ni recopiées ni transformées sans
  migration Alembic dédiée.
