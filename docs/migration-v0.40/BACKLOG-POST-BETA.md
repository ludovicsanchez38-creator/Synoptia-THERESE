# Backlog post-bêta THÉRÈSE 0.40 - à creuser après la sortie

Décision Ludo 16/07/2026 : ces points méritent tous d'être creusés, mais
APRÈS la bêta, un par un et sérieusement, pas entassés dans la release du soir.
Ne pas les perdre. Ordre indicatif par impact perçu.

## 1. Cohérence coque ↔ vues détaillées (le plus visible)
« Vue complète » (Contacts, Mémoire, etc.) et plusieurs raccourcis rouvrent les
écrans de l'ancienne interface intégrés dans la coque. Fonctionnel mais rupture
visuelle : l'utilisateur a l'impression de sortir de la nouvelle interface.
Chantier : soit habiller ces vues au chrome de la coque, soit les réécrire en
canevas 0.40. Gros sujet de fond, à cadrer. (LUDO-9)

## 2. Centre de notifications réel
La cloche pointe sur le Brief du jour mais il n'existe pas de vrai centre de
notifications avec état lu / non lu, badge de compteur, historique. C'est une
feature à part entière, pas un correctif. (SOLUX-24 partie notifications)

## 3. Onboarding - avance automatique
Après sauvegarde du profil, l'assistant avance seul au bout de ~650 ms et
désactive Retour. L'utilisateur ne choisit pas quand continuer. Finition :
état de succès stable + « Continuer » explicite. (SOLUX-30)

## 4. Onboarding - dossier de travail persisté trop tôt
Le dossier de travail est enregistré immédiatement à la sélection, avant de
valider l'étape ; revenir en arrière ne l'annule pas. Séparer sélection locale
et persistance sur « Continuer ». (SOLUX-31)

## 5. Feedback « nouvelle conversation »
Le « + » / Nouvelle conversation donne un signal faible qu'un espace vierge
s'est ouvert (écran proche de l'accueil). À confirmer et renforcer. (OPT-04)

---

Traité dans les vagues 1 à 5 + lot fenêtre (hors de ce backlog) :
6 bloquants bêta, chantier accessibilité complet (focus, ARIA, contraste,
états, responsive), contrôles de fenêtre native. Voir AUDIT-UIUX-20260716.md
et RAPPORT-RECETTE-PERSONAS-20260716.md.
