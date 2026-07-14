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
11. exporter les données globales, créer puis restaurer une sauvegarde de test ;
12. ouvrir Images, Relances et Voix, vérifier les confirmations et moteurs affichés.

Pour Email, la recette doit vérifier séparément Gmail et IMAP : compte absent,
erreur fournisseur, boîte vide, liste partielle, lecture du corps normalisé,
génération puis modification de la réponse, annulation de la confirmation et
création du brouillon. La création doit être visible chez le fournisseur sans
qu’aucun message soit envoyé.

Pour Devis et factures, vérifier la liste, le détail rechargé par identifiant, le
contact, la devise, les lignes et les totaux. L’ouverture du scénario ne doit
créer aucun document. La confirmation du brouillon doit produire exactement un
devis même en cas de double clic. Aucun bouton d’envoi, de suppression, de
conversion ou de paiement ne doit apparaître dans ce premier canevas.

Pour Rendez-vous, ouvrir le scénario sur une base vide et vérifier qu’aucun
calendrier, événement ou activité CRM n’est créé. Tester local, Google et CalDAV,
une source partielle, deux événements portant le même identifiant sur deux
calendriers, un participant sans contact et plusieurs contacts reliés. Une
création doit afficher calendrier, provider, compte, horaires, fuseau et invités,
puis rester sans effet avant confirmation. Annuler doit conserver zéro mutation ;
confirmer deux fois doit produire un seul événement. Rejouer ces invariants via
le LLM, `/rdv` et `[rdv: ...]`. La note CRM suit une confirmation distincte et
refuse un texte vide.

Pour le Board, vérifier qu’une ouverture ne lance aucun appel, qu’une question
de moins de dix caractères est refusée et que le préflight cloud décrit les
données transmises ainsi que les appels possibles. Tester une séquence SSE
complète, le double lancement, l’annulation, la fermeture du canevas, une erreur
conseiller, une synthèse invalide et un identifiant introuvable après `done`.
Le mode souverain doit échouer si Ollama est absent, sans appeler de provider
cloud. Une décision ne doit être annoncée comme enregistrée qu’après relecture
de son identifiant dans l’historique local.

Pour l’Atelier, vérifier un dépôt propre puis sale, une branche différente de
`main`, deux lancements simultanés, l’annulation pendant une commande et la
fermeture du canevas. Le clone utilisateur doit rester sur `main` et aucune
modification non enregistrée ne doit être commitée. La revue doit comparer
`main` à la branche `agent/*` enregistrée, même si cette branche n’est pas
checkoutée. Tester un résultat sans changement, un test absent ou en échec, un
diff illisible, la suppression de branche en échec et le double clic sur les
actions de revue. Approbation, refus et rollback ne sont réussis qu’après
relecture du statut backend. Vérifier enfin que les profils autonomes et
OpenClaw ne peuvent produire aucun effet métier ou écrire dans le dépôt depuis
le parcours 0.40 initial.

Pour le centre des capacités, vérifier que les 30 cartes possèdent exactement un
débouché. Tester au minimum une vue classique, une action guidée, un onglet de
réglages, une reprise dans le chat et un canevas spécialisé. Une reprise dans le
chat ne doit jamais placer son texte dans l’URL et doit être consommée une seule
fois. Les paramètres `prototype`, `scenario`, `action`, `handoff`, `prompt` et
`settings` doivent être nettoyés après la transition. Personnalisation doit
ouvrir l’onglet Avancé réel, même en mode standard, sans retomber sur Profil lors
du chargement différé de la modale.

Pour les calculateurs, exécuter ROI, ICE, RICE, VAN et seuil de rentabilité avec
des valeurs connues. Vérifier la formule affichée, les bornes de chaque champ,
le passage du taux VAN du pourcentage au décimal, les flux séparés par période,
l’impact RICE canonique et l’arrondi du seuil à l’unité entière supérieure.
Tester un double clic, un résultat extrême non fini et une erreur backend. Aucun
calcul ne doit partir à l’ouverture, être mémorisé ou être transmis à un modèle.

Pour Livrables et suivi client, vérifier que l’ouverture ne produit que des GET
vers Projets, Livrables CRM, Contacts, Tâches et Facturation. Tester un projet
sans livrable, les quatre statuts, une échéance dépassée, une source secondaire
indisponible et l’échec du référentiel principal. La facturation doit être
présentée comme celle du contact relié et jamais comme celle du livrable. Aucune
création, validation, suppression, conversion ou synchronisation ne doit être
accessible dans ce premier canevas.

Tester aussi un projet annulé, un statut ou une date historique inconnus, un
livrable rouvert avec `completed_at`, un changement rapide de projet et un projet
disparu après actualisation. Atteindre les limites de 200 projets, 100 documents
ou 1 000 tâches doit produire un avertissement, jamais un faux état vide.

Pour Confidentialité, vérifier que l’export global contient toutes les familles
métier sans secret de connexion, que la purge exige la saisie de `SUPPRIMER` et
annonce la conservation des audits et sauvegardes. Créer, lister, restaurer et
supprimer une sauvegarde sur une copie de données.

Pour Relances, charger une échéance réelle, modifier sa date et sa note, la
terminer, la rouvrir puis confirmer sa suppression. Pour Voix, vérifier le moteur
choisi, l’absence de transfert avant confirmation, le nom et le format du fichier
envoyé, puis la synthèse Piper locale. Pour Images, vérifier statut, historique,
confirmation avant génération, aperçu et téléchargement.

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

### Dernière recette locale consolidée

Exécutée le 14 juillet 2026 sur le dépôt local, sans bump, tag, signature ni
diffusion :

| Contrôle | Résultat |
|---|---|
| Version | `0.32.1` cohérente dans toutes les sources contrôlées |
| Backend principal | 1 568 réussis, 3 ignorés et 1 succès inattendu sur 1 572 cas hors E2E Python |
| Backend complémentaire | 159 tests réussis, sortie de suite rendue propre |
| Frontend | 541 tests réussis dans 96 fichiers |
| Parcours navigateur 0.40 | 15 scénarios réussis sur Agenda et centre des capacités, dont Images, Relances, Voix, Actions, Calculateurs et Livrables |
| Qualité | Ruff sans défaut ; ESLint sans erreur, avec 25 avertissements historiques tolérés |
| Typage | TypeScript sans erreur |
| Compilation | build web de production réussi |
| Coque native | `cargo check` réussi ; aucun paquet distribué ni signé généré |
| Reconnexion | moteur absent au démarrage, cinq reprises rapides puis contrôle durable ; retour tardif couvert par test |
| Différences | `git diff --check` sans erreur |

Cette recette valide la consolidation du code et les parcours navigateur locaux.
Elle ne vaut pas GO bêta : le premier démarrage du sidecar dans un paquet Tauri,
la revue visuelle du cycle dégradé, le retour arrière sur données
représentatives, la signature et le GO de Ludo restent à exécuter sur le build
candidat.

Les parcours navigateur locaux `parcours-07-rendez-vous-prototype.spec.ts` et
`parcours-08-capacites-prototype.spec.ts` verrouillent respectivement l’absence
de mutation à l’ouverture d’Agenda, la confirmation avant création, la
navigation unifiée, le calculateur ROI, Images, Relances, Voix et Livrables. Ils
complètent les tests unitaires, sans remplacer la recette Tauri sur données de
test.

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

La tête Alembic locale est `d9e0f1a2b3c4`. La migration précédente
`c8d9e0f1a2b3` ajoute les métadonnées historiques du Board ; la tête ajoute
phase, plan, tests, explication, événements, sorties agents, branche de base et
commit à l’Atelier. Leur test aller-retour sur une copie de base et leur downgrade
restent obligatoires avant le build candidat. Aucun champ historique n’est
détourné.

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
