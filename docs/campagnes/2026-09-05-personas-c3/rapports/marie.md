# Marie Exemple, artisane décoratrice (Atelier Exemple) : trace de la campagne

> THÉRÈSE 0.66.1, frontend Vite réel, backend jetable 17393, profil de démonstration.
> Thème clair, 1280×800, DPR 1, locale fr-FR, souris. Session du 05/09/2026.

## Mon impression

_(rédigée en fin de session, voir plus bas)_

## Parcours

### Accueil : comprendre ce qui m'attend et ouvrir un point d'attention

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Arriver sur l'accueil (après purge du stockage et rechargement) | Un brief lisible, mes quatre points d'attention, les parcours proposés | « Bonjour Marie. » + carte « Ton attention aujourd'hui, 4 éléments issus de tes données » ; les quatre éléments sont bien les miens (facture Claire Roux en retard, relance Paul Durand, FACT-2026-002 à relancer, séance 2 Garage Benali). En revanche la rangée « Sources réelles » est à moitié recouverte par le composeur, et les cinq parcours (Écrire/Retrouver/Préparer/Facturer/Décider) sont entièrement cachés dessous : je ne sais pas qu'ils existent. | `01-accueil-arrivee.png` | bug_candidate (marie-01) |
| 2 | Ouvrir le tiroir « Conversations » | La liste de mes conversations | Une seule conversation, « Quelles sont mes tâches urgentes… », identique à `GET /api/chat/conversations` (contrôle d'environnement OK). Le focus part sur le champ de recherche. | `02-accueil-tiroir-conversations.png` | observation |
| 3 | Échap | Le tiroir se ferme, je reviens d'où je viens | Le tiroir se ferme et le focus revient sur le bouton « Conversations » du rail. Comportement juste. | `03-accueil-echap-tiroir-conversations.png` | observation |
| 4 | Basculer le variateur sur « le minimum » | Moins d'éléments, et savoir ce qui est masqué | Deux éléments + « Voir les 2 autres éléments, dont 1 en retard ». Rien n'est caché en douce, j'aime bien. Mais l'étiquette du variateur et les échéances sont en 12 px. | `04-accueil-brief-le-minimum.png` | observation |
| 5 | Faire défiler jusqu'en bas | Voir la fin de la page | Les cinq parcours apparaissent enfin, au-dessus du composeur. Ils existaient donc, mais rien ne me le disait à l'arrivée. | `05-accueil-defilement-bas-etabli-masque.png` | bug_candidate (marie-01) |
| 6 | Revenir sur « l'essentiel » | Les quatre éléments | Les quatre éléments reviennent immédiatement. | `06-accueil-brief-essentiel-4-elements.png` | observation |
| 7 | Cliquer « Claire Roux · FACT-2026-002 · À relancer · 1 440,00 € » | Ouvrir CETTE facture | Ouvre la liste complète « Devis et factures » (10 documents), pas la facture. FACT-2026-002 n'est même pas dans le premier écran : je dois la chercher. | `07-accueil-ouvrir-point-attention-facture.png` | bug_candidate (marie-02) |
| 8 | Échap depuis « Devis et factures » | Retour à l'accueil | Retour à « Bonjour Marie. ». Le focus retombe sur la racine du document, pas sur l'élément que j'avais cliqué. | `08-accueil-echap-retour-depuis-factures.png` | observation |

Arbre d'accessibilité : à l'ouverture du tiroir, focus sur « Rechercher une conversation », région nommée « Conversations » ; sur l'écran Devis et factures, focus sur le titre `heading "Devis et factures"`, mais **les dix cartes de documents sont des `generic [cursor=pointer]` sans rôle ni nom** : rien n'est atteignable au clavier dans la liste.

### Contacts et Pipeline : ouvrir une fiche, corriger une adresse, déplacer un prospect, noter un appel

> Avertissement : un autre persona de la campagne travaillait sur le **même backend** pendant ce
> parcours (fiches `ROBUSTESSE-*`, factures d'essai, 300+ contacts créés entre 13h41 et 13h50).
> Je note ci-dessous ce qui vient de mes propres gestes ; les objets `ROBUSTESSE` ne sont pas de moi.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 9 | Ouvrir « Plus d'outils » | Trouver Contacts | Tiroir « Ce que Thérèse sait mobiliser », 30 capacités rangées par intention. Contacts est sous « Activité », pas évident du premier coup, mais la recherche est là. | `09-contacts-tiroir-plus-outils.png` | observation |
| 10 | Ouvrir la catégorie « Activité » | Les surfaces commerciales | Contacts, Pipeline, Projets, Devis et factures, Livrables. Les mots sont ceux que j'attends. | `10-contacts-tiroir-categorie-activite.png` | observation |
| 11 | Cliquer la carte « Contacts » | Ouvrir mes contacts | Ouvre un panneau latéral « Contacts et contexte — **lecture seule** » plus une carte dans la conversation. Je ne peux rien y corriger ; il faut encore cliquer « Ouvrir Contacts » (bouton présent **trois fois** à l'écran). | `11-contacts-liste.png` | proposal (marie-06) |
| 12 | Cliquer « Ouvrir Contacts » | La vraie liste | Écran Contacts avec Importer / Exporter / Nouveau contact. | `12-contacts-vue-complete.png` | observation |
| 13 | Taper « Claire » dans la recherche | Retrouver ma cliente | Un seul résultat, instantané, sans valider. C'est exactement ce que je veux. | `13-contacts-recherche-claire.png` | observation |
| 14 | Cliquer sur la ligne « Claire Roux » | Voir sa fiche | Ouvre directement le formulaire « Modifier le contact » (avec un bouton Supprimer). Surtout : **le téléphone et l'adresse affichés ne sont pas les siens**, ce sont des exemples gris foncé (`placeholder`) — l'API confirme `phone: null, address: null`. Je crois lire son adresse alors qu'elle n'existe pas. | `14-contacts-fiche-claire-roux.png` | bug_candidate (marie-03) |
| 15 | Saisir « 22 rue des Lices, 04100 Manosque » puis « Mettre à jour » | Enregistrer | La fenêtre se ferme. Aucun message de confirmation, et la ligne de la liste n'affiche pas l'adresse : rien ne me dit que c'est passé. L'API, elle, a bien enregistré. | `15-contacts-adresse-saisie.png`, `16-contacts-apres-mise-a-jour.png` | proposal (marie-07) |
| 16 | Rouvrir la fiche pour vérifier (recherche « Claire » toujours active) | Voir mon adresse | **Le champ est vide**, l'exemple « 14 chemin des Oliviers » est revenu. Je crois que ma saisie a été perdue. | `17-contacts-fiche-adresse-enregistree.png` | bug_candidate (marie-04) |
| 17 | Recliquer « Mettre à jour » (sans rien toucher) | Ne rien casser | **L'adresse enregistrée est effacée en base** (`address` repasse à `null`, `updated_at` 11:46:09). Un simple aller-retour de vérification détruit la donnée. | `18-contacts-adresse-effacee-sans-geste.png` | bug_candidate (marie-04) |
| 18 | Vider la recherche, ressaisir l'adresse, enregistrer, rouvrir | Voir mon adresse | Cette fois l'adresse s'affiche. Le défaut ne se produit que **quand une recherche est active**. | `19-contacts-sans-recherche-adresse-visible.png` | bug_candidate (marie-04) |
| 19 | ⌘K, taper « pipeline » | Ouvrir le pipeline | Deux entrées pour la même chose : « Pipeline » (capacité) et « Ouvrir le Pipeline » (commande). Je choisis au hasard. | `20-pipeline-palette-recherche.png` | observation |
| 20 | Ouvrir le Pipeline | Voir mes étapes | Colonnes Contact / Découverte / Proposition / Signature… la 4e est coupée par le bord, il faut faire défiler à l'horizontale sans que rien ne l'indique. | `21-pipeline-vue.png` | observation |
| 21 | Faire glisser Paul Durand de Découverte vers Proposition (souris) | Le prospect change d'étape | Rien ne bouge (`discovery` reste à 1 côté API), aucune erreur console. **Réserve d'instrument** : le glisser-déposer Playwright ne satisfait pas toujours le seuil de 8 px de dnd-kit ; je ne peux pas conclure que la souris est cassée. | `22-pipeline-apres-glisser-paul-durand.png` | observation |
| 22 | Cliquer sur la carte Paul Durand | Voir sa fiche prospect | Bascule sur l'onglet « Activités ». L'historique affiche **le JSON brut** `{"old_score": 80, "new_score": 90, "reason": "update_stage,source"}` et « Raison: update_stage,source ». | `23-pipeline-clic-carte-paul-durand.png` | bug_candidate (marie-05) |
| 23 | « Ajouter une activité », type Appel, titre + description | Noter mon appel | Boîte claire, bouton grisé tant que le titre manque, ajout immédiat en tête d'historique avec « À l'instant » et l'icône téléphone. Rien à redire. | `24-pipeline-formulaire-activite.png`, `25-pipeline-activite-remplie.png`, `26-pipeline-activite-ajoutee.png` | observation |
| 24 | Reprendre le déplacement au clavier (Espace, →, Espace) | Le prospect change d'étape | **Ça marche**, avec une annonce en français : « Carte de Paul Durand au-dessus de la colonne Proposition. » Après dépôt : Découverte 0, Proposition 2, score 90 → 100 (confirmé par `/api/crm/pipeline/stats`). | `27-pipeline-retour-onglet.png`, `28-pipeline-clavier-prise-carte.png`, `29-pipeline-clavier-au-dessus-proposition.png`, `30-pipeline-clavier-depose-proposition.png` | observation |

Arbre d'accessibilité : les cartes du pipeline sont de vrais `button` avec un nom complet (nom, société, courriel, score et son explication) et une région live française — du bon travail ; en revanche elles portent `aria-roledescription="sortable"`, un mot anglais annoncé à une utilisatrice française. La boîte d'activité s'annonce « Nouvelle activité **CRM** » alors que l'écran dit « Nouvelle activité » (le mot CRM n'est pas dans le lexique).

Console : aucun message d'erreur ni d'avertissement sur tout le parcours. Réseau : tout en 200 ; `GET /api/processing-tasks?limit=30` est appelé en continu (une quarantaine d'appels en deux minutes) alors que le compteur « Travaux » affiche 0 en cours.

### Devis et factures : filtrer les retards, ouvrir une facture, faire un devis, sortir le PDF

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 25 | ⌘K, « factures », Entrée sur le premier résultat | Ouvrir mes devis et factures | Ouvre le **canevas « Facturer un client »** dans la conversation, pas la liste. Les deux entrées de la palette (« Devis et factures » / « Ouvrir les Devis et factures ») portent presque le même nom et mènent à deux écrans différents. | `31-factures-palette-ouverte.png`, `33-factures-canevas-facturer-un-client.png` | bug_candidate (marie-08) |
| 26 | « Ouvrir Devis et factures » | La liste | Liste complète, filtres Type (Tout/Devis/Factures/Avoirs) et Statut. | `32-factures-liste-toutes.png` | observation |
| 27 | Filtre « En retard » | Voir ce qui traîne | Exactement une facture : Claire Roux, FACT-2026-002, 1 440,00 € TTC, échéance 25/08/2026. L'en-tête passe à « 1 document ». Net et rapide. | `34-factures-filtre-en-retard.png` | observation |
| 28 | Ouvrir FACT-2026-002 | Voir la facture de Claire | La fenêtre « Modifier FACT-2026-002 » s'ouvre avec **« Sélectionner un contact » à la place de Claire Roux**, alors que l'API porte bien `contact_id` = Claire. Un bandeau explique honnêtement « Liste incomplète : seuls les 200 contacts les plus récents sont proposés », mais ne dit pas que **le client de cette facture** en fait partie. Si j'enregistre, je perds le client. | `35-factures-detail-fact-2026-002.png` | bug_candidate (marie-09) |
| 29 | « Nouvelle facture » puis type « Devis » | Créer un devis | Le titre devient « Nouveau devis », le champ « Validité (jours) » apparaît, les statuts passent au vocabulaire du devis. Bien vu. (Le bouton de la liste s'appelle « Nouvelle facture » tant que le filtre Devis n'est pas actif.) | `36-devis-nouveau-formulaire-vide.png`, `37-devis-type-devis-client-choisi.png` | observation |
| 30 | Deux lignes : « Conception d'ambiance, salon » 1 × 850 €, « Pose et finitions » 2 × 320 € | Les totaux se calculent | 850,00 € et 640,00 €, TVA 20 %, totaux 1 490 HT / 298 TVA / 1 788 TTC. Calculs justes, mise à jour immédiate. | `38-devis-deux-lignes-saisies.png` | observation |
| 31 | « Créer » | Mon devis est enregistré et je le vois | La fenêtre se ferme, **aucun message**, et la liste reste filtrée sur « En retard » : mon devis n'apparaît nulle part. Je crois que ça a raté. Il est pourtant bien créé (DEV-2026-020, API). | `39-devis-cree-retour-liste.png` | bug_candidate (marie-10) |
| 32 | Filtres « Toutes » puis « Devis » | Retrouver mon devis | DEV-2026-020, Paul Durand, 1 788,00 € TTC, Brouillon, validité 30 jours, en tête de liste. Le bouton de création devient « Nouveau devis ». | `40-devis-filtre-devis-mon-devis.png` | observation |
| 33 | Survoler la carte | Voir les actions | Deux icônes apparaissent au survol seulement, sans libellé visible : un téléchargement et **une croix rouge de suppression**. Les infobulles existent (`Générer et ouvrir le PDF`, `Supprimer`) mais rien n'est visible à froid. | `41-devis-survol-actions-carte.png` | proposal (marie-11) |
| 34 | Cliquer l'icône PDF | Avoir mon devis en PDF | Message honnête « PDF généré — Fichier disponible : /Users/synoptia/Documents-Atelier-Exemple/factures/DEV-2026-020.pdf ». Le fichier existe, il est complet et juste (émetteur, destinataire, 2 lignes, 1 490 / 298 / 1 788, conditions, mentions légales). **Mais il porte « Statut : Brouillon »** : si je l'envoie à Paul, il lit « Brouillon ». Et les montants du PDF n'ont pas le séparateur de milliers (`1490,00 €`) alors que l'écran l'a (`1 788,00 €`) ; le PDF écrit « N. » au lieu de « N° ». | `42-devis-pdf-genere-notification.png` | bug_candidate (marie-12) |
| 35 | « Retour » | Revenir d'où je viens | Retour à la conversation, sans perte. | `43-devis-retour-conversation.png` | observation |

Arbre d'accessibilité : la boîte de création garde le nom accessible « Nouvelle facture » alors que son titre visible est « Nouveau devis » (ce que lit un lecteur d'écran ne correspond pas à l'écran). Les lignes ont de vrais libellés (`Description ligne 1`, `Prix HT ligne 2`), le bandeau de liste incomplète est un `alert`. Console : zéro erreur, zéro avertissement sur tout le parcours.

