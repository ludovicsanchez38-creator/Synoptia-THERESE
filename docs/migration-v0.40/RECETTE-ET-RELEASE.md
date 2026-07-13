# Recette et préparation de release 0.40

> Document préparatoire local. Les commandes de version et de diffusion ci-dessous
> restent interdites avant signature du build candidat et GO explicite de Ludo.

## Parcours critiques

Un GO exige au minimum les parcours suivants sur données réelles de test :

1. démarrer et retrouver une conversation ;
2. ouvrir un contact, un projet, un email, un événement et une tâche ;
3. préparer puis abandonner un brouillon sans effet externe ;
4. confirmer un envoi ou une création avec destination clairement affichée ;
5. produire un document et retrouver le ou les fichiers générés ;
6. créer un devis ou une facture, vérifier l’aperçu et le statut ;
7. lancer un Board, lire les divergences et retrouver la décision ;
8. lancer une mission Atelier, revoir les artefacts et refuser leur application ;
9. perdre le backend ou un service externe sans écran bloqué ;
10. revenir à l’interface classique et retrouver les mêmes données.

Pour Email, la recette doit vérifier séparément Gmail et IMAP : compte absent,
erreur fournisseur, boîte vide, liste partielle, lecture du corps normalisé,
génération puis modification de la réponse, annulation de la confirmation et
création du brouillon. La création doit être visible chez le fournisseur sans
qu’aucun message soit envoyé.

La bascule entre interfaces doit aussi être testée pendant cinq états sensibles :

- une réponse en streaming ;
- un brouillon non envoyé ;
- une confirmation d’outil en attente ;
- une conversation éphémère ;
- une indisponibilité du backend.

Avant la bêta, le comportement sûr est d’interdire la bascule pendant un effet
externe ou une confirmation en attente, puis de proposer une sortie explicite.

## Matrice de vérification

| Domaine | Vérifications minimales |
|---|---|
| Navigation | clavier, souris, retour, fermeture du canevas, lien vers l’objet |
| États | chargement, vide, erreur, résultat partiel, nouvelle tentative |
| Confiance | source visible, brouillon identifiable, confirmation avant effet externe |
| Accessibilité | ordre de tabulation, focus visible, lecteur d’écran, contraste, zoom, mouvement réduit |
| Données | absence de duplication, persistance, cohérence entre les deux interfaces |
| Résilience | backend arrêté, réseau coupé, provider en erreur, token expiré |
| Performance | démarrage, ouverture du centre, grand historique, fichiers volumineux |
| Affichage | fenêtre minimale Tauri, écran courant, thème clair/sombre si conservés |
| Plateformes | macOS réel ; Windows réel si annoncé dans les notes de version |
| Services | connexion, reconnexion, déconnexion, synchronisation et erreurs par protocole |

## Contrôles automatisés avant release

```bash
make version-check
make typecheck
make test-frontend
make lint
make build-web
git diff --check
```

Le contrôle de version couvre les sept sources principales, les lockfiles et le
badge du README. Le bump ci-dessous est une procédure future. Il n’est pas à
lancer pendant le chantier local :

```bash
./scripts/bump-version.sh 0.40.0
make version-check
```

Le nom du futur tag sera arrêté au moment du GO bêta. Le suffixe de canal ne sera
pas injecté dans les sept sources de version.

## Pré-vol données

- sauvegarder la base et les fichiers de travail ;
- tester sur une copie représentative, jamais sur l’unique base utilisateur ;
- relever la révision Alembic avant et après installation ;
- contrôler le nombre de conversations, contacts, projets, tâches et factures ;
- vérifier qu’un retour à l’ancienne interface relit les mêmes enregistrements.

Pour la coque 0.40 seule, la révision Alembic doit rester inchangée.

## Test explicite du retour arrière

1. Activer `conversation-canvas`.
2. Ouvrir plusieurs objets réels et créer un brouillon non envoyé.
3. Forcer `?interface=classic`.
4. Vérifier les mêmes objets dans les vues historiques.
5. Revenir en 0.40 et vérifier qu’aucun doublon n’a été créé.
6. Fermer et relancer l’application pour vérifier le mode persistant choisi.

## GO / NO GO

GO uniquement si :

- aucun défaut critique ou perte de données n’est ouvert ;
- tous les effets externes sont précédés d’une confirmation ;
- les parcours critiques sont verts dans les deux interfaces ;
- le retour arrière a été exécuté sur le build candidat ;
- les versions et lockfiles sont synchronisés ;
- les limitations connues sont écrites dans les notes de version ;
- le mode par défaut a été arbitré et documenté.
- le build candidat est signé et le GO de Ludo est explicite.

NO GO si une donnée simulée peut être confondue avec une donnée réelle, si un
effet externe part sans confirmation ou si la bascule classique ne fonctionne
pas.
