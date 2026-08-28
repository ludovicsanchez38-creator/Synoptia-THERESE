# Campagne dix personas — THÉRÈSE 0.53.0-alpha

**28/08/2026.** Dix métiers, un agent par métier, chacun sur une instance neuve.
Puis une passe au navigateur, et une contre-expertise chargée de me réfuter.

---

## En un coup d'œil

| | |
|---|---|
| Personas joués | 10 |
| Findings bruts | **76** |
| Dont bloquants (avant requalification) | 23 |
| Verdicts « je rouvre demain » | **0 sur 10** (un conditionnel) |

Répartition annoncée par les personas :

| Nature | Nombre |
|---|---|
| Défaut de l'application | 31 |
| Friction d'usage | 32 |
| Limite du modèle local | 12 |

**Les dix verdicts vont dans le même sens.** Un médecin, un plombier, une
écrivaine, un avocat, une magistrate, un formateur, une dirigeante d'organisme
de formation, un responsable administratif, un boulanger et une directrice
d'association ne se sont pas concertés. Ils butent sur les mêmes murs.

Le seul verdict conditionnel est celui de l'association : « Je la rouvre demain
**seulement si** on m'écrit que c'est gratuit, et si on arrête de me dire
*client* et *Facturer*. »

---

## Le motif dominant : l'écran promet ce que l'application ne fait pas

Ce n'est pas le motif le plus fréquent. C'est celui qui fait fermer.

Sept endroits distincts où un texte affiché affirme quelque chose de faux :

| Ce que l'écran dit | Ce qui est vrai | Où |
|---|---|---|
| « **Aucune donnée n'est envoyée à un serveur externe** » (sauf modèle cloud) | `web_search` part chez DuckDuckGo, sans clé, sans confirmation, **même en modèle local** | `PrivacyTab.tsx:253` |
| « Les parcours raccordés […] demandent une **confirmation avant l'effet externe** » | `SENSITIVE_TOOL_NAMES` ne contient que `send_email` et `create_calendar_event` | `CapabilityCenter.tsx:586` |
| « **Parcours réel · confirmation avant effet** » (sous le composeur, en permanence) | idem | `ConversationCanvasPrototype.tsx:1851` |
| « Conversations IA — conservation illimitée — **Pas de données personnelles tierces** » | le titre de conversation reprend les 50 premiers caractères du message, nom de patient compris | `PrivacyTab.tsx:50` + `chat.py:1137` |
| « **la base SQLite n'est PAS chiffrée au repos** » (dit par l'assistante) | elle **est** chiffrée, SQLCipher AES-256 depuis US-014 | prompt système, `llm.py` |
| « Score de potentiel commercial **de 0 à 100** » | le calcul n'est borné qu'en bas ; 4 contacts sur 8 sont sortis au-dessus, dont trois à 145 | `PipelineView.tsx:274` + `scoring.py:88` |
| « **Connecté** » | c'est l'état du moteur local, pas du réseau ; `useOnlineStatus` existe et n'est branché nulle part | `ConnectionStatus.tsx` |

Trois personas testaient exactement ce point, parce que c'est leur métier qui
l'exige : l'avocat (secret professionnel), le médecin (secret médical), la
magistrate (déontologie). **Les trois ont trouvé l'écart, et les trois sont
partis.**

> « Si l'écran me dit que rien ne sort, et que ça sort, je ferme. »
> — Claire Dumontier, magistrate

### Le cas le plus embarrassant

L'assistante affirme que la base n'est pas chiffrée. J'ai d'abord classé cela en
hallucination du modèle local. **La contre-expertise a montré que le prompt
système le lui ordonne** :

> « IMPORTANT (honnêteté sécurité) : la base SQLite n'est PAS chiffrée au repos.
> Ne prétends JAMAIS qu'elle est « chiffrée », « AES-256 » ou équivalent : ce
> serait faux. »

Cette consigne était juste en 0.20.0, quand une revue a exigé qu'on cesse de
prétendre le chiffrement. Puis US-014 a livré SQLCipher. Le prompt ne l'a jamais
su — **et un test verrouille la consigne** (`TestSovereigntyHonesty`).

Les deux tests, exécutés ensemble :

```
[VERT] test_la_db_de_l_app_est_chiffree
[VERT] test_prompt_does_not_claim_encrypted_database
```

L'un garantit que la base est chiffrée. L'autre garantit que l'assistante dira
le contraire. La suite de tests protège une contradiction.

---

## Les quatre autres motifs transversaux

### 1. L'accueil parle à un commerçant — 8 personas sur 10

Le premier écran propose *Écrire, Retrouver, Préparer, **Facturer**, Décider*,
et pousse à « Brancher tes mails » et « Compléter le profil de facturation ».

- Le médecin : « je ne facture pas mes patients dans un logiciel d'entrepreneur ».
- L'écrivaine : « rien sur un manuscrit, une éditrice, une date de remise ».
- L'avocat : « si le premier écran me parle de devis, je n'y mets pas un licenciement ».
- L'association : « mes bénévoles ont un *score de potentiel commercial* ».
- Le boulanger : « aucun ne dit commande, aucun ne dit farine ».
- La magistrate, le formateur, le responsable administratif : même constat.

Ce n'est pas un problème de goût. C'est que **le premier écran décide si la
personne se reconnaît**, et huit sur dix ne se reconnaissent pas.

### 2. On range quelque chose, on ne le retrouve plus — 5 personas

Le médecin enregistre ses quatre associés en une phrase. La conversation
suivante : « aucun contact trouvé ». Le boulanger note une commande, elle
n'existe plus au comptoir le lendemain.

La cause est une **décision de conception assumée** : un contact créé depuis le
chat reçoit `scope="conversation"` et n'est visible que là. Le code le documente
explicitement (moindre privilège, cloisonnement 0.43).

Le défaut n'est donc pas le cloisonnement. C'est que **rien ne le dit** :
l'utilisateur croit remplir un carnet d'adresses, il remplit une conversation.
Et le code promet de pouvoir « promouvoir » un contact — ce contrôle n'existe
nulle part (`schemas.py:160`, aucun champ `scope` dans `ContactUpdate`).

### 3. La cloison arrête les documents, pas les fiches — 1 persona, confirmé

**Correction du 28/08, après relecture du chantier C.** Cette section affirmait
que deux personas subissaient la même fuite. **C'est faux, et je le corrige ici
plutôt que de le laisser dans un document d'arbitrage.**

**Ce qui est établi** — l'avocat, dans le dossier Rousset, s'est vu ressortir la
lettre de licenciement d'un autre client **et** le traitement anxiolytique de sa
cliente. Sa conversation était rattachée au projet Rousset. Le mécanisme est
vérifié : tout contact créé depuis l'écran est `scope="global"`
(`memory.py:401`), ses notes sont indexées avec lui, et la recherche du chat ne
passe pas `include_global` — le défaut `True` s'applique (`qdrant.py:240`).

**Ce qui ne l'est pas** — le formateur a obtenu une convocation « Atelier
Martin » portant un prérequis daté du 8-9 juillet, qu'il attribue à la Mairie de
Manosque. Trois faits s'y opposent :

1. il travaillait en **conversation libre**, non rattachée à un projet — le
   cloisonnement n'y joue aucun rôle, et un mode « cabinet » n'y changerait rien ;
2. ces dates n'apparaissent **nulle part ailleurs** dans son propre rapport, y
   compris là où il enregistre la facture Mairie ;
3. il qualifie lui-même la ligne de « **prérequis inventé** ».

L'hypothèse la plus économique est une hallucination du modèle local, à laquelle
il a attribué après coup une origine plausible. Le compter comme une fuite de
cloisonnement aurait fait porter au chantier C un défaut qu'il ne corrige pas.

**Le vrai second chemin est ailleurs, et il est pire** : `read_contact`
(`_cloison_contacts`) laisse passer les contacts globaux **par conception**.
Fermer la recherche vectorielle sans fermer l'outil SQL ne protège rien — le
modèle demanderait la fiche et obtiendrait le secret.

Le seul libellé qui parle de cloisonnement dit **« Documents consultés par cette
conversation »**. Les fichiers sont cloisonnés. Les fiches clients, non.

### 4. L'assistante annonce fait ce qui ne l'est pas — 4 personas

« La réunion **a été programmée** » (médecin), « Le courrier **a été envoyé** »
(avocat), « la note **a été ajoutée** au dossier » (avocat, responsable), «
l'agenda est **ajouté** » (formateur) — dans tous les cas, rien n'était fait.

**Le backend fait pourtant sa part.** Le résultat renvoyé au modèle dit :

> « Action préparée et en attente de validation de l'utilisateur.
> **NE PAS la considérer comme exécutée.** »

Le modèle local l'ignore. Ce que le produit peut corriger, ce n'est pas le
modèle : c'est **l'écran, qui affiche le texte du modèle et la carte de
confirmation au même niveau, sans arbitrer**. Le médecin l'a formulé
exactement : « si j'avais répondu *oui* dans le champ au lieu de cliquer
*Créer*, je serais partie en croyant que c'était posé ».

Sur un produit dont l'argument est de faire tourner de petits modèles locaux,
c'est un choix d'interface, pas une fatalité.

---

## Ce qui a été requalifié, et ce qui est faux

Une campagne de personas produit des rapports dramatiques par construction :
c'est leur rôle. Deux passes de vérification ont suivi.

**Soso (Codex), lancé pour me réfuter** : « Un seul finding tient tel quel. Le
reste mélange absolus faux, causes ratées et gravités gonflées. » Il avait
raison sur l'essentiel.

| Mon affirmation | Ce qui est vrai |
|---|---|
| « L'adresse client ne peut être saisie **nulle part** » | Faux : l'import VCF la renseigne (`memory.py:491`). Le défaut réel est une dérive entre sept couches, dont trois seulement honorent le champ |
| « Le prompt de scénario est **envoyé au modèle** » | Faux : c'est un sous-titre de palette (`ConversationCanvasPrototype.tsx:559`). Rien ne part |
| « Le chiffrement : hallucination du modèle » | Faux, et plus grave : le prompt l'ordonne, un test le verrouille |
| « Le logging est codé en dur pour une raison d'ordre d'initialisation » | Faux : `settings` est importé avant `setup_logging()` (`main.py:16`) |
| « Le devis marqué DRAFT est bloquant » | Surévalué : le statut suit l'état réel, et passe à `SENT`. **Mineur** |
| « Un nom de patient lisible depuis le couloir » | Non démontré : le tiroir doit être ouvert, et la conversation est renommable. **Majeur**, pas bloquant |

**Et la contre-expertise a trouvé ce que personne n'avait vu** :
`POST /invoices/{id}/send` répond **501 en toutes circonstances**
(`invoices.py:880`). L'artisan fait son devis et ne peut pas l'envoyer depuis
l'application.

### Un finding « bloquant » était un artefact de mon harnais

Le boulanger a classé en bloquant le fait que la dictée exige le cloud
(`stt_available: false`, « la voix locale n'est pas embarquée dans cette
version »).

**C'est ma campagne qui l'a induit en erreur.** Le backend de test tournait
depuis le venv de développement ; la voix locale n'est installée que par l'extra
`voice-local`, que le workflow de release active (`release.yml:98`). J'ai lancé
le **binaire réellement livré** avec un data-dir jetable :

```json
{"enabled": false, "stt_available": true, "tts_available": true}
```

La dictée locale **est** dans la 0.53.0. Ce que le boulanger a lu ne s'affiche
pas chez un vrai utilisateur. Ce qui reste : elle est **éteinte par défaut** et
les modèles se téléchargent au premier usage (145 Mo) — un défaut de premier
usage, mineur.

> **Leçon de méthode** : un harnais qui n'est pas le paquet livré fabrique de
> faux findings. Pour toute campagne future : lancer le binaire packagé, ou
> synchroniser le venv avec `--extra voice-local`.

---

## La passe navigateur : ce qu'un agent sans écran ne peut pas voir

Quatre constats, dont deux validations.

**U1 — Le focus clavier se pose sur un bouton « Supprimer » invisible.**
Les actions de ligne de l'écran *Devis et factures* vivent dans un conteneur
`opacity-0 group-hover:opacity-100`. Les boutons restent dans le flux de
tabulation. Mesuré :

```json
{"focusEstSurLeBouton": true, "labelFocalise": "Supprimer",
 "focusVisible": true, "opaciteDuConteneur": "0"}
```

Il manque `group-focus-within:opacity-100`. **Nuance qui évite d'en faire un
bloquant** : le clic ouvre une modale de confirmation visible
(`InvoicesPanel.tsx:361`). C'est un manquement de visibilité du focus
(WCAG 2.4.7), pas une perte de données.

**U3 — « Écrire » affiche trois libellés qui parlent de lecture.** L'analyse de
code n'en avait relevé qu'un. À l'écran : le sous-titre de l'accueil (« Je
**consulte** la boîte connectée »), la carte du parcours (« **Messages à
consulter** ») et le titre du canevas (« **Lecture** et brouillon »). La densité
d'un défaut de nommage ne se lit pas dans un fichier.

**U4 — En fenêtre réduite, l'établi ne se dégage jamais du composeur.** À
900 × 700, après défilement maximal, les cinq verbes finissent 4 px sous le
composeur. Mineur.

**U2 — Les deux correctifs livrés ce matin tiennent en navigateur réel.** Le
plan réclamait « un gate clavier en navigateur réel à 1279 et 1280 px » ; il
n'existait pas. Mesuré : à 1280, canevas et chat coexistent, chat vivant ; à
1279, le canevas cède la place, le chat reste saisissable. **Le mock des tests
ne pouvait pas le vérifier** — ses auditeurs `matchMedia` sont des `vi.fn()`,
personne ne reçoit jamais `change`.

---

## Ce que la campagne n'a toujours pas vu

Un agent ne clique pas ; la passe navigateur a couvert une partie seulement.
Restent hors de portée :

- l'ordre de tabulation complet et les annonces des lecteurs d'écran ;
- les dialogues natifs Tauri, l'ouverture des PDF, les permissions de fichiers,
  le sidecar dans l'application packagée ;
- le rendu visuel réel des PDF (polices, césures, pagination) ;
- les courses entre l'état React, `localStorage` et le backend après une
  navigation, une fermeture ou un flux interrompu.

---

# Le plan

Six chantiers. Les chiffrages sont en jours de travail effectif, TDD et gates
compris, et supposent le rituel habituel (test rouge d'abord, preuve par
sabotage, relecture adversariale avant release).

## A — La vérité d'abord · **1 jour**

Les sept endroits où l'écran ou le prompt affirment le faux. C'est le chantier
qui a fait fermer trois personas sur une ligne rouge professionnelle, et c'est
le moins cher du plan.

| Tâche | Nature | Effort |
|---|---|---|
| Réécrire `SOVEREIGNTY_BLOCK` : la base **est** chiffrée (SQLCipher), rester honnête sur ce qui ne l'est pas (Qdrant en clair, conversations dans `localStorage`) | 1 chaîne | 1 h |
| **Retourner** `TestSovereigntyHonesty` : qu'il exige la vérité au lieu de l'ancienne consigne | 1 test | 30 min |
| `web_search` + `browser_navigate` soumis à confirmation — de préférence en branchant le gate sur `MUTATION_EXTERNE` plutôt que sur une liste tenue à la main | 1 ligne + 1 test de complétude | 3 h |
| Corriger `PrivacyTab.tsx:253` : la phrase est fausse aujourd'hui, quelle que soit la suite | 1 phrase | 30 min |
| Corriger `PrivacyTab.tsx:50` : « Pas de données personnelles tierces » est indéfendable | 1 phrase | 15 min |
| Borner le score à 100, ou corriger le libellé | 1 ligne | 30 min |
| Rejouer le token sur 401 (`core.ts`), + recharger sur `sidecar-status: running` | 1 retry + 1 test | 3 h |

**Le test qui manque et qui tient tout** : un test de complétude qui échoue si un
outil classé `MUTATION_EXTERNE` n'est couvert par aucun gate de confirmation.
Les deux tables ont divergé en silence.

## B — Les ruptures d'usage · **3 à 4 jours**

Ce qui empêche de finir un travail commencé.

| Tâche | Pourquoi | Effort |
|---|---|---|
| L'envoi de devis/facture répond 501 : soit on l'implémente, soit l'écran cesse de le proposer | l'artisan fait son devis et ne peut pas l'envoyer | 1 j (ou 2 h pour retirer le bouton) |
| `address` honorée par `POST /memory/contacts`, l'outil `create_contact` et le formulaire | 7 couches déclarent le champ, 3 l'honorent. Une adresse est obligatoire sur un devis | 0,5 j |
| Un outil de lecture financière (statut, échéance, encours) + `search_invoices` à `query` optionnelle | « combien me reste-t-il à encaisser ? » n'a aucun chemin | 1 j |
| Le nom du client sur les lignes de `InvoicesPanel` | « je retiens Moreau, pas DEV-2026-001 » | 0,5 j |
| Notifications **avant** l'échéance, pas seulement après | « me prévenir hier, c'est me prévenir trop tard » (avocat) | 0,5 j |
| Accents et statuts français dans le PDF (`invoice_pdf.py`) | un document client français marqué *Date d' emission* | 0,5 j |

## C — Le cloisonnement pour les professions au secret · **2 à 3 jours**

Le plus structurant des chantiers courts, et le seul qui ouvre un marché
(avocats, médecins, notaires, experts-comptables).

1. **Renommer le sélecteur.** « Documents consultés par cette conversation » ne
   dit pas ce qu'il fait. *(2 h)*
2. **Choix du périmètre à la création d'un contact**, avec un défaut explicite,
   et le contrôle de « promotion » que le code promet déjà. *(1 j)*
3. **Un mode « cabinet »** où `include_global=False` : aucune fuite entre
   dossiers, au prix de ressaisir les contacts communs. Pour un avocat, c'est un
   prix qu'il paiera. *(1 j)*
4. **Le test qui manque** : écrire un secret dans les notes d'un contact global,
   interroger une conversation rattachée à un autre projet, échouer si le secret
   remonte. *(2 h)*

## D — L'accueil qui parle au métier · **5 à 8 jours**

Huit personas sur dix ne se reconnaissent pas dans le premier écran. C'est le
chantier le plus lourd et le plus incertain — il touche au cap produit, pas
seulement au code.

La question à trancher **avant** de coder : THÉRÈSE est-elle un outil
d'entrepreneur (et alors le médecin, l'écrivaine, la magistrate et l'association
ne sont pas la cible), ou un assistant de travail générique dont la facturation
est un module parmi d'autres ?

Tant que cette question n'est pas tranchée, tout travail sur l'accueil sera
refait.

## E — Nommage et accessibilité · **2 jours**

| Tâche | Effort |
|---|---|
| `group-focus-within:opacity-100` sur les actions de ligne (U1) | 1 h |
| Les trois libellés de « Écrire » nomment une rédaction (U3) | 3 h |
| Étendre `lexiqueTitres.test.ts` à `scenarioLabels`, `scenarioPrompts` et les sous-titres de carte | 0,5 j |
| Un bouton *Annuler* là où le responsable administratif le cherche | 0,5 j |
| Purge du jargon aux 19 endroits relevés par l'artisan (*canevas*, *profil émetteur*, *référentiel contacts*…) | 0,5 j |

## F — Les fondations · **chantier de fond, à étaler**

La contre-expertise l'a formulé mieux que moi :

> « Une capacité est redéclarée à la main dans les schémas Pydantic, mappings de
> route, types TypeScript, formulaires, outils LLM, prompts, libellés et tests.
> Ces copies divergent. »

Trois symptômes de la même cause, tous rencontrés dans cette campagne : le champ
`address` déclaré sept fois et honoré trois ; le chiffrement livré dans le code
et jamais propagé au prompt ; la classification des outils tenue en double dont
une moitié seule est branchée.

Même motif appliqué aux chemins : `settings.data_dir` existe, et chaque service
invente encore son fallback. **Démontré en conditions réelles pendant cette
campagne** : trois PDF de personas ont été écrits dans l'installation réelle
(`~/.therese/invoices/`) alors que tout le reste était isolé — plus les journaux
en continu, avec les arguments complets des outils.

Ce chantier ne se planifie pas en jours : il se traite en posant, à chaque
correctif des chantiers A à E, **un test de cohérence entre couches** plutôt
qu'un correctif local.

---

## Recommandation

**A puis C.** Un jour pour cesser d'affirmer le faux, deux à trois pour rendre
la cloison utilisable par une profession au secret. C'est peu de code, et c'est
ce qui sépare « une alpha qui promet trop » de « une alpha honnête sur laquelle
un professionnel peut se prononcer ».

B ensuite, parce qu'un outil qui ne laisse pas finir un devis ne se rattrape pas
par de l'honnêteté.

D **après avoir tranché la question de cap** — pas avant.

---

## Où sont les pièces

- Rapports bruts des dix personas, protocole, fiches personas, journaux :
  scratchpad de la session, `campagne-personas/`
- Constats d'orchestration (O1 à O7) et vérifications ligne à ligne :
  `campagne-personas/constats-orchestrateur/`
- Passe navigateur (U1 à U4) : `campagne-personas/passe-ui/constats/`
- Méthode et garde-fous du harnais : `campagne-personas/SYNTHESE-methode.md`
