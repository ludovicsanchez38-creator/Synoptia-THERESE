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
