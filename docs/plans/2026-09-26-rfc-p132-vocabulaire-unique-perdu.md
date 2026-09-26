# RFC P-132, seconde moitié : un seul vocabulaire d'avancement, et l'étape « Perdu »

Rédigé le 26/09/2026. La décision est prise depuis le 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:194-195`) : « un seul vocabulaire d'avancement (celui du pipeline), étape terminale « Perdu », exclue des prospects en cours ». Ce document dit comment la tenir sans rien perdre, et dans quel ordre la livrer. La première moitié de P-132 (un champ « Étape » sur la fiche) est livrée depuis le 25/09 (commit `221de791`, `src/frontend/src/components/crm/CRMPanel.tsx:319-332`).

Aucune question n'est laissée à Ludo : la migration réécrit des valeurs, elle n'efface rien.

## 1. Le constat

Nathalie, persona du cycle 13, ouvre la fiche d'Élodie. Le Pipeline lui parle en sept colonnes : Contact, Découverte, Proposition, Signature, Livraison, Actif, Archive. Sous la même fiche, la prestation d'Élodie lui propose un autre jeu : Piste, Proposition envoyée, Signée, Perdue, En cours, Terminée (`docs/campagnes/2026-09-25-personas-c13/rapports/nathalie.md:54`). Le constat nathalie-09 le résume (`nathalie.md:164-165`) : deux vocabulaires pour dire où en est une vente, et pas de « Perdu » dans le pipeline.

## 2. Ce qui existe

### 2.1 Les étapes d'un contact

- Le domaine est un `Literal` de sept valeurs, `EtapePipeline` (`src/backend/app/models/schemas.py:242-250`). Il gouverne la création (l.298), la mise à jour (l.384), le déplacement dans le pipeline (l.1468) et la création côté CRM (l.1574).
- Les libellés vivent deux fois, avec un commentaire qui dit leur lien : `PIPELINE_ETAPES` à l'écran (`src/frontend/src/components/crm/pipelineEtapes.ts:7-15`) et `LIBELLES_ETAPES` au moteur (`src/backend/app/services/crm_utils.py:25-36`).
- **Contrainte B-167** (`schemas.py:237-241`) : la vue Kanban groupe les fiches en parcourant les colonnes connues, sans repli (`src/frontend/src/components/crm/PipelineView.tsx:66-73`). Une étape absente de `PIPELINE_ETAPES` ferait disparaître la carte sans un mot. Toute étape ajoutée au domaine est donc forcément une colonne.
- Le score ajoute des points par étape (`src/backend/app/services/scoring.py:33-41`, appliqués l.74-76, plancher 0 l.89). Le commentaire de `archive` dit tout du problème : « Perdu ou terminé ». Le pipeline mélangeait déjà deux issues opposées dans une seule colonne.
- `archive` est aussi le **tombeau RGPD** : l'anonymisation y pose la fiche (`src/backend/app/services/rgpd_identite.py:33`, `src/backend/app/routers/rgpd.py:195`) et les relances l'excluent pour ne jamais afficher « Relancer [ANONYMISÉ] » (`src/backend/app/services/relances.py:43-46`).
- Les « prospects en cours » de l'Accueil comptent une liste blanche, `ETAPES_DE_PROSPECT` (`src/backend/app/routers/dashboard.py:539-541`, lue l.641-646). L'écran la recopie dans `ORDRE_DES_ETAPES` (`src/frontend/src/components/prototype/CetteSemaine.tsx:14`, lue l.76-77 et l.126-135).

### 2.2 Les phases d'une prestation

- Six valeurs, `PHASES_DE_PRESTATION` (`src/backend/app/models/entities.py:113-114`), dont quatre « ouvertes » (`PHASES_OUVERTES`, l.115-116).
- Le modèle s'en explique (`entities.py:122-148`) : la prestation n'est pas une opportunité, elle couvre la vente **et** le suivi, là où le Kanban des contacts « en a sept qui ne parlent que de vente ».
- Le routeur exige la phase à la création, sans défaut (`src/backend/app/routers/prestations.py:38-40`), et la vérifie contre la liste (l.107-112, appelée l.138 et l.168).
- L'écran : `ListeDesPrestations.tsx` (sélecteur par ligne l.99-113, sélecteur de création « Où ça en est » l.131-143, présélection visible `'piste'` l.38) et ses libellés dans `src/frontend/src/services/api/prestations.ts:10-29`.
- Les lecteurs : l'état courant de la fiche, lu par le chat et le MCP, ne garde que les prestations ouvertes (`src/backend/app/services/memory_tools.py:986-993`, `1012-1014`, `1133-1152`) ; l'export d'un contact au titre du RGPD (`rgpd.py:137-149`) ; l'export complet (`src/backend/app/routers/data.py:232` et `348`) ; l'effacement total (l.674) ; l'anonymisation, qui supprime les prestations (`rgpd.py:214-220`).

### 2.3 Pourquoi deux champs restent deux champs

Une fusion stricte, qui ne garderait que `Contact.stage`, perdrait une information que le code protège par un test : « une personne, une étape, c'est faux. Un client qui rouvre une négociation est à la fois en cours et en proposition » (`tests/test_prestation.py:29-43`). L'état courant que lit l'assistante dérive des prestations ouvertes, pas de l'étape de la fiche (`memory_tools.py:1012-1013`).

**« Un seul vocabulaire » veut donc dire : mêmes identifiants, mêmes libellés, une seule source, sur deux champs.** `Contact.stage` dit où en est la relation avec la personne ; `Prestation.phase` dit où en est chacune de ses ventes. Les deux parlent la langue du pipeline.

## 3. La correspondance, tranchée

| Phase actuelle | Libellé actuel | Étape du pipeline | Libellé | Ce qui change à la lecture |
|---|---|---|---|---|
| `piste` | Piste | `discovery` | Découverte | Rien de substantiel : une prestation qui porte un intitulé suppose un besoin repéré, c'est-à-dire une découverte engagée |
| `proposition` | Proposition envoyée | `proposition` | Proposition | L'adjectif tombe ; le score le disait déjà (« Offre envoyée », `scoring.py:36`) |
| `gagne` | Signée | `signature` | Signature | Voir ci-dessous (1) |
| `perdue` | Perdue | `lost` (nouvelle) | Perdu | Aucun |
| `en_cours` | En cours | `delivery` | Livraison | Le score le disait déjà (« Projet en cours », `scoring.py:38`) |
| `terminee` | Terminée | `archive` | Archive | Voir ci-dessous (2) |

La correspondance est **injective** : six valeurs distinctes vont vers six étapes distinctes. La migration ne confond donc aucune prestation avec une autre, et elle se défait exactement (§5.2).

**Les prestations n'offrent que six des huit étapes.** « Contact » et « Actif » décrivent une personne (un premier contact, un client actif), pas une vente : une prestation « Actif » se lirait « en cours », ce qui est faux, et une prestation « Contact » ne dirait rien. Le sélecteur d'une prestation propose Découverte, Proposition, Signature, Livraison, Perdu, Archive, dans l'ordre du pipeline. Ce sont les mêmes mots, tirés de la même liste ; il n'y a pas de second vocabulaire.

**(1) Signée devient Signature.** Le score commente la colonne « En attente signature » (`scoring.py:37`), la prestation disait « Signée ». La prestation n'a jamais distingué les deux : elle n'avait pas d'état « en attente de signature », donc la migration ne perd rien. La définition retenue, écrite dans le commentaire de `STAGE_SCORES` et dans le lexique : **Signature = l'accord est donné ou en cours de formalisation, la livraison n'a pas commencé.** Elle vaut pour un contact comme pour une prestation.

**(2) Terminée devient Archive.** C'est le seul endroit où le mot change vraiment de ton. L'information, elle, reste entière : une fois « Perdu » séparé, une prestation close est soit Perdu, soit Archive, et Archive ne peut plus vouloir dire que « menée à son terme ». Le questionnaire à froid (J+90) ne dépend pas de la phase mais de la date de fin (`prestations.py:67-78`) : rien ne se perd pour Qualiopi. Trois autres voies ont été pesées et écartées :

- **Terminée vers Actif** : « Actif » se lit « en cours » sur une prestation, contresens.
- **Renommer « Archive » en « Terminé » dans tout le pipeline** : cela change un mot du vocabulaire qui fait foi, alors que la décision garde celui du pipeline ; cela rouvre B-1416, qui vient d'écrire « Archive » dans les exports tableur (`crm_utils.py:25-36`, commit `2e15dd28`), et les tableurs déjà exportés chez les testeurs ; et une fiche anonymisée se lirait « Terminé ».
- **Une neuvième étape « Terminé »** : une colonne de plus au Kanban pour un mot dont seules les prestations ont besoin.

## 4. L'étape « Perdu »

- **Identifiant `lost`, libellé « Perdu »**, placée après `active` et avant `archive` : les deux issues terminales ferment la grille, Archive restant la dernière comme tombeau RGPD. Ajoutée à `EtapePipeline`, à `PIPELINE_ETAPES` et à `LIBELLES_ETAPES`, dans le même ordre.
- **Huitième colonne du Kanban**, par la contrainte B-167. La grille défile déjà en largeur, au clavier compris (B-1426, `PipelineView.tsx:163-172`). Le commentaire « 7 stages » (`PipelineView.tsx:4`) devient faux et suit.
- **Étiquette** : ton `neutre` (`src/frontend/src/components/ui/Etiquette.tsx:16`), comme Archive. Une vente perdue n'est pas une erreur ; le mot porte le sens, pas la couleur.
- **Création d'une fiche** : le formulaire exclut déjà Archive (`CRMPanel.tsx:455`) ; il exclut aussi Perdu. Le moteur, lui, accepte `lost` partout, pour que l'import et la synchro puissent l'apporter.
- **Score** : `lost` vaut −100, exactement comme `archive` aujourd'hui. Qui rangeait ses ventes perdues en Archive et les déplace vers Perdu garde le même score. Le commentaire de `archive` devient « Terminé, ou fiche effacée (RGPD) ».
- **Prospects en cours** : exclu par construction, puisque `ETAPES_DE_PROSPECT` est une liste blanche qui ne le contient pas. Un test le fige (§6, lot 1). Côté écran, `ORDRE_DES_ETAPES` disparaît : `CetteSemaine` parcourt `PIPELINE_ETAPES` et ne garde que les étapes que le moteur lui rend. Le moteur devient la seule source de ce qui compte comme prospect, et l'ordre vient du vocabulaire unique.
- **Relances** : Perdu n'est **pas** exclu. Une date de relance est une décision de l'utilisatrice (`entities.py:41-43`) ; « perdu, je le rappelle dans six mois » est un geste commercial courant. Seul `archive` reste exclu, pour la raison RGPD de `relances.py:43-46`.
- **Base légale RGPD** : l'inférence range tout ce qui n'est pas Actif, Signature ou Livraison en intérêt légitime (`rgpd.py:657`). Perdu y tombe, ce qui est juste : un prospect perdu n'a jamais signé. Un test le fige.
- **Aucune migration des contacts.** Une fiche en `archive` aujourd'hui peut être terminée, perdue ou anonymisée ; rien ne permet de les distinguer. Les déplacer serait deviner. La colonne Perdu démarre vide et chacun y range ses fiches à la main.

## 5. La migration des prestations

### 5.1 Où elle tourne

L'application empaquetée ne lance jamais `alembic upgrade head` au démarrage (`src/backend/app/models/database.py:322-325`). Le démarrage enchaîne `create_all` (l.1113), les migrations ad hoc idempotentes (`apply_adhoc_migrations`, l.255, appelée l.1167) puis l'estampille (`ensure_alembic_stamp`, l.642, appelée l.1173). Le pré-vol d'Alembic rejoue les mêmes migrations ad hoc (`src/backend/alembic/env.py:153-155`). Il faut donc les trois pièces, comme pour chaque révision depuis US-015 :

1. **Une étape ad hoc idempotente** dans `apply_adhoc_migrations`, juste après la création de la table `prestations` (`database.py:329-341`) :
   `UPDATE prestations SET phase = CASE phase WHEN 'piste' THEN 'discovery' WHEN 'gagne' THEN 'signature' WHEN 'perdue' THEN 'lost' WHEN 'en_cours' THEN 'delivery' WHEN 'terminee' THEN 'archive' END WHERE phase IN ('piste', 'gagne', 'perdue', 'en_cours', 'terminee')`.
   `proposition` ne bouge pas. La clause `WHERE` rend l'étape sans effet dès le deuxième démarrage ; elle ne réécrit jamais `updated_at`, puisque la prestation n'a pas changé pour l'utilisatrice.
2. **Une révision Alembic de données**, chaînée sur la tête du moment (`b8c9d0e1f2a3` aujourd'hui, `database.py:619`, ou la révision de P-104 si elle arrive avant). Elle vérifie d'abord que la table existe (aucune révision ne la crée, elle naît de `create_all` ou de l'étape ad hoc), puis joue le même `UPDATE`. Le `downgrade` joue la correspondance inverse, et ramène les contacts `lost` en `archive`, leur ancien sens.
3. **La preuve d'estampillage étendue.** Le code l'exige (« Toute future révision doit étendre cette preuve », `database.py:688-692`). Jusqu'ici la preuve ne portait que sur le schéma (l.745-759) ; cette révision n'ajoute aucune colonne, sa preuve est donc **un état des données** : si la table `prestations` existe, aucune ligne ne porte une valeur héritée. La table absente vaut preuve (une base sans prestation n'a rien à migrer) : la base de test `_make_patched_tracked_db` n'a pas cette table (`tests/test_alembic_stamp.py:98-137`) et doit continuer d'être ré-estampillée.

`ALEMBIC_HEAD_REVISION` passe à la nouvelle révision ; `test_constante_epinglee_suit_la_vraie_tete` (`test_alembic_stamp.py:139-153`) le vérifie.

**Pourquoi pas un marqueur dans `preferences`**, comme la conversion des journées entières de BUG-144 (`database.py:556-608`) ? Le marqueur dit « fait une fois », la clause `WHERE` dit « il n'y a plus rien à faire », et la preuve d'état vérifie les valeurs elles-mêmes. Il n'y a pas de marqueur à oublier dans une restauration ou un import.

### 5.2 Les cas de bord

- **Le défaut `'piste'` du DDL ad hoc** (`database.py:334`). Le modèle n'a plus de défaut depuis la 0.59, et un test l'exige (`tests/test_prestation.py:182-202`). Le littéral du `CREATE TABLE IF NOT EXISTS` perd son `DEFAULT 'piste'`. Sur les bases existantes, SQLite garde le défaut dans le schéma : c'est sans effet, puisque l'ORM écrit toujours la phase, et une insertion brute qui l'omettrait serait remise d'aplomb au démarrage suivant par l'étape ad hoc.
- **Une valeur inconnue** (ni héritée, ni du nouveau domaine) : laissée telle quelle, journalisée une fois par processus (amendé le 26/09, constat 4 de la revue du diff : `apply_adhoc_migrations` tourne deux fois par démarrage), jamais remplacée par un défaut. À l'écran, le sélecteur la montre honnêtement (« Étape inconnue : xyz ») au lieu d'afficher la première option, ce que ferait un `<select>` dont la valeur manque à la liste. La preuve d'estampillage ne regarde que les valeurs héritées, pour ne pas bloquer une base sur une donnée étrangère.
- **La restauration d'une sauvegarde d'avant P-132.** La restauration ferme la base (`data.py:1587`) puis la rouvre par `init_db` (`data.py:1665`, `_rouvrir_la_base_apres_restauration`, l.1442-1453) : l'étape ad hoc tourne sur les données restaurées. Un test le prouve (lot 3).
- **L'export complet** change de contrat : `data_format_version` passe de 1.4 à 1.5, selon la règle écrite à côté (`data.py:259-262`) ; `tests/test_routers_data.py:152` suit.
- **Le MCP et l'assistante** (amendé le 26/09, constat 2 de la revue du design puis constat 2 de la revue du diff). `PHASES_OUVERTES` devient `("discovery", "proposition", "signature", "delivery")`. Le modèle ne reçoit plus l'identifiant d'une prestation : « signature » tout court se lit « en attente de signature », alors qu'une prestation « Signée » avant P-132 y a été rangée. L'état courant rend donc, pour chaque prestation ouverte, `etape` (le libellé : « Signature ») et `definition_de_l_etape` (« l'accord est donné ou en cours de formalisation, la livraison n'a pas commencé »), à la place de `phase`. C'est un changement de contrat pour tout client MCP. La fiche elle-même (`read_contact` au chat, `get_contact` au MCP) garde `stage` en identifiant, la même forme que `list_contacts`, et ajoute `etape` et `definition_de_l_etape` ; les définitions des huit étapes vivent dans `DEFINITIONS_ETAPES` (`crm_utils.py`). La consigne donnée au modèle (`CONSIGNE_DE_LECTURE`) ne cite aucune étape et ne change pas.

## 6. Effets, surface par surface

| Surface | Ce qui change | Ancre |
|---|---|---|
| Domaine des étapes | `lost` ajouté, après `active` | `schemas.py:242-250` |
| Libellés moteur et écran | « Perdu » dans les deux listes, même ordre | `crm_utils.py:25-36`, `pipelineEtapes.ts:7-15` |
| Score | `lost` : −100 ; commentaires de `signature` et `archive` réécrits | `scoring.py:33-41` |
| Tableau de bord | liste blanche inchangée, test d'exclusion ajouté | `dashboard.py:539-541` |
| Cette semaine | `ORDRE_DES_ETAPES` retiré, ordre tiré de `PIPELINE_ETAPES` | `CetteSemaine.tsx:14`, `76-77` |
| Relances | inchangées (Perdu relancé si une date est posée) ; test | `relances.py:43-46` |
| Export tableur | écrit « Perdu » par `LIBELLES_ETAPES` ; le filtre `stage` accepte `lost` | `crm_export.py:55`, `169-171` ; `crm.py:628-652` |
| Import tableur | lit « Perdu » et « lost » par `etape_depuis_cellule` ; l'aperçu (P-130) ne le signale plus comme inconnu | `crm_utils.py:44-51` ; `crm_import.py:686-691`, `776-783` |
| Import JSON de contacts | accepte `lost` (le domaine est lu, pas recopié) | `data.py:1916-1918`, `1986` |
| Synchro Google Sheets | passe par `etape_depuis_cellule` : « Perdu » et « Découverte » y sont enfin reconnus, comme à l'import (B-1416 a décidé que l'import accepte les deux formes) | `crm_utils.py:379-383` |
| Base légale RGPD | Perdu en intérêt légitime ; test | `rgpd.py:657` |
| Agent « Relance clients » | reçoit le libellé (« étape : Perdu »), plus l'identifiant | `src/backend/app/services/action_agents.py:356` |
| Changement d'étape | la frise traduit déjà par `libelleDEtape` | `src/frontend/src/lib/activitesCrm.ts:46-59` |
| Kanban | huitième colonne | `PipelineView.tsx:39`, `172` |
| Fiche du contact | le sélecteur « Étape » offre Perdu | `CRMPanel.tsx:331` |
| Création d'une fiche | Perdu exclu, comme Archive | `CRMPanel.tsx:455` |
| Prestations | six étapes du pipeline ; le libellé « Où ça en est » devient « Étape » (le mot de la fiche) ; « Phase de … » devient « Étape de … » ; présélection visible Découverte | `ListeDesPrestations.tsx:38`, `102`, `132` ; `prestations.ts:10-29` |
| État courant (chat, MCP) | `PHASES_OUVERTES` réécrit ; `etape` et `definition_de_l_etape` à la place de `phase` | `entities.py`, `memory_tools.py` (`_etat_courant`) |
| Fiche lue par le modèle (chat, MCP) | `stage` reste l'identifiant ; `etape` et `definition_de_l_etape` ajoutés | `memory_tools.py` (`fiche_selon_le_contrat`) |
| Création d'une fiche CRM | la ligne poussée à la feuille « Clients » porte le libellé de l'étape | `routers/crm.py` |
| Skill de proposition | reçoit l'étape (en libellé) et le score de la fiche | `routers/skills.py`, `text_skills.py` |
| Export complet | version 1.5 | `data.py:262` |

La synchro Sheets n'est pas à sens unique (amendé le 26/09, constat 1 de la revue du design) : la synchro lit le tableur vers THÉRÈSE (`crm_sync.py`), mais la création d'une fiche CRM pousse une ligne dans la feuille « Clients » (`routers/crm.py`, `create_crm_contact`). Cette ligne porte désormais le libellé de l'étape (« Perdu »), comme l'export tableur, et la synchro le relit par `etape_depuis_cellule` ; un test le prouve de bout en bout. Rien d'autre n'est réécrit dans le tableur : une cellule « archive » y reste Archive, et la règle B-1187 (« le tableur fait foi pour ce qu'il dit ») ne change pas.

## 7. Mise en œuvre, lot par lot

Chaque lot : tests écrits d'abord et vus rouges, sabotage ciblé par fonction (règle du 27/08), un commit, revue adverse du diff. L'ordre compte : le lot 3 a besoin de `lost` dans le domaine.

### Lot 1 : « Perdu » au moteur

Tests à écrire d'abord (pytest) :
- `PATCH /api/crm/contacts/{id}/stage` avec `lost` rend 200, écrit l'activité de changement et le score de la règle (base, coordonnées, −100, plancher 0) ;
- `GET /api/dashboard/semaine` : une fiche `lost` n'entre pas dans `prospects_par_etape` (à côté de `tests/test_p135_accueil_semaine.py:30-48`) ;
- `contacts_a_relancer` rend une fiche `lost` dont la date est échue, et jamais une fiche `archive` (à côté de `tests/test_relance_une_seule_definition.py`) ;
- l'export tableur écrit « Perdu » ; l'import tableur relit « Perdu », « perdu » et « lost » (à côté de `tests/test_b1416_export_tableur_en_francais.py`) ;
- l'import JSON de contacts garde `lost` ;
- la synchro Sheets accepte « lost » et « Perdu », et laisse l'étape en place sur une cellule inconnue (à côté de `tests/test_b1187_synchro_contact_ne_vide_pas.py`) ;
- l'inférence RGPD range `lost` en intérêt légitime ;
- l'agent « Relance clients » reçoit « étape : Perdu ».

Commentaires qui deviennent faux et suivent dans le même commit : la liste des étapes de `Contact.stage` (`src/backend/app/models/entities.py:37`) et celles de `STAGE_SCORES` (`scoring.py:34-40`).

Critère observable : sur une base de démonstration, une fiche passée en Perdu par l'API disparaît du compteur « Prospects en cours » de l'Accueil et apparaît « Perdu » dans un export tableur.

### Lot 2 : « Perdu » à l'écran

Tests à écrire d'abord (vitest) :
- le Kanban rend huit colonnes nommées, Perdu entre Actif et Archive (`CRMPanel.da.test.tsx:210` passe de 7 à 8) ;
- déposer une carte sur Perdu au clavier l'annonce et appelle `/stage` avec `lost` ;
- le sélecteur « Étape » de la fiche propose Perdu ; le formulaire de création ne propose ni Perdu ni Archive ;
- la frise affiche « Étape : Proposition → Perdu » ;
- `CetteSemaine` suit l'ordre de `PIPELINE_ETAPES` et n'affiche que les étapes rendues par le moteur ; une clé inattendue ne s'invente pas un libellé.

Commentaires qui deviennent faux et suivent : l'en-tête « Les sept étapes du pipeline » (`pipelineEtapes.ts:2`) et « Vue Kanban du pipeline commercial avec 7 stages » (`PipelineView.tsx:4`).

Critère observable : dans l'application lancée, Nathalie range Karim en Perdu depuis la fiche, la carte change de colonne, l'Accueil compte un prospect de moins.

### Lot 3 : les prestations parlent le pipeline (moteur et migration)

Tests à écrire d'abord (pytest) :
- une base qui porte les six anciennes valeurs sort de `apply_adhoc_migrations` avec les six nouvelles, `updated_at` intact ; un second passage ne change rien ;
- une valeur inconnue traverse intacte, et le démarrage le journalise ;
- `upgrade` puis `downgrade` de la révision rendent les valeurs de départ ;
- `ensure_alembic_stamp` refuse de ré-estampiller une base ancienne qui porte encore une valeur héritée, et ré-estampille une base sans table `prestations` (`tests/test_alembic_stamp.py`, patron l.248-270) ;
- une sauvegarde d'avant P-132 restaurée par `/api/data/restore/{nom}` se lit avec les nouvelles valeurs ;
- l'API refuse `piste` en 400 et accepte les six étapes ; elle refuse `contact` et `active` pour une prestation ;
- l'état courant garde Découverte, Proposition, Signature et Livraison, écarte Perdu et Archive (réécriture de `tests/test_prestation.py:102-123`) ;
- l'export complet annonce 1.5 et porte les nouvelles valeurs.

Tests existants à réécrire dans le même commit, puisque leurs valeurs changent : `tests/test_prestation.py`, `tests/test_financement.py`, `tests/test_seance_et_echeances.py`, `tests/test_routers_data.py` (l.38, 143, 152).

Critère observable : sur une copie de la base de Ludo, `SELECT phase, count(*) FROM prestations GROUP BY phase` ne rend plus que des étapes du pipeline, avec les mêmes effectifs qu'avant, redistribués selon la table du §3.

### Lot 4 : les prestations parlent le pipeline (écran)

Tests à écrire d'abord (vitest) :
- le sélecteur d'une prestation propose exactement Découverte, Proposition, Signature, Livraison, Perdu, Archive, avec les libellés de `PIPELINE_ETAPES` (une seule source importée, aucun libellé recopié) ;
- il s'appelle « Étape de FORGER » pour un lecteur d'écran ; le champ de création affiche « Étape », se nomme « Étape de la nouvelle prestation » dans un groupe « Nouvelle prestation » (amendé le 26/09, constat 5 de la revue du diff : dans la fiche, « Étape » nomme déjà le contrôle de l'étape du contact) et présélectionne Découverte ;
- une valeur inconnue s'affiche « Étape inconnue : … » et n'est pas remplacée ;
- réécriture de `ListeDesPrestations.test.tsx` (l.39 et l.51-53).

Critère observable : la fiche d'Élodie ne montre plus qu'un seul jeu de mots, celui des colonnes du Pipeline.

### Lot 5 : recette

Rejouer le parcours 2 de Nathalie (`nathalie.md:45-62`) dans l'application lancée, sur les données de démonstration puis sur une copie de base réelle : fiche, étape, prestation, Perdu, Accueil, export et réimport du tableur. Le lexique (`docs/rules/RULES-DESIGN.md`, section 13, l.357-392) reçoit une ligne : « Étapes : Contact, Découverte, Proposition, Signature, Livraison, Actif, Perdu, Archive ; une prestation n'en prend que six ; Signature = accord donné ou en cours de formalisation, livraison pas commencée ».

## 8. Risques

- **Le mot « Archive » sur une prestation terminée** sonne plus froid que « Terminée ». Le sens est entier (§3) ; si la recette montre une gêne réelle, la voie propre reste de renommer le libellé partout, pas d'en créer un second.
- **Une huitième colonne** élargit le Kanban. La grille défile déjà ; sur un écran étroit, Perdu et Archive tombent hors champ, ce qui convient à deux colonnes terminales.
- **Chevauchement de migrations avec P-104**, qui ajoutera sa propre révision : celle qui arrive en second se chaîne sur la première, et chacune étend la preuve d'estampillage. `test_constante_epinglee_suit_la_vraie_tete` attrape l'oubli.
- **Deux champs, un seul vocabulaire** : quelqu'un finira par vouloir que la fiche suive ses prestations. Ce couplage automatique est refusé ici, pour la raison de `tests/test_prestation.py:29-43`. Le rappeler dans le docstring de `Prestation`.

## Annexe : appuis dans le code (relevés du 26/09)

- Domaine et libellés : `src/backend/app/models/schemas.py:237-250` ; `src/frontend/src/components/crm/pipelineEtapes.ts:7-36` ; `src/backend/app/services/crm_utils.py:22-51`, `304`, `379-383`.
- Prestations : `src/backend/app/models/entities.py:113-163` ; `src/backend/app/routers/prestations.py:28-129` ; `src/frontend/src/components/crm/ListeDesPrestations.tsx:35-143` ; `src/frontend/src/services/api/prestations.ts:10-29`.
- Lecteurs : `src/backend/app/services/memory_tools.py:986-993`, `1012-1014`, `1133-1152` ; `src/backend/app/routers/rgpd.py:137-149`, `195`, `214-220`, `657` ; `src/backend/app/routers/data.py:232`, `259-262`, `348`, `674`, `1916-1918`, `1986`.
- Score, Accueil, relances : `src/backend/app/services/scoring.py:33-41`, `74-76`, `89` ; `src/backend/app/routers/dashboard.py:539-541`, `641-646` ; `src/frontend/src/components/prototype/CetteSemaine.tsx:14`, `76-77`, `126-135` ; `src/backend/app/services/relances.py:25-49`.
- Tableur et synchro : `src/backend/app/services/crm_export.py:19`, `55`, `169-171` ; `src/backend/app/services/crm_import.py:25`, `686-691`, `776-783` ; `src/backend/app/services/crm_sync.py:49`, `119-120`, `201` ; `src/backend/app/routers/crm.py:508-554`, `576-620`, `628-652`.
- Écrans : `src/frontend/src/components/crm/PipelineView.tsx:4`, `39`, `66-73`, `163-172` ; `src/frontend/src/components/crm/CRMPanel.tsx:319-332`, `455` ; `src/frontend/src/lib/activitesCrm.ts:46-59` ; `src/frontend/src/components/ui/Etiquette.tsx:16`.
- Migrations : `src/backend/app/models/database.py:255-262`, `320-341`, `556-608`, `619`, `642-785`, `1113`, `1167`, `1173` ; `src/backend/alembic/versions/b8c9d0e1f2a3_date_d_envoi_des_pieces.py:10-20` ; `src/backend/alembic/env.py:136-155` ; `src/backend/app/routers/data.py:1442-1453`, `1587`, `1665`.
- Tests d'appui : `tests/test_prestation.py:29-43`, `102-123`, `182-202` ; `tests/test_alembic_stamp.py:98-153`, `248-270` ; `tests/test_p135_accueil_semaine.py:30-48` ; `tests/test_routers_data.py:152` ; `src/frontend/src/components/crm/CRMPanel.da.test.tsx:210`.

## Écarts assumés de l'implémentation (26/09)

Relevés à l'implémentation et par la revue adverse du diff ; le texte ci-dessus est amendé en conséquence.

1. **Ce que lit le modèle.** L'état courant d'une prestation donne `etape` et `definition_de_l_etape` au lieu de `phase` ; la fiche garde `stage` en identifiant, comme `list_contacts`, et ajoute les deux mêmes clés (§5.2).
2. **La synchro Sheets n'est pas à sens unique** : la création d'une fiche CRM écrit une ligne dans la feuille, avec le libellé de l'étape (§6).
3. **Import d'un ancien export.** Il n'existe pas d'import JSON des prestations : un export 1.4 se réimporte par ses contacts (`/api/data/import/contacts`), et une sauvegarde d'avant P-132 restaurée passe par l'étape ad hoc du démarrage. Les deux cas sont testés.
4. **Skill de proposition.** Le dictionnaire donné aux skills n'avait ni l'étape ni le score : les deux y sont, et la ligne « Score » perd son « /100 », l'échelle n'étant pas plafonnée.
5. **Commits.** Lots 1 et 2 dans un commit, lots 3 et 4 dans un autre, tests et code ensemble : un commit de gardes rouges seul aurait laissé `main` dans un état cassé. Le parcours Playwright du CRM compte huit colonnes dans le commit des lots 1 et 2.
6. **Lot 5.** La ligne du lexique est posée ; la recette dans l'application lancée reste à faire.
