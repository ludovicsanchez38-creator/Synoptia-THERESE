# Plan de migration vers la 0.40

Les numéros intermédiaires ci-dessous constituent un découpage proposé. Ils
n’engagent pas une publication pour chaque étape. Chaque lot doit rester
livrable, testable et désactivable indépendamment.

Toutes ces étapes restent locales jusqu’au GO bêta donné après signature des
builds/apps. Les numéros décrivent des jalons de travail, pas des releases à
publier.

## 0.33 : fondations réversibles

Objectif : faire cohabiter les deux interfaces sans toucher aux données.

État local au 14 juillet 2026 : socle implémenté, non diffusé. La coque Tauri de
développement compile et démarre ; la reprise tardive du backend est couverte.
Le premier démarrage du sidecar empaqueté reste à valider avant bêta.

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
- [x] recette locale du backend indisponible puis reconnecté, avec contrôle
  automatique persistant après les cinq premières tentatives ;

Sortie du lot : la racine sans paramètre ouvre toujours l’interface stable et la
nouvelle coque reste accessible sur demande en développement local uniquement.

## 0.34 : capacités en lecture

Objectif : remplacer les données simulées par des données réelles sans effet
externe.

État local au 14 juillet 2026 : les raccordements principaux sont réalisés et testés. Ils
restent non diffusés.

- [x] brief du jour ;
- [x] contacts et mémoire en lecture locale ;
- [x] emails en consultation, Gmail et IMAP ;
- [x] devis et factures en consultation ;
- [x] historique et détail du Board ;
- [x] agenda en consultation et préparation de rendez-vous factuelle ;
- [x] projets et pipeline via leurs vues réelles montées dans la coque ;
- [x] fichiers et connaissances via leur vue réelle montée dans la coque ;
- [x] historique reconstructible des missions Atelier.

Sortie du lot : chaque carte affiche sa source, gère vide/erreur/chargement et
ouvre la vue classique équivalente si le canevas n’est pas encore disponible.

## 0.35 : brouillons et édition locale

Objectif : produire et modifier sans exécuter implicitement.

- [x] brouillon d’email généré ou manuel, modifiable, avec confirmation avant
  création chez le fournisseur et aucun envoi exposé ;
- [x] devis brouillon structuré, calculé, modifiable et créé une seule fois après
  confirmation explicite ;
- [x] proposition d’événement avec calendrier/provider/fuseau visibles et
  confirmation commune au canevas, au LLM, à `/rdv` et aux directives inline ;
- [x] proposition de tâche via la vue Tâches réelle ;
- [x] formulaire de devis ou facture via le canevas et la vue Factures ;
- [x] document structuré et livrable Office via les surfaces existantes ;
- [x] génération d’image confirmée, historique et téléchargement ;
- [x] modèles, variables et commandes via leurs surfaces existantes ;
- [x] relances email et voix/transcription via des canevas spécialisés ;
- [x] export, purge et sauvegardes globales dans Confidentialité.

Sortie du lot : l’utilisateur peut reprendre, éditer, abandonner ou valider un
brouillon. Fermer un canevas ne déclenche aucun effet externe.

## 0.36 : Board et Atelier réels

Objectif : relier les deux expériences distinctives aux services existants.

- [x] Board : lancement confirmé, progression, conseillers, divergences,
  synthèse, historique et sauvegarde relue ;
- [x] Board souverain sans repli cloud et annulation des tâches au départ ;
- [x] Atelier : historique, préflight, cadrage, plan SSE, agents, progression,
  artefacts Git, revue, application et refus confirmés ;
- [x] Board : états interrompu, annulé, erreur et sauvegarde non vérifiable ;
- [x] Board : transmission et nombre maximal d’appels visibles avant lancement ;
- [x] Atelier : états interrompu, annulé, erreur, dépôt non sûr et revue
  indisponible ; annulation propagée au processus backend.
- [x] Board : sources, modèles et usage conservés dans l’historique ;
- [x] Atelier : plan, phases, tests, explication, sorties agents, branche de base
  et commit conservés dans l’historique.

Le canevas initial branche uniquement le swarm de changement de code. OpenClaw,
les six profils autonomes et Action Agents restent en repli expérimental jusqu’à
l’adoption du même contrat de permission, persistance et confirmation. OpenClaw
est limité à la lecture dans l’intervalle.

Sortie du lot : aucune réponse ou progression simulée n’est présentée comme
réelle.

## 0.37 : parité et registre des capacités

Objectif : couvrir les 30 capacités et réduire les doubles chemins.

État local au 14 juillet 2026 : les 30 cartes ont un débouché déterministe et
testé. La parité de navigation du catalogue est atteinte ; plusieurs capacités
restent néanmoins portées par les surfaces classiques.

- [x] relier chaque capacité à un canevas ou une destination explicite ;
- [x] documenter et désactiver les capacités indisponibles sans faux repli chat ;
- [x] unifier la recherche et le centre des capacités avec la navigation réelle ;
- [x] ajouter les tests de contrat du catalogue et du pont classique ;
- [x] ajouter les liens de repli vers les vues classiques restantes ;
- [x] raccorder ROI, ICE, RICE, VAN et seuil de rentabilité à leurs moteurs ;
- [x] raccorder Livrables et suivi client à une lecture réelle unifiée ;
- [x] relier Personnalisation aux réglages réellement consommés.
- [x] remplacer les bascules normales vers le classique par le montage des vues
  existantes dans la coque unifiée ;
- [x] raccorder Images, Relances, Voix et Confidentialité à leurs API réelles.

Sortie du lot : la matrice de couverture ne contient plus de capacité sans
propriétaire technique ni comportement de repli.

## 0.38 : bêta maîtrisée

Objectif : tester l’usage réel avant de changer le mode par défaut.

- activation explicite pour un groupe de test ;
- [x] rôles de dialogue, focus initial, tabulation contenue et restitution du
  focus pour le centre, la confiance et la recherche ;
- accessibilité complète clavier, contraste, taille de texte et réduction des mouvements ;
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

La coque ne crée pas de deuxième jeu de données. Les migrations additives Board
et Atelier ont leur révision Alembic et leurs tests de tête. Elles doivent encore
être validées sur une copie représentative avec sauvegarde et retour avant bêta.
