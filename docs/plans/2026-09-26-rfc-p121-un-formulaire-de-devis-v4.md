# RFC P-121 (V4) : un seul formulaire de devis, pour la création et la modification

Rédigé le 26/09/2026. **Base relue : `main` à `7baf1793`.** Toutes les lignes citées ont été lues à ce commit ; `main` a bougé pendant la rédaction (B-1522 à B-1535, P-132 lots 1 à 4), et chaque citation a été recalée puis vérifiée mécaniquement (existence de chaque ligne, première ligne relue). Depuis `a3c98b74`, base de la V3, ont bougé, parmi les fichiers cités : `components/invoices/InvoiceForm.tsx` (B-1518 : trois lignes de plus au-delà de `components/invoices/InvoiceForm.tsx:337`), `routers/invoices.py` (B-1506 : 30 lignes, de huit à trente de décalage au-delà de `routers/invoices.py:563`), `models/schemas.py` (P-132 : quatre lignes de plus avant les requêtes de pièces), `models/entities.py` et `models/database.py` (P-132, lignes citées inchangées ou recalées). La coque, le tiroir, le registre des saisies, les hôtes du devis et `services/invoice_pdf.py` n'ont pas bougé.

Remplace la V3 du même jour (`docs/plans/2026-09-26-rfc-p121-un-formulaire-de-devis-v3.md`), refusée par la revue adverse du 26/09 (constats 1 à 7, dont deux P2, verdict NO-GO). Proposition acceptée par Ludo le 25/09 sous une contrainte : **aucune perte de fonctionnalité**. Les décisions 26 à 29 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:93-102`) sont des faits. **Cette V4 est la dernière version avant implémentation** : pas de nouvelle revue de document ; chaque lot a sa revue de conception au moment du code, puis la revue adverse de son diff.

La garde de navigation que ce chantier réécrit est commune avec P-125 et P-109 : sa signature et l'ordre de ses clauses sont fixés dans **P-125 V4, § 6** (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v4.md`). Cette RFC la cite et ne la redéfinit pas.

Chemins relatifs à `src/frontend/src/` (écran) et `src/backend/app/` (moteur), sauf mention.

## 0. Les constats de la revue et leur traitement

| Nº | Constat | Verdict, relu à `7baf1793` | Traitement | Où | Fermé au code, ou traité en design |
|---|---|---|---|---|---|
| 1 (P2) | Le repli du chat au rétrécissement n'a pas de réalisation correcte | **Accepté.** Replier par `fermerLeChat` fait `goBack` (`components/prototype/ConversationCanvasPrototype.tsx:1522-1524`), le store tombe à `null` (`stores/navigationStore.ts:106-112`) et l'effet de navigation referme le panneau (`components/prototype/ConversationCanvasPrototype.tsx:1305-1315`) ; replier par `setChatOpen(false)` laisse le store sur `chat`, le défaut de Finding 7 (`components/prototype/ConversationCanvasPrototype.tsx:1517-1521`) | **Le chat ne se replie plus.** Le panneau se replie comme aujourd'hui (`components/prototype/ConversationCanvasPrototype.tsx:1587-1589`, inchangé) et la saisie du devis est mise à l'abri au démontage, puis rendue à la réouverture de Facturer (V4-1) | § 6.4, lots 4 et 5 | design ; tests `InvoiceConversationCard.miseALAbri` (lot 4) et ligne « rétrécissement » de la table (lot 5) |
| 2 (P2) | Replier le chat démonte le composeur : pièces jointes perdues, réponse invisible et inarrêtable | **Accepté** (`components/chat/ChatInput.tsx:126`, `components/chat/ChatInput.tsx:284-290`, `components/chat/ChatInput.tsx:1117`, `lib/arretDeLaReponse.ts:30-32`, `components/prototype/ConversationCanvasPrototype.tsx:2054-2055`) | Sans objet dès que le chat ne se replie plus (V4-1). Aucune dépendance au lot 2 de P-125 : chaque lot se livre seul | § 6.4 | design ; tests « rétrécir pendant une réponse » et « rétrécir avec une pièce jointe » au lot 4 |
| 3 | `changerLePanneau` sans passage par la garde commune ni clause vocale | **Accepté** | `changerLePanneau(surfaces, effet)` s'écrit `if (sortieRefusee({ surfaces })) return; effet();`, par la garde commune (P-125 V4, § 6), clause vocale comprise | § 6.4, lot 5 | design ; test « session vocale active » au lot 5 |
| 4 | La garde de source vise 76 écritures, dont une quarantaine sans rapport avec le devis | **Accepté.** 76 lignes à `7baf1793` (écritures des huit états dans la coque) | La garde raisonne par **site** (fonction englobante), avec une table de sites et un verdict par site ; les gestionnaires en ligne du JSX qui écrivent ces états deviennent des fonctions nommées (V4-2) | § 6.4, lot 5 | design ; garde `sortiesDuDevis.sites.test.ts` au lot 5 |
| 5 | Le test de concurrence ne peut pas passer dans l'ordre légitime | **Accepté.** L'écriture conditionnelle précède la lecture (`routers/invoices.py:541`) et tient le verrou d'écriture jusqu'au commit : l'ordre 1 puis 2 est un succès normal | Deux ordres forcés par une barrière, attendus écrits comme la revue le propose | lot 1 | design ; tests `test_concurrence_*` au lot 1 |
| 6 | La modale n'est pas inscrite au registre ; c'est un comportement neuf | **Accepté, et c'est un défaut existant** (R-121-4) : la modale utilise `useQuestionDAbandonDeModale` (`components/invoices/InvoiceForm.tsx:221`), qui ne s'inscrit pas ; seul `useAbandonDeSaisie` le fait (`hooks/useAbandonDeSaisie.ts:77-80`). **Réfuté en partie** : le scénario proposé, « ⌘N puis rail », n'atteint pas la modale. Les raccourcis sont absorbés tant qu'un dialogue `aria-modal` est ouvert (B-638, `hooks/useKeyboardShortcuts.ts:63`), et le rail est sous le voile de la modale (`components/invoices/InvoiceForm.tsx:610-619`, couche `MODAL_NESTED`). Ce qui l'atteint, c'est une navigation posée dans le store, par exemple « Voir » sur la notification d'une Action finie (`stores/actionsStore.ts:94`), notification dont la couche passe au-dessus (`styles/z-layers.ts:25`, `components/ui/Notifications.tsx:52`) | L'inscription devient une option de `useQuestionDAbandonDeModale` (`surfaceDuRegistre`), posée par `InvoiceForm` seul ; `ContactModal` et `ProjectModal`, surfaces de la coque qu'aucune sortie ne démonte, ne s'inscrivent pas (V4-3) | § 6.4, lot 5 | design ; test `InvoiceForm.registreDesSaisies` au lot 5 |
| 7 | `main` a bougé : B-1518 ferme R-121-1, B-1506 refuse le retour d'une facture émise au brouillon ; citations décalées ; deux tests « rouges d'abord » sont verts à HEAD | **Accepté.** `components/invoices/InvoiceForm.tsx:340` (`tva_applicable`), test `components/invoices/InvoiceForm.sansTva.b1518.test.tsx` ; `routers/invoices.py:566-573` (409), `routers/invoices.py:701-711` (`_facture_emise`) ; `lib/saisieEnCours.ts:26-31` | R-121-1 retiré (fermé) ; `requeteDePiece` et les statuts proposés suivent B-1506 (V4-4) ; citations recalées ; les tests verts par construction deviennent « non-régression » avec sabotage | § 3, § 6.2, lots 2 et 5 | B-1518 **fermé au code** (`369e068b`) ; B-1506 **fermé au code** (`62639261`) ; le reste en design |

Un constat est réfuté en partie (le 6, sur le scénario, preuve à l'appui) ; son traitement tient, pour le chemin qui existe vraiment.

## 1. Ce que la V4 garde de la V3

- Le constat de départ (Claire, claire-31) et la recommandation : un corps de saisie commun, deux hôtes qui gardent leur cycle de vie.
- L'inventaire ligne par ligne des deux formulaires (V2 § 3.3), relu : il reste juste, aux recalages près.
- Les décisions V1-Q1, V1-Q2, V1-Q4, Q-quantité et Q-serveur, V3-1 (`noValidate`, `validerPiece` seul juge), V3-2 (la mention de l'écran est celle du PDF), V3-3 (avertissement de régime non bloquant), V3-4 (le registre connaît des surfaces).
- La précondition `statut_attendu` par écriture conditionnelle, le régime de TVA exposé par `/billing/profile-status`, la table de mentions partagée entre `pytest` et `vitest`.
- Le module pur, `useSaisieDePiece`, `LignesDePiece`, `CorpsDePiece`, les identifiants par hôte, l'absence de second `<form>` (B-011).
- La table des sorties, relevée à partir de ce que l'arbre de rendu démonte, et une seule fonction gardée par laquelle elles passent.

## 2. Ce que la V4 retire ou reporte, et pourquoi

- **Retiré : « le rétrécissement replie le chat au lieu du panneau »** (V3 § 6.4, dernière ligne de la table). Aucune réalisation n'était juste (constat 1), et démonter le composeur perdait ses pièces jointes et l'arrêt de la réponse (constat 2). Remplacé par la mise à l'abri de la saisie (V4-1).
- **Retiré : la garde de source « aucune des huit écritures hors de `changerLePanneau` »** (V3 § 6.4). Elle était rouge dès sa création (constat 4). Remplacée par la garde par sites (V4-2).
- **Retiré : « la modale s'inscrit avec `vue` », présenté comme l'existant** (V3 § 6.4). C'était un comportement neuf (constat 6), et une inscription par défaut dans `useQuestionDAbandonDeModale` aurait fait poser la question à `ContactModal` et `ProjectModal` par des gestes qui ne les démontent pas. Remplacé par l'option (V4-3).
- **Retiré : R-121-1** (V3 § 9). B-1518 l'a fermé.
- **Retiré : « l'immutabilité d'une facture émise » comme hors périmètre en entier** (V3 § 6.7). B-1506 refuse désormais sa suppression et son retour au brouillon ; seul reste hors périmètre le verrouillage de ses lignes et de ses montants.
- **Retiré : le test de concurrence « quel que soit l'ordre »** (V3 lot 1) (constat 5).
- **Retiré : « le second des deux lots 5 se rebase sur le premier »** (V3 § 6.4). Remplacé par la garde commune (P-125 V4, § 6).
- **Reporté, inchangé : fermer le chat referme aussi le panneau ouvert à côté** (R-121-2). Tant qu'il existe, fermer le chat pose la question.

## 3. Prérequis et correctifs arrivés sur `main`

- **B-1492** (`b39ac7d8`) : remettre un devis en Brouillon part au moteur (`components/invoices/InvoiceForm.tsx:444`). Test `components/invoices/InvoiceForm.retourBrouillon.b1492.test.tsx`.
- **B-1493** (`feac6303`) : la borne de validité ne vaut que pour une validité saisie (`components/invoices/InvoiceForm.tsx:377-385`). Test `components/invoices/InvoiceForm.validiteHorsBornes.b1493.test.tsx`.
- **B-1518** (`369e068b`) : la modale suit `tva_applicable` dans ses totaux (`components/invoices/InvoiceForm.tsx:340`). Ferme R-121-1. Test `components/invoices/InvoiceForm.sansTva.b1518.test.tsx`, non-régression au lot 2.
- **B-1506** (`62639261`) : une facture ou un avoir émis ne se supprime plus et ne repasse plus en brouillon, 409 « émets un avoir » (`routers/invoices.py:566-573`, `routers/invoices.py:676`, `routers/invoices.py:701-711`) ; un devis n'est pas concerné. Test `tests/test_b1506_facture_emise_intouchable.py`.

Rien n'empêche le lot 0 de commencer.

## 4. Le besoin

Claire crée son devis dans le panneau « Facturer » et le modifie dans la modale de « Devis et factures » : même objet, deux codes, deux jeux de règles. Chaque correctif de devis a dû être posé deux fois, ou ne l'a été que d'un côté. Tant qu'il y a deux formulaires, un correctif sur deux manque à l'un d'eux.

## 5. Décisions

| Nº | Décision | Origine | Ce qu'elle impose ici |
|---|---|---|---|
| 26 à 29 | Arrondi commercial ; règles strictes à la création ou au changement du champ ; taux 0 selon le régime ; devis envoyé non retouchable depuis Facturer | Ludo par délégation, 25/09 | Inchangé depuis la V3 |
| V3-1 à V3-4 | `noValidate` et `validerPiece` seul juge ; mention de l'écran égale à celle du PDF ; avertissement de régime ; registre à surfaces | Tranchées en V3 | Inchangées |
| V4-1 | Au rétrécissement, le panneau se replie comme aujourd'hui et le chat n'est jamais touché ; un devis modifié qui se démonte sans réponse « Abandonner » est mis à l'abri, et rendu à la prochaine ouverture de Facturer | Tranché ici | Motif : constats 1 et 2 ; ce qui n'est pas un geste ne peut pas poser de question, et ne doit rien perdre. La mise à l'abri couvre aussi toute sortie qu'une garde aurait manquée |
| V4-2 | La garde de source raisonne par site d'écriture, avec une table de sites et un verdict par site | Tranché ici | Motif : constat 4 ; 76 écritures, dont la plupart ne touchent jamais le devis |
| V4-3 | La modale ne s'inscrit au registre que par une option de `useQuestionDAbandonDeModale`, posée par `InvoiceForm` seul | Tranché ici | Motif : constat 6 ; seules les modales hébergées dans une vue sont démontées par une sortie |
| V4-4 | `requeteDePiece` n'envoie jamais `draft` pour une facture ou un avoir émis, et la liste des statuts n'y propose pas « Brouillon » | Tranché ici | Motif : B-1506 ; l'écran ne propose pas un geste que le moteur refuse (R-121-3) |
| V4-5 | La garde de navigation est commune (P-125 V4, § 6) | Tranché avec P-125 | Motif : constat 3 |

## 6. Conception

### 6.1 Moteur (lot 1)

**Précondition de statut (décision 29).** `UpdateInvoiceRequest` (`models/schemas.py:1332-1344`) gagne `statut_attendu: str | None = None` ; quand il est fourni, `update_invoice` (`routers/invoices.py:531`) commence par `UPDATE invoices SET updated_at = :maintenant WHERE id = :id AND status = :statut_attendu`, avant la lecture de la pièce (`routers/invoices.py:541`). Aucune ligne touchée : relecture, 404 si la pièce n'existe plus, 409 sinon : « Ce devis n'est plus un brouillon (statut : Envoyé). Il ne se retouche plus ici. » Sans le champ, rien ne change. La garde de B-1506 (`routers/invoices.py:566-573`) reste où elle est, après la lecture : elle ne concerne que les factures et les avoirs. Aucun parcours de l'écran n'atteint ce 409 aujourd'hui (V3 § 6.1) : la précondition est une garde du moteur, prouvée par des tests.

**Régime de TVA exposé (décision 28).** `/billing/profile-status` (`routers/invoices.py:849-876`), qui porte déjà `tva_intra_renseigne` (P-136), renvoie aussi `regime_tva` ; sans profil, `normal`.

**Une seule règle de mention.** Le calcul de `_build_conditions_block` (`services/invoice_pdf.py:672-689`) sort dans une fonction pure `mention_de_tva(lignes, tva_applicable, regime_tva) -> str`, appelée par le bloc sans changement de comportement. Ses cas vivent dans `components/invoices/mentionsDeTva.cas.json`, lue par `pytest` et par `vitest` : les trois régimes × {toutes les lignes à 0 %, lignes mixtes, toutes taxées}, `tva_applicable` faux sous chaque régime, aucune ligne.

Aucune colonne ne change ; la tête Alembic est celle de `main` à la base (`c9d0e1f2a3b4`, arrivée avec P-132), et ce chantier n'en ajoute pas.

### 6.2 Le module pur `components/invoices/saisieDePiece.ts` (lot 2)

Repris de la V3 (§ 6.2), avec la règle de B-1506 :

- `totauxDePiece(lignes, tvaApplicable)` : si `tvaApplicable` est faux, TTC = HT, comme `_montants_de_ligne` (`routers/invoices.py:194-217`) et comme la modale depuis B-1518. L'hôte passe la valeur de la pièce chargée, vrai à la création.
- `mentionDeTva({ lignes, tvaApplicable, regime })` et `avertissementDeRegime({ lignes, regime })` : inchangés.
- `validerPiece(saisie, reference)` : seul juge (V3-1) ; la garde de B-1493 (`components/invoices/InvoiceForm.tsx:377-385`) y devient une règle, et son test reste vert.
- `statutsProposes(documentType, reference)` : les listes de la modale (`components/invoices/InvoiceForm.tsx:72-88`), sans « Brouillon » pour une facture ou un avoir émis, selon la règle de `_facture_emise` (`routers/invoices.py:701-711`) : type facture ou avoir, et `sent_at` posé ou statut autre que `draft` (`services/api/invoices.ts:45`).
- `requeteDePiece(saisie, reference)` : en modification, le statut part dès qu'il diffère de `reference.status` (règle de B-1492, `components/invoices/InvoiceForm.tsx:444`), sauf `draft` pour une pièce émise, qui n'est jamais envoyé (V4-4). `tva_applicable` n'est jamais envoyé.

### 6.3 Les composants et la présentation (lots 3 et 4)

Inchangés depuis la V3 : `LignesDePiece`, `CorpsDePiece`, `useSaisieDePiece` ; le `<form>` que la modale garde porte `noValidate`, le bouton restant rattaché par `form=` (B-011, `components/invoices/InvoiceForm.tsx:649`, `components/invoices/InvoiceForm.tsx:1035`) ; le panneau affiche la mention et l'avertissement de régime au même endroit que la modale.

**Mise à l'abri (V4-1), lot 4.** Un petit store, `components/invoices/saisieAbritee.ts`, garde une place : la saisie du devis du panneau Facturer. Au démontage de `DevisDraftForm` (`components/prototype/InvoiceConversationCard.tsx:310`), si `useSaisieDePiece` dit la saisie modifiée et qu'elle n'a été ni abandonnée par la question, ni enregistrée, elle est écrite dans cette place. Au montage suivant avec `new-devis` (`components/prototype/InvoiceConversationCard.tsx:726-727`), la saisie initiale vient de la place, qui se vide, et une ligne d'état dit « Devis repris là où tu l'avais laissé ». La place vit en mémoire : un rechargement la perd, comme toute saisie non enregistrée aujourd'hui. Le double montage de StrictMode écrit puis reprend la même saisie, sans effet.

### 6.4 Le registre à surfaces et les sorties (lot 5)

**Le registre.** `lib/saisieEnCours.ts` change de forme de garde (V3-4) :

```ts
type Surface = 'vue' | 'panneau';
interface Garde { surface: Surface; modifiee: () => boolean; demander: () => void }
inscrireSaisieEnCours(garde: Garde): () => void
sortieRetenueParUneSaisie(surfaces: readonly Surface[] = ['vue']): boolean // pose la question de la plus récente modifiée parmi ces surfaces
uneSaisieEstModifiee(surfaces: readonly Surface[]): boolean               // lecture sans effet
```

La valeur par défaut `['vue']` garde à l'identique les appelants actuels (`components/tasks/TasksPanel.tsx:194`, `components/calendar/CalendarPanel.tsx:295`, `components/calendar/CalendarPanel.tsx:372`, `lib/actionRegistry.ts:117`, `components/prototype/ConversationCanvasPrototype.tsx:1293`, `components/prototype/ConversationCanvasPrototype.tsx:1502`, `components/prototype/PrototypeConversationDrawer.tsx:268`). Qui s'inscrit, et avec quoi :

- `useAbandonDeSaisie` (`hooks/useAbandonDeSaisie.ts:77-80`), donc `TaskForm` et `EventForm` : `{ surface: 'vue', modifiee, demander }` ;
- **la modale de Devis et factures, par option (V4-3)** : `useQuestionDAbandonDeModale` (`hooks/useQuestionDAbandonDeModale.ts:18-76`) gagne `surfaceDuRegistre?: Surface`, posée par `InvoiceForm` seul (`components/invoices/InvoiceForm.tsx:221`) ; elle est montée dans la vue `invoices` (`components/invoices/InvoicesPanel.tsx:617`, `components/prototype/PrototypeUnifiedViewCanvas.tsx:94`), que les sorties de vue démontent. `ContactModal` et `ProjectModal` ne la posent pas : ce sont des surfaces de la coque, qu'aucune sortie ne démonte ;
- le formulaire du panneau : `{ surface: 'panneau' }`, drapeau « modifiée » venu de `useSaisieDePiece` (et non de `hasUnsavedChanges`, `components/prototype/InvoiceConversationCard.tsx:345`, qui n'est posé qu'après un premier enregistrement).

**Quand le devis est-il démonté ?** `DevisDraftForm` est rendu si aucun des cinq panneaux d'outils n'est ouvert (ils passent avant dans le ternaire, `components/prototype/ConversationCanvasPrototype.tsx:2470-2508`), que `canvasOpen` est vrai, que `scenario` vaut `invoice`, que `selectedInvoiceId` vaut `new-devis`, **et que la ressource de facturation est prête** (`components/prototype/InvoiceConversationCard.tsx:722-727` : un état « chargement » ou « erreur » le remplace). Cette neuvième condition, absente de la V3, n'est atteinte que par un nouveau chargement (`components/prototype/usePrototypeInvoiceData.ts:36-38`), lancé à l'entrée du parcours (`components/prototype/usePrototypeInvoiceData.ts:157-164`) ou par « Réessayer » d'un état d'erreur ; jamais pendant la saisie aujourd'hui, et la mise à l'abri la couvre de toute façon.

**Les sorties** (lignes de `components/prototype/ConversationCanvasPrototype.tsx`) :

| Sortie | Écriture qui démonte | Garde à `7baf1793` | Comportement voulu |
|---|---|---|---|
| Croix du panneau | `collapseScenarioPanel`, `:1534-1537` | aucune | question (`['panneau']`) |
| Ouvrir le chat, « Nouvelle conversation », « Vider », sous 1280 px | `openChat`, `:1207` | registre sans surface (`:1082`) | question (`['vue', 'panneau']`) |
| Les mêmes à 1280 px et plus | aucune | registre sans surface | aucune question (`['vue']`) ; **non-régression**, vert à HEAD par construction |
| Fermer le chat (croix `:2066`, Échap `:1615`) | `fermerLeChat` puis l'effet de navigation (`:1305-1315`) | registre sans surface | question tant que R-121-2 n'est pas tranché |
| Ouvrir une vue (rail, palette, Accueil `:1866`) | `openEmbeddedView`, `:1234`, et `rangerPourLAccueil`, `:1636-1650` | registre sans surface | une question, `['vue', 'panneau']` (B-994) |
| Choisir un parcours ou une capacité | `chooseScenario` `:1652-1676`, `chooseCapability` `:1678-1720` | registre sans surface (`:1653`, `:1679`) | question |
| Une ligne de « Travaux » | `:1410-1429` | registre sans surface (`:1413`) | question |
| Ouvrir une séance depuis l'Agenda | `:1731-1742` | registre sans surface (`:1732`) | question |
| Cliquer une pièce dans la carte Facturer | `onOpenInvoice`, `:2223-2227` | **aucune** | question (`['panneau']`) |
| Pastille « Board » ou « Atelier en arrière-plan » | `:2083`, `:2084` | **aucune** | question |
| Valider le composeur sur une capacité d'outil | `submitComposer` puis `ouvrirDestination` (`:1779-1789`, `:1761-1767`) | **aucune** | question |
| Navigation posée dans le store | effet de navigation, `:1280-1326` | B-994 seulement si une vue est affichée (`:1293`) | question, et le store revient à l'écran affiché |
| Tiroir : ouvrir ou créer une conversation | `openChat` par `onOpenChat` | verrou puis saisie, avant toute mutation (B-991, `components/prototype/PrototypeConversationDrawer.tsx:258-285`) | la coque passe au tiroir les surfaces qu'`openChat` démontera à la largeur courante |
| **Rétrécissement sous 1280 px** | `components/prototype/ConversationCanvasPrototype.tsx:1587-1589` | aucune | **aucune question, le chat n'est pas touché ; le panneau se replie comme aujourd'hui et la saisie est mise à l'abri (V4-1)** |

**Le mécanisme.** `changerLePanneau(surfaces, effet)` s'écrit `if (blockStreamingNavigation({ surfaces })) return; effet();`. `blockStreamingNavigation` est, dans la coque, la délégation locale de `sortieRefusee` : il passe donc par la garde commune (P-125 V4, § 6), et par ses quatre clauses dans leur ordre (vocale, flux, interdits, saisie). Les fonctions qui se gardent déjà en tête (`chooseScenario`, `chooseCapability`, « Travaux », la séance, les actions) passent leurs surfaces à cette garde ; les sorties sans garde (croix, carte, pastilles, composeur) passent par `changerLePanneau`.

**La garde de source, par sites (V4-2).** Test `components/prototype/sortiesDuDevis.sites.test.ts`, sur le modèle de `lib/lexiqueTitres.test.ts`. Il relève dans la coque chaque écriture des huit états (`setCanvasOpen`, `setCalculatorOpen`, `setDeliverablesOpen`, `setImagesOpen`, `setFollowUpsOpen`, `setVoiceOpen`, `setScenario`, `setSelectedInvoiceId`) et lui attribue son **site** : la fonction englobante la plus proche (`function nom(`, `const nom = (…) =>`, `const nom = useCallback(`, `nomRef.current = (`, propriété JSX `onX={`), ou, pour un effet, le marqueur `// site : nom` posé sur la ligne de son `useEffect(`. Le lot 5 extrait en fonctions nommées les gestionnaires en ligne qui écrivent ces états : pastilles (`ouvrirLeBoardEnFond`, `ouvrirLAtelierEnFond`, `components/prototype/ConversationCanvasPrototype.tsx:2083-2084`), point d'attention (`ouvrirLePointDAttention`, `:2144-2149`), carte (`ouvrirUnePiece`, `ouvrirUnNouveauDevis`, `:2223-2231`). La table des sites, dans le test :

| Verdict | Sites (à `7baf1793`) | Ce que le test vérifie |
|---|---|---|
| `gardé` | `openChat`, `openEmbeddedView`, `ouvrirLeTravailRef`, `collapseScenarioPanel`, `chooseScenario`, `chooseCapability`, `ouvrirLaSeanceRef`, `ouvrirLeBoardEnFond`, `ouvrirLAtelierEnFond`, `ouvrirUnePiece` | le corps appelle `changerLePanneau(` ou `blockStreamingNavigation({ surfaces` avant sa première écriture |
| `gardé par le retour B-994` | l'effet de navigation (`// site : effet-de-navigation`) | le corps appelle `sortieRetenueParUneSaisie([` avec `'panneau'` avant sa première écriture (le retour B-994 de `:1293`, étendu au panneau) |
| `gardé par l'appelant` | `rangerPourLAccueil` (appelé par l'action `home.open`, `:1866-1873`), `ouvrirDestination` (appelé par `chooseCapability` et `submitComposer`) | chaque appel textuel est dans un site `gardé` |
| `hors du devis`, avec motif | `collapseToolPanel` (appelé quand un panneau d'outil est affiché, qui passe avant le devis), la réouverture B-1386 (`:1366-1378`, seulement avec une vue affichée, qui a déjà refermé le panneau), `ouvrirLePointDAttention` (parcours `today` seulement), les cartes des autres parcours (`onOpenContact`, `onOpenMessage`, `onOpenEvent`, `onNewEvent`, `onOpenDecision`, `onNewBoard`, `onOpenCurrent`, `onOpenTask`, `onNewMission`, rendues hors du parcours `invoice`), `onContinueInChat` (espace Voix affiché) | le motif est écrit dans la table |
| `ouvre le devis` | `ouvrirUnNouveauDevis` | rien |
| `exception` | l'effet de rétrécissement (`// site : retrecissement`) | la mise à l'abri (V4-1) |

Une écriture dont le site n'est pas dans la table, ou un site `gardé` qui écrit avant de se garder, rougit la garde : elle force la question « cette écriture démonte-t-elle un formulaire ? ». Sabotage : une écriture brute dans `ouvrirUnePiece`, hors de `changerLePanneau`.

La garde protège la **question** ; la mise à l'abri protège la **saisie**. Une écriture manquée par la garde ne perd donc plus rien : elle ne pose simplement pas la question.

### 6.5 Ce que chaque hôte garde, ce qu'il gagne

**Panneau Facturer.** Garde tout ce que la V2 énumère. Gagne : `statut_attendu: 'draft'` à chaque mise à jour, et sur un 409 ou un 404 la saisie intacte, le brouillon enregistré oublié, « Créer un nouveau devis avec cette saisie » (rien ne part sans ce clic) ; la question d'abandon sur les gestes de la table ; la mise à l'abri pour le reste ; saisie décimale, total HT par ligne, taux nommés, mention et avertissement de régime.

**Modale.** Garde tout ce que la V2 énumère. Gagne : `validerPiece` seul juge, fin du remplacement silencieux d'une validité 0 par 30 (`components/invoices/InvoiceForm.tsx:801`), quantité décimale, champ fautif relié pour chaque règle, cause du serveur au pied, carnet illisible distingué, mention et avertissement de régime, « Brouillon » absent pour une pièce émise (V4-4), et la question d'abandon quand une navigation venue du store veut fermer sa vue (R-121-4).

### 6.6 Ce que l'utilisatrice verra changer

Le même formulaire, les mêmes libellés, dans Facturer et dans Devis et factures. Changements volontaires, chacun couvert par un test qui le dit : quantité 0,5 acceptée des deux côtés ; taux 0 qui ne se dit plus « exonéré » en régime normal ; mention sous les totaux identique à celle du PDF ; avertissement quand une franchisée taxe une ligne ; validité et échéance signalées par un message relié au champ ; « Brouillon » absent pour une facture émise ; dans Facturer, question avant de perdre un devis entamé par un geste, et devis repris après un rétrécissement de la fenêtre.

### 6.7 Hors périmètre, nommé

- Le verrouillage des lignes et des montants d'une facture émise (B-1506 couvre suppression et retour au brouillon).
- `tva_applicable` jamais envoyé à la création par les formulaires : aucun formulaire ne propose de le poser.
- P-075, P-074, la modification d'un devis existant depuis Facturer (V1-Q4), échéance et validité comme règles du moteur (Q-serveur).
- Fermer le chat qui referme le panneau (R-121-2).
- Une saisie mise à l'abri qui survivrait à un rechargement.

## 7. Livraison en lots TDD

Chaque lot : tests écrits d'abord et vus rouges pour la bonne raison, sauf caractérisations et non-régressions (sabotées pour prouver qu'elles mordent) ; un commit par lot ; sabotage ciblé par fonction, jamais par chaîne globale (règle du 27/08) ; les six portes du dépôt ; revue de conception au début du lot, revue adverse du diff à la fin ; recette navigateur sur la pile jetable (17393 et 1420, jamais 17293) quand le lot touche l'affichage. Chaque lot se livre seul.

**Lot 0. Caractérisation (aucun code applicatif).** Verts à HEAD et jusqu'au lot 6 :
- `tests/test_f1_coherence_des_couches.py` étendu : 2,5 × 1,25 € et 1 × 1,005 € traversent base, schéma, PDF et trésorerie à 3,13 € et 1,01 € HT ;
- `components/invoices/InvoiceForm.caracterisation.p121.test.tsx` : une facture existante dont l'échéance précède l'émission se marque payée et s'enregistre ; le total HT de chaque ligne s'affiche ;
- `components/prototype/parite.devis.p121.test.tsx` : dans les deux hôtes, trois lignes de 33,33 € à 20 % annoncent 120,00 € TTC ;
- `components/prototype/ConversationCanvasPrototype.fermerLeChat.p121.test.tsx` : à 1440 px, ouvrir le chat depuis Facturer laisse le panneau ; le fermer le referme (fige R-121-2 ; à retirer si R-121-2 est corrigé).
Critère observable : `pytest` et `vitest` verts, aucun fichier applicatif touché.

**Lot 1. Moteur et store.** Rouges d'abord :
- `tests/test_p121_statut_attendu.py` : `test_statut_attendu_draft_sur_un_devis_envoye_rend_409` (détail « Ce devis n'est plus un brouillon (statut : Envoyé)… », lignes et totaux intacts) ; `test_statut_attendu_draft_sur_un_brouillon_rend_200` ; `test_sans_statut_attendu_rien_ne_change` ; `test_identifiant_inconnu_rend_404` ;
- concurrence, deux ordres forcés par une barrière injectée dans `update_invoice` : `test_concurrence_mise_a_jour_puis_envoi` (la mise à jour avec `statut_attendu='draft'` passe la première : 200, son `UPDATE` a vu `draft` ; l'envoi suit : 200 ; la base contient un devis `sent` dont les lignes sont celles de la mise à jour, ce qui est l'ordre légitime) ; `test_concurrence_envoi_puis_mise_a_jour` (l'envoi passe le premier : la mise à jour rend 409 et les lignes d'avant sont intactes). Motif : l'écriture conditionnelle tient le verrou d'écriture de SQLite jusqu'au commit ; aucun entrelacement n'est possible, seuls ces deux ordres le sont ;
- `tests/test_p121_mention_de_tva.py` : `mention_de_tva` sur toute la table partagée (sabotage : inverser la condition `sans_tva` dans la seule fonction) ;
- `tests/test_p121_regime_tva.py` : `/billing/profile-status` rend `regime_tva` pour les trois régimes et `normal` sans profil, `tva_intra_renseigne` inchangé ;
- `stores/billingProfileStore.regimeTva.test.ts` ; `components/prototype/usePrototypeInvoiceData.statutAttendu.test.ts` (`statut_attendu: 'draft'` envoyé) ;
- `components/prototype/InvoiceConversationCard.devisPlusBrouillon.test.tsx` : 409 simulé par le module d'API, message affiché, saisie intacte, aucun `createInvoice` sans clic, puis « Créer un nouveau devis avec cette saisie » crée une pièce ; même chemin pour un 404.
Non-régression : `tests/test_b1506_facture_emise_intouchable.py`.
Critère observable : les tests ci-dessus verts ; aucun parcours de l'application n'est modifié.

**Lot 2. Module pur, branché dans la modale.** Rouges d'abord :
- `components/invoices/saisieDePiece.test.ts` : les cas de la V2, plus totaux avec `tvaApplicable` faux ; `mentionDeTva` sur la table partagée ; avertissement de régime pour les deux régimes exonérés ; statut `draft` envoyé quand il diffère du chargé, **sauf pour une facture ou un avoir émis** ; `statutsProposes` sans « Brouillon » pour une pièce émise, avec pour un devis envoyé ; chaque ancien `required` a son cas vide ;
- dans la modale : `validité 0 refusée, texte de validerPiece relié au champ (aria-describedby), rien ne part` ; `échéance antérieure refusée à la création, acceptée sur une pièce existante dont on ne touche pas les dates` ; `franchise, une ligne à 20 % et une à 0 % : aucune mention 293 B, avertissement affiché` ; cause du serveur au pied ; carnet illisible annoncé ;
- `components/invoices/InvoiceForm.statutsEmise.b1506.test.tsx` (R-121-3) : facture envoyée ouverte dans la modale, la liste des statuts ne propose pas « Brouillon ».
Non-régression, verts sans modification : `components/invoices/InvoiceForm.sansTva.b1518.test.tsx` (sabotage : ignorer `tvaApplicable` dans `totauxDePiece`, rouge), `components/invoices/InvoiceForm.retourBrouillon.b1492.test.tsx`, `components/invoices/InvoiceForm.validiteHorsBornes.b1493.test.tsx`, et l'ensemble des tests `InvoiceForm.*`.
Test réécrit : `components/invoices/InvoiceForm.test.tsx:85-113` garde ses assertions ; son commentaire sur la validation native est réécrit.
Critère observable : dans l'app, une validité de 0 affiche un message sous le champ et rien ne part ; une facture envoyée ne propose plus « Brouillon ».

**Lot 3. `LignesDePiece` dans les deux hôtes.** Inchangé depuis la V2 (une seule garde de présentation à la place de `ligneDevis.b1355` et `colonnesDesLignes`, recette à 1280, 1024 et 800 px, 100 % et 125 %, deux thèmes).

**Lot 4. `CorpsDePiece`, `useSaisieDePiece`, migration du panneau, mise à l'abri.** Inchangé depuis la V2 (test de parité des deux hôtes, mention et avertissement identiques), plus `components/prototype/InvoiceConversationCard.miseALAbri.test.tsx`, rouges d'abord :
- `devis modifié, panneau démonté sans réponse : rouvrir Facturer rend la même saisie, avec « Devis repris là où tu l'avais laissé »` ;
- `devis modifié puis « Abandonner » : rien n'est gardé` ; `devis enregistré puis démonté : rien n'est gardé` ;
- `rétrécir sous 1280 px avec un devis entamé, chat ouvert : aucune question, panneau replié, chat intact` ; `même geste pendant une réponse : la réponse reste visible et « Arrêter la réponse » reste offert` ; `même geste avec une pièce jointe au composeur : elle est conservée` ; `après le rétrécissement, une Action qui finit rouvre la conversation` (Finding 7, non-régression).
Critère observable : dans l'app, un devis entamé, la fenêtre rétrécie puis élargie, Facturer rouvert : le devis est là.

**Lot 5. Registre à surfaces, garde commune, sorties.** Rouges d'abord :
- `lib/saisieEnCours.surfaces.test.ts` : `sortieRetenueParUneSaisie(['vue'])` ignore une garde `panneau` ; `uneSaisieEstModifiee` ne pose aucune question ; les tests de `TaskForm` et `EventForm` (B-978, B-991, B-994) restent verts sans modification ;
- si ce lot est le premier des trois lots 5 à passer : `lib/gardeDeNavigation.test.ts`, les tests par clause de P-125 V4 § 6 ; sinon, ceux de la clause saisie dans sa nouvelle forme ;
- `components/prototype/ConversationCanvasPrototype.sortiesDuDevis.test.tsx`, un test par ligne de la table, à 1440 px ou sous le seuil selon la ligne : `sous le seuil, « Nouvelle conversation » : question posée, « Continuer la saisie » rend le devis intact` ; `clic sur une pièce de la carte : question, devis intact` ; `pastille Board : question` ; `valider le composeur sur une capacité d'outil : question` ; `fermer le chat à 1440 px : question` ; `action rapide qui pose une vue dans le store : question, store revenu à l'écran affiché, devis intact` ; `tiroir sous le seuil : question posée avant tout changement de conversation (currentConversationId inchangé)` ; `une seule question par geste` (B-994) ; `session vocale active : chaque sortie de la table refusée par la clause vocale, aucune question, devis intact` (si P-109 est fusionné) ;
- **non-régression, verts à HEAD par construction** (le panneau ne s'inscrit nulle part aujourd'hui) : `à 1440 px, « Nouvelle conversation », ouvrir le chat et « Vider » : aucune question, devis intact` ; `tiroir à 1440 px : aucune question`. Sabotage : inscrire le panneau avec `vue`, rouge ;
- `components/invoices/InvoiceForm.registreDesSaisies.test.tsx` (R-121-4) : `modale modifiée, « Voir » d'une notification pose chat dans le store : la modale pose sa question, la vue Devis et factures reste, le store revient à invoices` ; `ContactModal modifiée, même geste : comportement inchangé (non inscrite)` ;
- `components/prototype/sortiesDuDevis.sites.test.ts` : la garde de source par sites (sabotage : une écriture brute dans `ouvrirUnePiece`).
Critère observable : à 1440 px, un devis entamé puis « Nouvelle conversation » ne pose aucune question et le devis reste à côté du chat ; sous 1280 px, le même geste pose « Abandonner les modifications ? ».

**Lot 6. Ménage et garde anti-retour.** Inchangé depuis la V2 (suppression du code mort du panneau, garde contre une seconde liste de taux, un second calcul de totaux ou un alias d'arrondi, recette du parcours de Claire, PDF aux montants de l'écran), plus la mention de l'écran relevée sur chaque PDF de la recette.

## 8. Défauts qui existent sans aucune RFC

- **R-121-1 : fermé** par B-1518 (`369e068b`).
- **R-121-2, inchangé** : fermer le chat referme aussi le panneau ouvert à côté (1280 px et plus) et jette un devis entamé sans question (§ 0 de la V3, constat 2 de la revue V2). À décider ; s'il est corrigé, une ligne de la table disparaît.
- **R-121-3, nouveau, à reproduire** : la modale propose encore « Brouillon » pour une facture émise (`components/invoices/InvoiceForm.tsx:82-88`, `components/invoices/InvoiceForm.tsx:736`), que le moteur refuse depuis B-1506 (409, `routers/invoices.py:566-573`). Reproduction : une facture envoyée, « Modifier », statut « Brouillon », « Enregistrer » : 409 « émets un avoir ». Corrigé au lot 2.
- **R-121-4, nouveau, à reproduire (lu au code)** : une modale de devis ou de facture modifiée est fermée sans question par une navigation posée dans le store. Le chemin : une Action finit, sa notification propose « Voir » (`stores/actionsStore.ts:94`), la notification est au-dessus de la modale (`styles/z-layers.ts:25`), « Voir » appelle `loadConversation`, qui pose `chat` (`stores/chatStore.ts:167-172`) ; l'effet de navigation consulte le registre (`components/prototype/ConversationCanvasPrototype.tsx:1293`), où la modale n'est pas inscrite, puis ouvre le chat et démonte la vue `invoices`. Reproduction : lancer une Action, ouvrir un devis dans Devis et factures, changer une ligne, cliquer « Voir » à la fin de l'Action : la modale disparaît, la modification est perdue. Corrigé au lot 5.

## 9. Risques et régressions à protéger

- **Deux gardes de présentation contradictoires** (`ligneDevis.b1355`, `colonnesDesLignes`) : une seule survit, au lot 3.
- **Identifiants et noms accessibles** (B-234, B-578) : une table par hôte ; les tests `identifiants`, `nomsAccessibles`, `boutonsNommes` et `da` restent verts.
- **B-011** : pas de second `<form>`.
- **`noValidate`** : chaque ancien `required` a son cas vide dans `saisieDePiece.test.ts`.
- **Registre à surfaces** : un hôte futur (P-075) devra déclarer sa surface ; la garde par sites ne couvre que la coque.
- **Mise à l'abri** : une place, en mémoire ; un second devis entamé après un premier mis à l'abri reprend le premier au montage (il n'y a qu'un devis `new-devis` à la fois) ; dit par la ligne d'état.
- **Effet de navigation** : étendre le retour B-994 au panneau touche un effet que BUG-139 et B-816 ont rendu délicat ; les tests `ConversationCanvasPrototype.parite` et ceux de B-994 restent verts.
- **Garde commune** : ses tests par clause vivent avec elle (P-125 V4, § 6).
- **Table de mentions** : si le texte du PDF change, les deux suites rougissent ensemble.
- **Largeur** : jsdom ne voit ni débordement ni troncature ; seule la recette prouve B-1355, B-1387 et claire-28.

## 10. Questions réservées à Ludo

Aucune. Ce chantier n'efface aucune donnée chez les utilisatrices (la mise à l'abri en garde plutôt), n'annonce rien publiquement et ne touche pas à la marque. Les choix ouverts sont tranchés au § 5, chacun avec son motif ; R-121-2 relève d'un arbitrage de conception que la règle de délégation couvre.

## Annexe : appuis dans le code (à `7baf1793`)

- Modale : `components/invoices/InvoiceForm.tsx` : statuts `:72-88`, question d'abandon `:221`, totaux `:334-361`, envoi `:363-495`, garde de validité `:377-385`, statut (B-1492) `:444`, date de paiement `:497-500`, voile `:610-619`, dialogue `:622-624`, formulaire `:649`, `required` `:713`, `:764`, `:774`, `:873`, `:885`, liste des statuts `:736`, validité `:798-801`, bouton `:1035`.
- Panneau : `components/prototype/InvoiceConversationCard.tsx` : `DevisDraftForm` `:310`, états `:336-349`, `invalidateDraft` `:372-376`, hôte `:722-727`. Données : `components/prototype/usePrototypeInvoiceData.ts:28-72`, `:157-164`.
- Coque : `components/prototype/ConversationCanvasPrototype.tsx` : garde `:1076-1091`, `openChat` `:1195-1216`, `openEmbeddedView` `:1225-1240`, effet de navigation `:1280-1326`, réouverture B-1386 `:1366-1378`, « Travaux » `:1410-1429`, `fermerLeChat` `:1514-1525`, `collapseToolPanel` `:1526-1533`, `collapseScenarioPanel` `:1534-1537`, rétrécissement `:1587-1589`, `rangerPourLAccueil` `:1636-1650`, `chooseScenario` `:1652-1676`, `chooseCapability` `:1678-1720`, séance `:1731-1742`, `ouvrirDestination` `:1761-1777`, `submitComposer` `:1779-1805`, actions `:1856-1881`, pastilles `:2083-2084`, point d'attention `:2144-2149`, carte `:2219-2233`, ternaire latéral `:2470-2515`.
- Navigation : `stores/navigationStore.ts:104-116` ; raccourcis : `hooks/useKeyboardShortcuts.ts:58-63` ; couches : `styles/z-layers.ts:7-30`.
- Registre : `lib/saisieEnCours.ts:12-36` ; `hooks/useAbandonDeSaisie.ts:60-83` ; `hooks/useQuestionDAbandonDeModale.ts:18-76`.
- Moteur : `routers/invoices.py` : montants `:194-217`, réponse `:267-280`, création `:440-500`, mise à jour `:531-630`, B-1506 `:566-573`, `:676`, `:701-711`, profil `:849-876` ; `models/schemas.py:1245-1265`, `:1316-1344` ; `models/database.py:219-234` ; `services/invoice_pdf.py:653-689`.
- Lectures seules du statut : `services/workspace_tools.py:762`, `services/notification_service.py:125`, `services/action_agents.py:467`.
