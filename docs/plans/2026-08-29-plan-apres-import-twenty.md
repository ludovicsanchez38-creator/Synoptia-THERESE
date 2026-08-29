# Ce que l'import des vraies données a révélé - plan

> 29 août 2026. Import du CRM Twenty de Ludo dans sa THÉRÈSE 0.57.0 :
> 74 contacts, 74 tâches, 120 notes historiques. Design challenge Grok +
> vérifications directes dans le code. Chaque constat ci-dessous porte sa
> mention **vérifié** ou **non vérifié**.

## En une phrase

L'import n'a pas révélé des bugs : il a révélé que **THÉRÈSE range des gens là
où Twenty suit des affaires**. Tout le reste en découle.

## Le manquement de fond

**THÉRÈSE n'a pas d'objet « affaire ».** Le pipeline commercial est une
propriété du contact (`Contact.stage`), pas une entité. Conséquences mesurées
sur les vraies données :

- Les 78 opportunités de Twenty n'ont **aucune maison**. 8 sont vivantes
  (SCREENING, PROPOSAL, NEGOCIATION), elles n'ont pu entrer que comme une ligne
  de texte dans les notes du contact.
- Un client qui rouvre une négociation ne peut pas être `active` et
  `proposition` à la fois. Une personne, une étape.
- Montant, BANT, objections, offre recommandée : nulle part où les poser.

Tant que cet objet n'existe pas, chaque donnée réelle posée dans THÉRÈSE devra
soit mentir, soit disparaître.

## Les manquements vérifiés, par ordre de coût

### 1. Deux définitions du même « à relancer » (vérifié, mesuré)

| Chemin | Règle | Sur les vraies données |
|---|---|---|
| Le brief (`dashboard.py:413`) | `stage IN ('contact','discovery')` ET (`last_interaction` NULL **OU** < 15 j) | **24** |
| La cloche (`notification_service.py:166`) | `stage IN ('contact','discovery','proposition')` ET `last_interaction` **NON NULL** ET < seuil | **20** |

Quatre contacts sans date sont comptés par l'accueil et ignorés par les
notifications. Deux bouches, deux chiffres, même question. C'est le motif des
« jumeaux » : une règle posée sur un chemin, pas balayée sur les autres.

### 2. THÉRÈSE déduit une relance que Ludo a déjà décidée (vérifié)

Twenty porte une **date de prochaine relance** sur 24 fiches. THÉRÈSE n'a aucun
champ pour la recevoir : `Contact` n'a que `last_interaction` (le passé), et
`EmailFollowUp.email_message_id` est une clé étrangère **obligatoire**, donc une
relance CRM sans e-mail est impossible à représenter.

Elle déduit donc un devoir d'une absence, au lieu de lire une décision. À
l'import, ces 24 dates ont dû devenir des tâches datées : honnête, mais ce
n'est pas du CRM.

**Le plus petit geste utile : un champ `next_follow_up` sur `Contact`**, lu par
le brief en priorité sur la règle des 15 jours.

### 3. Un contact importé est invisible dans le CRM (vérifié)

`CRMPanel.tsx:40` : `allContacts.filter((c) => !!c.source)`. Un contact sans
`source` apparaît dans le brief (« Relancer Dupont »), et le clic ouvre un
pipeline où il n'est pas. Deux chemins de création, deux visibilités.
L'import a contourné en posant `source='twenty'` ; le défaut reste.

### 4. `Contact.extra_data` est un trou noir (vérifié)

Absent de `ContactCreate`, `ContactUpdate`, `ContactResponse`, de la réponse
API, du contexte du chat et du texte d'embedding. Seuls lecteurs : l'export de
sauvegarde et l'effacement RGPD. **Y ranger une donnée, c'est la jeter avec des
étapes en plus.** C'est pour ça que BANT, objections et signaux d'achat sont
partis dans un fichier d'archive plutôt que dans ce champ.

### 5. L'import n'indexe pas la recherche sémantique (vérifié)

Aucun appel d'embedding dans le chemin d'import. Les 74 contacts sont
trouvables par leur nom, invisibles à la recherche sémantique. Le chat qui « ne
trouve pas Garcia » alors que Garcia est en base : une affirmation par omission.

### 6. Les routes d'écriture jettent les champs qui font marcher le brief (vérifié)

Ni `POST /api/data/import/contacts` ni `POST /api/memory/contacts` n'acceptent
`last_interaction`. Un import par l'API aurait produit **74 fausses relances**
au premier écran. L'import a dû écrire par la couche SQL.

### 7. Le MCP existe, la porte n'existe pas (vérifié)

`mcp_therese_server.py` est un serveur JSON-RPC complet (protocole 2024-11-05)
qui expose **14 outils** : `list_contacts`, `get_contact`, `create_activity`,
`list_emails`, `draft_email`, `send_email`, `list_invoices`, `create_invoice`,
`list_tasks`, `create_task`, `list_events`, `create_event`, `search_memory`,
`get_project`.

Il n'est lancé qu'en stdio, par les sous-agents internes (`agents.py:1197`).
Aucune route ne l'expose, rien ne le documente. **Le chantier n'est pas de
construire les outils : c'est d'ouvrir la porte, l'authentifier et l'écrire.**

## Non vérifié, à confirmer avant d'agir

- Le score de THÉRÈSE serait recalculé par une formule qui écraserait une valeur
  importée (je n'ai pas retrouvé la formule là où elle était annoncée). Par
  précaution, l'import n'a **pas** recopié les scores Twenty.
- Pagination silencieuse annoncée : contacts 200, dossiers 50 dans le sélecteur
  de conversation.
- `POST /api/crm/activities` forcerait `last_interaction = maintenant`.

## Ordre proposé

1. **Le champ `next_follow_up`** (petit, et il empêche l'accueil de mentir).
2. **Réconcilier les deux définitions** de « à relancer », une seule fonction,
   les deux chemins l'appellent.
3. **Ouvrir le MCP** : une route, un jeton, une page de doc.
4. **L'objet « affaire »**. Gros. C'est le vrai sujet, et rien ne le remplace.

Les points 3, 4, 5 et 6 de la liste vérifiée sont des corrections d'un
après-midi chacune, à caler entre les deux.

## Ce qui n'a pas été importé, et pourquoi

- **63 opportunités mortes** (33 perdues, 30 clients sans chantier) : ce ne sont
  pas des dossiers, et 78 dossiers noieraient un sélecteur qui en affiche 50.
- **235 notes machine** (`client_created - <horodatage>`) : filtre de forme.
- **BANT, objections, signaux d'achat, secteur, scores** : aucune surface ne les
  lit. Dans `~/import-twenty-archive.json`, pas dans la base.
- **Les 81 sociétés sans personne** : THÉRÈSE n'a pas d'entité société, les
  créer en contacts fabriquerait 81 cartes de plus.

---

## Deuxième passe : ce que le CONTENU des notes a révélé (29/08, soir)

Les sept manquements ci-dessus parlent de **forme**. Le contenu réel des
120 notes importées parle d'autre chose, et c'est plus grave.

### Le manquement que la forme cachait : THÉRÈSE n'a pas de fait

Les notes de Ludo passent leur temps à **s'annuler l'une l'autre** :

> « CORRECTION de ma note de ce matin : le dossier AFDAS est DEPOSE ET VALIDE »
> « CORRIGE LA NOTE DE 15h40 DU MÊME JOUR, qui disait FORGER » (écart de 2 000 €)
> « Cette note trace une **déclaration**, pas un constat »
> « VÉRIFIÉ À LA SOURCE, sur ses propres feuilles d'émargement »

THÉRÈSE n'a que des textes. Une `Activity` n'a ni statut « annulée », ni lien
vers celle qu'elle remplace, ni distinction entre **déclaré**, **vérifié à la
source** et **déduit**. `read_contact` envoie au modèle le bloc `notes` **et**
les cinq activités les plus récentes, à égalité. La timeline les affiche toutes
avec la même icône.

**Le dégât est déjà en base** : un résumé de fiche dit encore « FORGER 490 € »
alors qu'une note du 27/08 sur la même fiche dit « PROPULSER, 2 490 € ».

### Le métier que les notes révèlent, et qu'aucun objet ne porte

- une **séance** bloquée par une attestation fiscale (l'OPCO écrit de ne pas la tenir) ;
- un **dossier de financement** (déposé / validé / refusé), distinct de la personne ;
- un **questionnaire à froid J+90**, dont l'échéance court depuis la fin de formation ;
- un **encaissement partiel** (l'OPCO règle le HT, le client la TVA).

`Invoice.status` vaut `draft | sent | paid | overdue | cancelled` : pas de
partiel, pas de deux payeurs. `Task` n'a pas de `contact_id`. L'objet
« affaire » absorberait le montant et l'étape ; il n'absorberait pas
« l'attestation bloque la séance de lundi ».

### L'ordre du plan initial était mauvais

`next_follow_up` en premier est un piège de remplissage : le champ vide,
l'accueil continue d'inférer ; le champ rempli par une heuristique, c'est une
date qui **a l'air** d'une décision. Et poser ce champ sans reprendre les
74 tâches créerait une **troisième** définition de « à relancer ».

Ordre corrigé :

1. **Faire taire ce qui parle déjà faux** : 51 tâches périmées (dont deux de
   janvier 2025), les notifications du jour, le résumé qui dit encore FORGER,
   les deux contacts de test E2E mêlés aux 74 vrais.
2. **Une seule définition de relance, et c'est une date posée** : copier les
   24 dates Twenty, brancher les deux heuristiques dessus quand elle existe,
   **silence** sinon.
3. **`Task.contact_id`**, sans quoi ces 74 lignes sont des chaînes de caractères.
4. **L'objet affaire.**
5. **Le MCP**, seulement une fois décidé qui est la source (Twenty ou THÉRÈSE) :
   une deuxième porte d'écriture fabrique deux vérités divergentes.
6. **La rétractation** (fait courant, note qui annule) et les objets d'organisme
   de formation. Ce n'est pas un après-midi.

### Corrections à mes propres constats

- **La formule de score existe** (`scoring.py` : base 50 + email 20 + téléphone
  15 + société 10 + `active` 50). Je l'avais classée « non vérifiée ». Ne pas
  avoir importé les scores Twenty était juste ; ne lancer aucun recalcul global.
- **`limit` est plafonné à 200** sur la liste des fichiers, en HTTP 200 : le
  même piège de pagination silencieuse que celui documenté côté Twenty.

### Le corpus de Syn : ce qui est entré, et ce qui a été refusé

Sur 569 fiches rapatriées, **32 sont indexées** (317 chunks). Les 271
`feedback_*` avaient été indexées puis **retirées** : ce sont des règles de
conduite d'agent, pas de la matière métier. Les avaler aurait fait remonter une
leçon d'agent au même rang qu'un compte-rendu client, et THÉRÈSE se serait mise
à parler comme Syn. Critère retenu : **un client nommé, ou une obligation de
Ludo.** Tout ce qui documente la fabrication des outils est resté dehors.

### Le piège du corpus de test, et le protocole qui l'évite

La familiarité va faire illusion : les noms sont les bons, Ludo reconnaîtra
ses clients et croira que ça marche. Le test honnête écrit **la réponse
attendue et sa source avant d'ouvrir l'app**. Quatre épreuves :

1. **La contradiction** : « le dossier AFDAS est-il déposé ? » Si THÉRÈSE cite
   les deux notes à égalité, c'est un échec. Dire « j'ai deux notes qui se
   contredisent » vaut mieux que la bonne réponse.
2. **Le compte** : combien de relances aujourd'hui ? Trois chiffres coexistent
   (24, 20, 51). Toute réponse unique est un mensonge.
3. **Le silence** : « où en est la facture AES de 3 348 € ? » THÉRÈSE a zéro
   facture. La bonne sortie est « je ne l'ai pas », pas un résumé plausible.
4. **Le sabotage** : masquer la note de correction, reposer la question. Si le
   résumé continue d'affirmer l'état faux, on a mesuré que l'état courant est un
   paragraphe écrit à la main, pas un objet.

