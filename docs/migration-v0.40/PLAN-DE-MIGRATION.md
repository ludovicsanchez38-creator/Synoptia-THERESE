# Plan de migration vers la 0.40

Les numéros intermédiaires ci-dessous constituent un découpage proposé. Ils
n’engagent pas une publication pour chaque étape. Chaque lot doit rester
livrable, testable et désactivable indépendamment.

Toutes ces étapes restent locales jusqu’au GO bêta donné après signature des
builds/apps. Les numéros décrivent des jalons de travail, pas des releases à
publier.

## 0.33 : fondations réversibles

Objectif : faire cohabiter les deux interfaces sans toucher aux données.

État local au 13 juillet 2026 : socle implémenté, non diffusé. La recette dans
Tauri, le premier démarrage et les modes dégradés restent à valider avant bêta.

- [x] sélecteur de mode centralisé ;
- [x] compatibilité de l’URL du prototype ;
- [x] variable de build et préférence bêta locale ;
- [x] retour forcé vers le mode classique ;
- [x] verrou de production forçant le mode classique ;
- [x] extraction du bootstrap commun : sidecar, auth, onboarding, accessibilité,
  erreurs, notifications et updater ;
- [x] confirmations d’outils portées par la coquille commune ;
- [x] tests automatisés de la bascule et de la confirmation commune ;
- [x] contrôle unique de cohérence des versions ;
- [ ] recette du premier démarrage dans Tauri ;
- [ ] recette du backend indisponible puis reconnecté.

Sortie du lot : la racine sans paramètre ouvre toujours l’interface stable et la
nouvelle coque reste accessible sur demande en développement local uniquement.

## 0.34 : capacités en lecture

Objectif : remplacer les données simulées par des données réelles sans effet
externe.

État local au 13 juillet 2026 : trois raccordements sont réalisés et testés. Ils
restent non diffusés.

- [x] brief du jour ;
- [x] contacts et mémoire en lecture locale ;
- [x] emails en consultation, Gmail et IMAP ;
- projets et pipeline ;
- agenda en consultation ;
- fichiers et connaissances ;
- historiques du Board et des missions.

Sortie du lot : chaque carte affiche sa source, gère vide/erreur/chargement et
ouvre la vue classique équivalente si le canevas n’est pas encore disponible.

## 0.35 : brouillons et édition locale

Objectif : produire et modifier sans exécuter implicitement.

- [x] brouillon d’email généré ou manuel, modifiable, avec confirmation avant
  création chez le fournisseur et aucun envoi exposé ;
- proposition d’événement et de tâche ;
- formulaire de devis ou facture ;
- document structuré et livrable Office ;
- génération ou déclinaison d’image ;
- modèles, variables et commandes.

Sortie du lot : l’utilisateur peut reprendre, éditer, abandonner ou valider un
brouillon. Fermer un canevas ne déclenche aucun effet externe.

## 0.36 : Board et Atelier réels

Objectif : relier les deux expériences distinctives aux services existants.

- Board : lancement, progression, conseillers, divergences, synthèse, historique ;
- Atelier : cadrage, plan, agents, progression, artefacts, revue, application ;
- états interrompu, partiel, en erreur et relançable ;
- permissions et coût visibles avant lancement quand l’information existe.

Sortie du lot : aucune réponse ou progression simulée n’est présentée comme
réelle.

## 0.37 : parité et registre des capacités

Objectif : couvrir les 30 capacités et réduire les doubles chemins.

- relier chaque capacité à un ou plusieurs identifiants d’action ;
- documenter les capacités partielles ou indisponibles ;
- unifier raccourcis, recherche et centre des capacités ;
- tests de contrat sur les adaptateurs ;
- liens de repli vers les vues classiques restantes.

Sortie du lot : la matrice de couverture ne contient plus de capacité sans
propriétaire technique ni comportement de repli.

## 0.38 : bêta maîtrisée

Objectif : tester l’usage réel avant de changer le mode par défaut.

- activation explicite pour un groupe de test ;
- accessibilité clavier, contraste, taille de texte et réduction des mouvements ;
- fonctionnement avec backend indisponible ou service externe déconnecté ;
- mesure locale des échecs de parcours si cet arbitrage est accepté ;
- tests macOS, puis Windows réel si la plateforme est incluse dans la release.

Sortie du lot : les incidents de la nouvelle UI n’empêchent pas le retour au
mode classique.

## 0.39 : release candidate

Objectif : figer le périmètre et prouver le retour arrière.

- gel des nouvelles fonctionnalités ;
- recette complète des parcours critiques ;
- test sur copie d’une base utilisateur existante ;
- sauvegarde, installation, mise à jour et retour arrière ;
- notes de version, limitations connues et support ;
- décision documentée sur l’interface par défaut.

Sortie du lot : décision GO/NO GO signée, artefacts reproductibles et versions
synchronisées.

## 0.40.0 bêta signée : bascule contrôlée

Objectif futur : ouvrir la bêta uniquement avec un build signé et un périmètre
validé.

- activation selon la décision prise en 0.39 ;
- ancienne interface conservée comme repli pendant une période définie ;
- suivi des régressions avec identifiant de parcours ;
- aucun retrait de code historique dans le même changement que la bascule.

## Stratégie de retour arrière

| Niveau | Déclencheur | Retour |
|---|---|---|
| Canevas | erreur locale ou capacité incomplète | ouvrir la vue classique du même objet |
| Interface | régression bloquante | `?interface=classic` ou préférence locale `classic` |
| Build | défaut généralisé | republier le dernier build validé selon la procédure de release |
| Données | migration future en échec | restauration de sauvegarde et downgrade Alembic testé |

La coque initiale ne modifie pas les données. Tout futur changement de schéma
doit avoir son propre plan, son test de copie réelle et sa procédure de retour.
