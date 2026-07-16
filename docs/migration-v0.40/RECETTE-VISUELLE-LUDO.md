# Recette visuelle guidée - 30 minutes (Ludo)

Version condensée et actionnable de la matrice de `RECETTE-ET-RELEASE.md`,
pensée pour une passe manuelle unique. Cocher au fil de l'eau, noter chaque
défaut avec une capture, envoyer le tout à OPT sur Telegram.

Préparation : `make dev`, ouvrir les Paramètres, puis dans « À propos » activer
« Essayer la nouvelle interface (bêta) » et choisir « Recharger maintenant ».
Le paramètre `?interface=conversation-canvas` reste disponible comme solution de
secours en développement.

## 1. Affichage et thème (5 min)

- [ ] Thème clair puis thème sombre depuis les réglages : aucun texte illisible,
      aucun bloc au mauvais fond dans le fil, le centre des capacités et deux
      canevas au choix.
- [ ] Fenêtre réduite au minimum : rien ne se superpose, le fil reste utilisable,
      pas de défilement horizontal parasite.
- [ ] Zoom d'accessibilité (taille de texte augmentée dans les réglages) : la
      coque tient.

## 2. Fil conversationnel (5 min)

- [ ] Envoyer un message et regarder le streaming : la réponse s'écrit sans
      saccade anormale.
- [ ] Pendant une réponse active : tenter de changer de vue, fermer, créer une
      nouvelle conversation. Tout doit être refusé tant que le flux tourne.
- [ ] Ouvrir le tiroir des conversations : historique présent, renommer une
      conversation, exporter, en supprimer une de test.

## 3. Centre des capacités (5 min)

- [ ] Ouvrir le centre : les 30 entrées répondent, aucune n'aboutit à une
      impasse ou à un écran vide.
- [ ] Calculateur ROI : saisir deux valeurs simples, résultat immédiat et
      cohérent (moteur local, pas d'IA).
- [ ] Images : la galerie charge, une génération demande confirmation avant de
      partir.
- [ ] Relances : les échéances s'affichent et une date est éditable.

## 4. Effets externes - le point de confiance (5 min)

- [ ] Créer un brouillon d'email depuis le fil : aperçu complet, confirmation en
      deux temps, et NE PAS envoyer.
- [ ] Créer un brouillon de rendez-vous : même exigence, l'annulation ne laisse
      aucune trace.
- [ ] Vérifier qu'aucune action externe ne part jamais sans écran de
      confirmation.

## 5. Retour arrière (7 min) - protocole officiel

1. En mode `conversation-canvas`, ouvrir 2-3 objets réels (un contact, un
   email, une facture) et créer un brouillon non envoyé.
2. Dans Paramètres → À propos, désactiver « Essayer la nouvelle interface
   (bêta) », puis recharger comme proposé.
3. Retrouver exactement les mêmes objets dans les vues historiques.
4. Réactiver l’interrupteur, recharger et vérifier qu’aucun doublon n’a été créé.
5. Fermer et relancer : le mode choisi persiste aussi dans un build de
   production. Sans choix valide, le classique reste le mode par défaut.

## 6. Verdict

- [ ] Aucun défaut critique (perte de données, action externe sans
      confirmation, bascule classique cassée) → recette visuelle OK.
- Défauts mineurs : liste + captures à OPT, ils partent en lot de correctifs
  avant le build candidat.

Rappel : cette recette valide l'interface en dev. Le GO bêta exige en plus le
paquet Tauri signé et le pré-vol données (fait par OPT sur copie). Le mode par
défaut a été décidé par Ludo le 15/07/2026 et consigné dans `DECISIONS.md`.
