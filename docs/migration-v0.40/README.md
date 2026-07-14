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
données du brief du jour, de Contacts et mémoire, d’Email, de Rendez-vous, de
Devis et factures, du Board et de l’Atelier sont maintenant reliées au backend
et aux stores existants. Le fil utilise aussi les vraies conversations, leur
historique, leur renommage, leur export et leur suppression. Le centre des
capacités possède désormais un débouché explicite pour chacune de ses 30
entrées : canevas 0.40, vue existante intégrée dans la coque, action, réglage ou
reprise dans le chat. Les cinq calculateurs
ROI, ICE, RICE, VAN et seuil de rentabilité utilisent leurs moteurs locaux
déterministes, sans modèle IA ni persistance. Images, Relances et Voix disposent
de leurs surfaces réelles : galerie et génération confirmée, échéances email
éditables, import audio, transcription confirmée et synthèse locale Piper. Le
suivi des livrables agrège en lecture seule les projets, livrables CRM, tâches et
documents de facturation. Confidentialité expose l’export global, la purge
globale et les sauvegardes avec confirmation. Le Board vérifie le consentement
cloud, interdit le repli cloud en mode souverain, annule les tâches actives à la
fermeture et conserve sources, modèles et usage avec la décision. L’Atelier
relit l’historique `AgentTask`, affiche le dépôt et les modèles configurés,
exécute dans un worktree isolé et persiste plan, phases, tests, explication,
sorties agents, branche et commit. Rendez-vous agrège les calendriers sur 90
jours, relie les contacts par email exact et ne charge que les activités CRM
réellement disponibles.

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
Board et Atelier. Ces sept parcours utilisent désormais leurs données réelles.
Agenda reste modifiable dans la vue classique ; le canevas 0.40 permet aussi une
création confirmée et une note CRM confirmée, sans synthèse IA non sourcée.
Les 30 capacités ont maintenant une destination explicite. Personnalisation
ouvre les réglages réels de mode, démarrage et accessibilité ; les anciennes
préférences backend non consommées par l’application ne sont pas annoncées.

La dernière consolidation locale du 14 juillet 2026 est verte : 1 568 tests
backend principaux, 159 tests backend complémentaires, 541 tests frontend et
15 parcours navigateur 0.40, plus typage, lint, build web et compilation native.
La reconnexion continue après une panne longue est
désormais couverte. Ces résultats sont consignés dans la recette ; ils ne
remplacent ni le test du sidecar empaqueté ni la signature du futur build
candidat.

## Principes non négociables

1. L’interface 0.32.1 reste disponible jusqu’à la parité fonctionnelle vérifiée.
2. La coque réutilise la base existante ; deux migrations Alembic additives
   conservent les métadonnées historiques du Board et de l’Atelier.
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
- [Audit final local](AUDIT-FINAL-LOCAL.md)
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
