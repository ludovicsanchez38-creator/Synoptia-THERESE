# RFC P-121 (V3) : un seul formulaire de devis, pour la création et la modification

Rédigé le 26/09/2026 ; lignes relues sur `main` à `feac6303`, revérifiées à `a3c98b74` (les commits intermédiaires, B-1503 à B-1505, ne touchent aucune ligne citée ici). Remplace la V2 du même jour (`docs/plans/2026-09-26-rfc-p121-un-formulaire-de-devis-v2.md`), refusée par la revue adverse du 26/09 (constats 1 à 8, verdict NO-GO). Proposition acceptée par Ludo le 25/09 sous une contrainte explicite : **aucune perte de fonctionnalité**. Les décisions 26 à 29 du 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md:93-102` et `:183-186`) sont posées comme des faits. Aucun code avant la validation de ce document.

Chemins relatifs à `src/frontend/src/` (écran) et `src/backend/app/` (moteur), sauf mention. Toutes les lignes citées ont été lues à `feac6303` par `git show HEAD:` : la rédaction a commencé à `66b78788`, quinze commits sont arrivés pendant, dont les deux prérequis (B-1492 et B-1493), et toutes les citations ont été recalées puis revérifiées ; l'arbre de travail portait des modifications non commitées, qui ne sont pas la base. Entre `900765fb` (base de la V2) et `feac6303`, un seul des fichiers examinés ici a bougé sur les lignes citées : `InvoiceForm.tsx` (B-1492 autour de la mise à jour du statut, B-1493 autour de la validité) ; `services/mcp_therese_server.py` et `services/workspace_tools.py` ont changé plus loin que les lignes citées. Ses numéros de ligne dans la V2 sont décalés d'une dizaine au-delà de la validation ; les autres restent justes, sauf là où la V3 les corrige.

## 0. Les constats de la revue et leur traitement

| Nº | Constat | Verdict et preuve relue à HEAD | Traitement | Où |
|---|---|---|---|---|
| 1 | La validation native bloque une pièce existante avant `validerPiece` : la décision 27, telle que la V2 la pose, est déjà fausse dans la modale | **Accepté ; défaut existant, B-1493, corrigé pendant la rédaction** (commit `feac6303`) : `min` et `max` retirés du champ Validité, et une garde applicative ne refuse plus qu'une validité **saisie** hors de 1 à 365 (`components/invoices/InvoiceForm.tsx:374-382`) ; test `InvoiceForm.validiteHorsBornes.b1493.test.tsx` (devis existant à 400 jours dont on change les notes : il s'enregistre). Restent à HEAD : le formulaire sans `noValidate` (`InvoiceForm.tsx:646`), dont le bouton est rattaché par `form=` (`:1032`), et cinq `required` que la revue ne relevait pas (`:710`, `:761`, `:771`, `:870`, `:882`), que `InvoiceForm.test.tsx:97-100` décrit en commentaire ; et le remplacement silencieux d'une validité 0 ou vide par 30 (`InvoiceForm.tsx:798`). Le moteur accepte toute validité (`models/schemas.py:1323`, `:1338` ; `routers/invoices.py:467-469`, `:597-598`) | Le formulaire commun porte `noValidate` et `validerPiece` devient le seul juge, champs vides compris ; la garde de B-1493 y passe telle quelle et son test reste vert ; au lot 2, le test « validité 0 » lit le texte rendu par `validerPiece` | § 3, § 6.2, lot 2 |
| 2 | Inscrire le panneau Facturer au registre global le ferait consulter par des gestes qui ne le démontent pas | **Accepté en partie.** Juste pour ouvrir le chat, « Nouvelle conversation » et « Vider » à 1280 px et plus : `openChat` ne referme le panneau que sous le seuil (`components/prototype/ConversationCanvasPrototype.tsx:1207`), `startConversation` (`:1217-1224`) et `chat.clear` (`:1877-1881`) passent par lui. **Faux pour fermer le chat** (croix `:2066`, Échap `:1615`) : `fermerLeChat` appelle `goBack` (`:1522-1524`), qui rend `activeView` à `null` quand la pile est vide (`stores/navigationStore.ts:106-112`), et l'effet de navigation de la coque referme alors le panneau (`ConversationCanvasPrototype.tsx:1305-1315`) ; si la pile porte une vue, c'est `openEmbeddedView` qui le referme (`ConversationCanvasPrototype.tsx:1322`, puis `:1234`). Fermer le chat démonte donc bien le devis | Registre à surfaces : chaque garde déclare ce qu'elle protège (`vue` ou `panneau`), chaque sortie ne consulte que les surfaces qu'elle démonte ; le tiroir reçoit de la coque la liste des surfaces qu'ouvrir le chat démontera. Tests à 1440 px et sous le seuil | § 6.4, lot 5 |
| 3 | Cliquer une pièce dans la carte Facturer démonte le devis sans question ; énumérer les sorties à partir des écritures | **Accepté, et élargi.** `ConversationCanvasPrototype.tsx:2223-2227` (`setSelectedInvoiceId` sans garde), `InvoiceConversationCard.tsx:726`. L'énumération proposée (trois états) est elle-même incomplète : le ternaire du panneau latéral de la coque rend d'abord cinq panneaux d'outils (`ConversationCanvasPrototype.tsx:2470-2508`), ouverts sans garde par `ouvrirDestination` (`:1763-1767`, appelée par `submitComposer` à `:1785`) ; les pastilles de fond changent le parcours sans garde (`:2083-2084`) ; l'effet de navigation referme le panneau (`:1305-1315`) | Les sorties sont relevées à partir de ce que l'arbre de rendu démonte réellement (huit états, § 6.4) ; toutes passent par une seule fonction gardée ; un test par sortie et une garde de source | § 6.4, lot 5 |
| 4 | La mention légale de l'écran ne suivrait pas la règle du PDF (franchise, lignes mixtes) | **Accepté.** `services/invoice_pdf.py:676-689` : la mention 293 B n'est imprimée que si `tva_applicable` est faux ou si toutes les lignes sont à 0 % en franchise ; sinon « TVA incluse selon les taux en vigueur » | Une seule règle, extraite du PDF en fonction pure ; une table de cas partagée, lue par `pytest` et par `vitest` ; avertissement non bloquant quand le régime déclare une exonération et qu'une ligne est taxée | § 6.1, § 6.2, lots 1 et 2 |
| 5 | Le rétrécissement ne peut pas replier le chat « quand une saisie est retenue » : le registre n'offre qu'une consultation qui pose la question | **Accepté.** `lib/saisieEnCours.ts:25-31` ; `hooks/useAbandonDeSaisie.ts:77-80` (`setAbandonDemande(true)` dans la garde) | Lecture sans effet `uneSaisieEstModifiee(surfaces)` | § 6.4, lot 5 |
| 6 | `totauxDePiece` n'a pas de miroir de `tva_applicable = false`, alors que la modale modifie des pièces qui le portent | **Accepté ; c'est aussi un défaut existant.** La pièce lue le porte (`services/api/invoices.ts:28`, `routers/invoices.py:273`, `models/schemas.py:1247`), l'API l'accepte à la création (`models/schemas.py:1317`), de telles pièces existent en base (migration `models/database.py:219-234`), et la modale calcule déjà ses totaux sans lui (`InvoiceForm.tsx:335-340`) contre le moteur (`routers/invoices.py:215-217`) | `totauxDePiece(lignes, tvaApplicable)` et `mentionDeTva` reçoivent la valeur de la pièce chargée (vrai à la création) ; défaut existant fiché R-121-1 | § 6.2, § 9, lot 2 |
| 7 | La modale n'envoie jamais le statut `draft` : remettre un devis en Brouillon est ignoré en silence | **Accepté ; défaut existant, B-1492, corrigé depuis par l'orchestrateur** (commit `b39ac7d8` : le statut part dès qu'il diffère du statut chargé, `InvoiceForm.tsx:438-441` ; test `InvoiceForm.retourBrouillon.b1492.test.tsx`). Le moteur n'écrit le statut que s'il est fourni (`routers/invoices.py:586-588`) | `requeteDePiece` reprend la règle de B-1492 ; son test reste vert à chaque lot, et `saisieDePiece.test.ts` fige la même règle dans le module | § 3, § 6.2, lot 2 |
| 8 | Le critère observable du lot 1 est vrai sans code, le 409 n'est atteint par aucun parcours, son texte suppose une origine | **Accepté.** Ouvrir Devis et factures referme le panneau (`ConversationCanvasPrototype.tsx:1234`) ; `brouillonEnregistre` est un état local du formulaire (`InvoiceConversationCard.tsx:344`) ; aucune écriture de statut de pièce hors de `routers/invoices.py` (les services ne font que lire : `services/workspace_tools.py:762`, `services/notification_service.py:125`, `services/action_agents.py:465` ; le serveur MCP liste et crée, `services/mcp_therese_server.py:268-269`). Il ne subsiste aucun mode classique : `InvoicesPanel` n'est monté que comme vue embarquée (`components/prototype/PrototypeUnifiedViewCanvas.tsx:94`) | La précondition reste, comme garde du moteur (décision 29). Le critère devient un test composant (409 simulé) et un test moteur de concurrence ; le message ne suppose plus d'origine | § 6.1, lot 1 |

Aucun constat n'est réfuté en entier. Le constat 2 l'est sur un point (fermer le chat), preuve à l'appui, et ce point change le traitement : fermer le chat pose la question, puisqu'il démonte le devis.

## 1. Ce que la V3 garde de la V2

- Le constat de départ (Claire, `docs/campagnes/2026-09-25-personas-c13/rapports/claire.md`, claire-31) et la recommandation : option A, un corps de saisie commun, deux hôtes qui gardent leur cycle de vie.
- L'inventaire ligne par ligne du § 3.3 de la V2, relu à `feac6303` : il reste juste (numéros de `InvoiceForm.tsx` décalés au-delà de la validation, lignes « Statut » et « Validité » corrigées par B-1492 et B-1493), et c'est lui que les tests de parité reprennent. Seule la phrase sur les sorties du panneau (V2 `:128`) est remplacée par la table du § 6.4.
- Les décisions V1-Q1, V1-Q2, V1-Q4, Q-quantité et Q-serveur, avec leur motif (V2 § 2).
- La précondition `statut_attendu` par écriture conditionnelle, et le régime de TVA exposé par `/billing/profile-status` (V2 § 5.1).
- Le module pur, `useSaisieDePiece`, `LignesDePiece`, `CorpsDePiece`, les identifiants par hôte, l'absence de second `<form>` (B-011), la requête de conteneur (V2 § 5.2 à § 5.4), et le hors périmètre (V2 § 5.8), à une ligne près (§ 2).

## 2. Ce que la V3 retire ou reporte, et pourquoi

- **Retiré : l'inscription du panneau au registre global** (V2 `:198`, lot 5 `:269-270`). Elle aurait fait poser « Abandonner les modifications ? » par des gestes qui laissent le devis intact (constat 2). Remplacée par le registre à surfaces (§ 6.4).
- **Retiré : la liste des sorties « énumérées à partir des fonctions »** (V2 lot 5). Elle oubliait la carte, les pastilles et les panneaux d'outils (constat 3). Remplacée par une table tirée de ce que l'arbre de rendu démonte.
- **Retiré : « la mention légale s'écrit dès qu'une ligne est à 0 % hors régime normal »** (V2 `:168`). Elle aurait affirmé à l'écran une mention que le PDF n'imprime pas (constat 4).
- **Retiré : « `tva_applicable = false` n'a pas besoin de miroir »** (V2 `:171`, et le point correspondant du § 5.8). La modale modifie de telles pièces (constat 6). Reste hors périmètre le fait qu'aucun formulaire n'envoie ce champ à la création.
- **Retiré : le critère observable du lot 1** (V2 `:253`) et le texte du 409 qui nommait Devis et factures (V2 `:160`) (constat 8).
- **Retiré, comme fait établi : « une pièce existante qui viole la règle reste enregistrable tant qu'on ne touche pas ce champ »** (V2 `:11`, `:24`). C'était faux à la base de la V2 (constat 1) ; B-1493 l'a rendu vrai pour la validité ; la V3 le tient pour toutes les règles, par `noValidate` et `validerPiece`, prouvé par des tests.
- **Reporté, hors de ce chantier : fermer le chat referme aussi le panneau ouvert à côté.** C'est peut-être un défaut en soi (l'entrée 9 promet que le chat garde l'objet qu'il commente) ; il est fiché à reproduire (R-121-2). Tant qu'il existe, fermer le chat pose la question ; s'il est corrigé, le test du lot 5 correspondant devient « aucune question, devis intact ».

## 3. Prérequis, corrigés hors RFC par l'orchestrateur

- **B-1492**, fermé (commit `b39ac7d8`) : remettre un devis en Brouillon était ignoré ; le statut part désormais dès qu'il diffère du statut chargé (`InvoiceForm.tsx:438-441`). Le lot 2 garde cette règle dans `requeteDePiece`.
- **B-1493**, fermé (commit `feac6303`) : `min` et `max` retirés du champ Validité (`InvoiceForm.tsx:792-801`), garde applicative pour une validité saisie (`:374-382`), test `InvoiceForm.validiteHorsBornes.b1493.test.tsx`. Le lot 2 va plus loin avec `noValidate` (§ 6.2).

Les deux prérequis sont fermés : rien n'empêche le lot 0 de commencer après la validation de ce document.

## 4. Le besoin

Claire crée son devis dans le panneau « Facturer » et le modifie dans la modale de « Devis et factures » : même objet, deux codes, deux jeux de règles. Chaque correctif de devis a dû être posé deux fois (B-1411 et B-017, B-1413 et la date civile du panneau), ou ne l'a été que d'un côté. Tant qu'il y a deux formulaires, un correctif sur deux manque à l'un d'eux.

## 5. Décisions tranchées

| Nº | Décision | Origine | Ce qu'elle impose ici |
|---|---|---|---|
| 26 | Arrondi commercial au demi-centime supérieur, identique au moteur et à l'écran | Ludo par délégation, 25/09 ; livré par B-1428 | Le module commun n'arrondit que par `lib/auCentime.ts:8-13` |
| 27 | Échéance et validité vérifiées à la création, ou quand le champ est modifié | Ludo par délégation, 25/09 | `validerPiece(saisie, reference)` ; `noValidate` pour que rien d'autre ne juge (constat 1) |
| 28 | Le libellé du taux 0 suit le régime déclaré au profil | Ludo par délégation, 25/09 | `regime_tva` exposé ; la mention suit la règle du PDF (constat 4) |
| 29 | Un devis envoyé ou accepté ne se retouche pas depuis Facturer, refus côté serveur comme à l'écran | Ludo par délégation, 25/09 | Précondition `statut_attendu`, garde du moteur ; aucun parcours de l'écran ne l'atteint aujourd'hui (constat 8) |
| V3-1 | Le formulaire commun porte `noValidate` ; `validerPiece` est le seul juge, champs vides compris | Tranché ici | Motif : la validation native s'interpose avant tout code (constat 1), ne relie pas le champ fautif par `aria-describedby` et ne connaît pas la décision 27. `validerPiece` couvre déjà client, lignes, nombres et dates (V2 `:173`). La date de paiement (`InvoiceForm.tsx:986`) est hors du formulaire et garde sa garde applicative (`InvoiceForm.tsx:497-500`) |
| V3-2 | La mention sous les totaux est celle que le PDF imprimera, calculée par la même règle ; elle ne s'affiche que quand elle n'est pas « TVA incluse selon les taux en vigueur » | Tranché ici | Motif : l'écran ne doit rien affirmer que la pièce ne dira pas (constat 4), et une ligne de plus sur chaque devis ordinaire serait du bruit |
| V3-3 | Régime exonéré (franchise ou formation) et au moins une ligne taxée : avertissement non bloquant | Tranché ici | Motif : la décision 28 ne bloque rien, mais une franchisée qui facture de la TVA doit le voir avant d'envoyer |
| V3-4 | Le registre des saisies en cours connaît des surfaces | Tranché ici | Motif : constat 2 ; une question n'est posée que si la saisie va réellement disparaître |

Les décisions V1-Q1, V1-Q2, V1-Q4, Q-quantité et Q-serveur (V2 `:27-32`) restent en vigueur, avec leur motif.

## 6. Conception

### 6.1 Moteur (lot 1)

**Précondition de statut (décision 29).** Inchangée dans son mécanisme (V2 § 5.1) : `UpdateInvoiceRequest` (`models/schemas.py:1328-1340`) gagne `statut_attendu: str | None = None` ; quand il est fourni, `update_invoice` commence par `UPDATE invoices SET updated_at = :maintenant WHERE id = :id AND status = :statut_attendu`, avant la lecture de la pièce (`routers/invoices.py:541`). Aucune ligne touchée : relecture, 404 si la pièce n'existe plus, 409 sinon, avec un détail qui ne suppose aucune origine : « Ce devis n'est plus un brouillon (statut : Envoyé). Il ne se retouche plus ici. » Sans le champ, rien ne change pour la modale.

Ce que la V3 dit en plus (constat 8) : aucun parcours de l'écran n'atteint ce 409 aujourd'hui. Pendant que le panneau Facturer est monté, rien d'autre dans l'application n'écrit le statut d'une pièce : Devis et factures ne s'ouvre qu'en refermant le panneau, les services ne font que lire, le serveur MCP liste et crée. La précondition est une garde du moteur, pour les appels directs à l'API et pour un hôte futur (P-075) ; elle se prouve par des tests, pas par un parcours.

**Régime de TVA exposé (décision 28).** Inchangé (V2 § 5.1) : `/billing/profile-status` (`routers/invoices.py:819-845`) renvoie `regime_tva` ; sans profil, `normal`.

**Une seule règle de mention (constat 4).** Le calcul de `_build_conditions_block` (`services/invoice_pdf.py:675-689`) sort dans une fonction pure `mention_de_tva(lignes, tva_applicable, regime_tva) -> str`, appelée par le bloc sans changement de comportement. Ses cas vivent dans une table JSON versionnée, `components/invoices/mentionsDeTva.cas.json` (côté écran, pour que Vite l'importe sans sortir de son dossier racine) : chaque cas donne des lignes, `tva_applicable`, un régime et la mention attendue. `pytest` lit cette table et vérifie `mention_de_tva` ; `vitest` lit la même table et vérifie `mentionDeTva` (lot 2). Un cas ajouté d'un côté l'est des deux ; c'est le test de parité que la revue demandait. Cas minimaux : les trois régimes × {toutes les lignes à 0 %, lignes mixtes, toutes taxées}, plus `tva_applicable` faux sous chaque régime, plus aucune ligne.

Aucune colonne ne change ; la tête Alembic reste `b8c9d0e1f2a3`.

### 6.2 Le module pur `components/invoices/saisieDePiece.ts` (lot 2)

Repris de la V2 (§ 5.2), avec ces changements :

- `totauxDePiece(lignes, tvaApplicable)` : si `tvaApplicable` est faux, le TTC de chaque ligne est son HT, comme `_montants_de_ligne` (`routers/invoices.py:215-217`). L'hôte passe la valeur de la pièce chargée, `true` à la création (constat 6).
- `mentionDeTva({ lignes, tvaApplicable, regime })` : la règle de `mention_de_tva`, testée sur la table partagée. L'écran l'affiche sous les totaux sauf quand elle vaut « TVA incluse selon les taux en vigueur » (V3-2). Régime inconnu (profil illisible) : seule la branche `tvaApplicable` faux, qui ne dépend pas du régime, peut produire une mention ; sinon rien n'est affirmé.
- `avertissementDeRegime({ lignes, regime })` : franchise ou exonération formation, et au moins une ligne à un taux non nul : « Ton profil déclare [la franchise de TVA / l'exonération formation], mais une ligne est taxée : cette pièce facturera de la TVA et le PDF n'imprimera pas la mention d'exonération. » Non bloquant (V3-3).
- `validerPiece(saisie, reference)` : les règles de la V2 (client, lignes, description par ligne, nombres, quantité strictement positive, prix positif ou nul, dates, puis échéance et validité selon la décision 27), désormais seul juge (V3-1). Chaque règle rend le champ fautif, que l'hôte focalise et relie.
- `requeteDePiece(saisie, reference)` : en modification, le statut part dès qu'il diffère de `reference.status`, `draft` compris : c'est la règle que B-1492 a posée dans la modale (`InvoiceForm.tsx:441`, constat 7). `tva_applicable` n'est jamais envoyé (la mise à jour ne le connaît pas, `models/schemas.py:1328-1340`).

### 6.3 Les composants et la présentation (lots 3 et 4)

Inchangés depuis la V2 (§ 5.3 et § 5.4), avec deux précisions. Le `<form>` que la modale garde porte `noValidate` (V3-1), le bouton restant rattaché par `form=` (B-011). Le panneau affiche l'avertissement de régime et la mention au même endroit que la modale, sous les totaux.

### 6.4 Le registre à surfaces et les sorties (lot 5)

**Le registre.** `lib/saisieEnCours.ts` change de forme de garde :

```ts
type Surface = 'vue' | 'panneau';
interface Garde { surface: Surface; modifiee: () => boolean; demander: () => void }
inscrireSaisieEnCours(garde: Garde): () => void
sortieRetenueParUneSaisie(surfaces: readonly Surface[] = ['vue']): boolean // pose la question du plus récent formulaire modifié parmi ces surfaces
uneSaisieEstModifiee(surfaces: readonly Surface[]): boolean               // lecture sans effet (constat 5)
```

La valeur par défaut `['vue']` garde à l'identique tous les appelants actuels : `TaskForm` et `EventForm` vivent dans des vues (`components/tasks/TasksPanel.tsx:348`, `components/calendar/CalendarPanel.tsx:696`), et la modale de Devis et factures aussi (`components/prototype/PrototypeUnifiedViewCanvas.tsx:94`), qui s'inscrit avec `vue`. `useAbandonDeSaisie` (`hooks/useAbandonDeSaisie.ts:77-80`) se réécrit en `{ surface: 'vue', modifiee: () => etat.current.modifie, demander: () => setAbandonDemande(true) }`. Le formulaire du panneau s'inscrit avec `panneau` ; son drapeau « modifiée » vient de `useSaisieDePiece` (lot 4) : la saisie diffère de l'état initial, ou du dernier brouillon enregistré. `hasUnsavedChanges` (`InvoiceConversationCard.tsx:345`) ne suffit pas : il n'est posé qu'après un premier enregistrement (`:372-376`), si bien qu'un devis entamé et jamais enregistré, le cas le plus courant, ne le pose pas.

**Quand le devis est-il démonté ?** `DevisDraftForm` est rendu si, et seulement si, aucun des cinq panneaux d'outils n'est ouvert (`calculatorOpen`, `deliverablesOpen`, `imagesOpen`, `followUpsOpen`, `voiceOpen` : ils passent avant dans le ternaire, `ConversationCanvasPrototype.tsx:2470-2508`), que `canvasOpen` est vrai, que `scenario` vaut `invoice` (`:2508`, `:387-400`) et que `selectedInvoiceId` vaut `new-devis` (`InvoiceConversationCard.tsx:726`). Huit états, donc, et c'est leurs écritures qu'on relève, pas les gestes déjà connus.

**Toutes les sorties, relevées à partir de ces écritures** (lignes de la coque, `components/prototype/ConversationCanvasPrototype.tsx`, sauf mention) :

| Sortie | Écriture qui démonte | Garde à HEAD | Comportement voulu |
|---|---|---|---|
| Croix du panneau, `onClose` | `collapseScenarioPanel`, `ConversationCanvasPrototype.tsx:1534-1537` (appelé `:2512-2514`) | aucune | question |
| Ouvrir le chat, « Nouvelle conversation », « Vider », sous 1280 px | `:1207` | registre sans surface (`:1082`) | question |
| Les mêmes à 1280 px et plus | aucune (le panneau reste) | registre sans surface | **aucune question** (constat 2) |
| Fermer le chat (croix `:2066`, Échap `:1615`) | `goBack` (`:1522-1524`), puis `:1305-1315` ou `:1322` et `:1234` | registre sans surface | question tant que R-121-2 n'est pas tranché |
| Ouvrir une vue (rail, palette, « Ouvrir dans Devis et factures », Accueil `:1866`) | `:1234`, `:1639` | registre sans surface | une question, surfaces `vue` et `panneau` (motif B-994 : une seule question par geste) |
| Choisir un parcours ou une capacité | `:1654`, `:1669`, `:1705` | registre sans surface (`:1653`, `:1679`) | question |
| Une ligne de « Travaux » qui ouvre un parcours | `:1422`, `:1425` | registre sans surface (`:1413`) | question |
| Ouvrir une séance depuis l'Agenda | `:1736-1741` | registre sans surface (`:1732`) | question |
| Cliquer une pièce dans la carte Facturer | `:2224` | **aucune** (constat 3) | question |
| Pastille « Board » ou « Atelier en arrière-plan » | `:2083`, `:2084` | **aucune** | question |
| Valider le composeur sur une capacité d'outil | `:1785`, puis `:1763-1767` | **aucune** | question |
| Navigation posée dans le store (actions rapides, commandes, registre) | `:1305-1315`, `:1322` | B-994 seulement si une vue est affichée (`:1293`) | question, et le store revient à l'écran affiché, comme B-994 le fait pour les vues (`:1294-1296`) |
| Tiroir : ouvrir ou créer une conversation | `openChat` via `onOpenChat` | registre sans surface, **avant** toute mutation (B-991, `PrototypeConversationDrawer.tsx:267-285`) | la coque passe au tiroir les surfaces qu'`openChat` démontera à la largeur courante (`vue` à 1280 px et plus, `vue` et `panneau` en dessous) ; le tiroir les consulte avant `loadConversation` |
| Rétrécissement sous 1280 px, chat ouvert | `ConversationCanvasPrototype.tsx:1587-1589` | aucune | ce n'est pas un geste, il ne pose pas de question : si `uneSaisieEstModifiee(['panneau'])`, il replie le chat au lieu du panneau (le brouillon du composeur est déjà écrit sous la clé de sa conversation au démontage, `hooks/useAutosave.ts:161-177`) |

Deux lignes relevées sont sans effet sur le devis et restent hors de la table : le point d'attention de l'Accueil (`ConversationCanvasPrototype.tsx:2146-2148`) n'est affiché qu'en parcours `today`, où le panneau Facturer n'est pas rendu ; la réouverture d'un panneau d'outil B-1386 (`:1372-1377`) n'a lieu qu'avec une vue affichée, qui a déjà refermé le panneau.

**Le mécanisme.** Une seule fonction de la coque, `changerLePanneau(surfaces, effet)`, consulte `sortieRetenueParUneSaisie(surfaces)` puis exécute l'effet ; toutes les sorties de la table y passent, et `blockStreamingNavigation` reçoit les surfaces de son appelant au lieu d'interroger tout le registre. Une garde de source, sur le modèle de `lib/lexiqueTitres.test.ts`, lit `ConversationCanvasPrototype.tsx` et échoue si l'une des huit écritures apparaît hors de `changerLePanneau`, des déclarations d'état et d'une liste d'exceptions motivées (l'effet de rétrécissement, les deux lignes sans effet ci-dessus, les ouvertures du panneau Facturer lui-même). Une écriture ajoutée demain rougit la garde et force la question « démonte-t-elle un formulaire ? ».

**Coordination avec P-125.** Le lot 5 de P-125 (`docs/plans/2026-09-26-rfc-p125-reponse-en-fond-v3.md`) réécrit aussi `blockStreamingNavigation`. Le second des deux lots à passer se rebase sur le premier ; les tests des deux restent verts.

### 6.5 Ce que chaque hôte garde, ce qu'il gagne

**Panneau Facturer.** Garde tout ce que la V2 énumère (§ 5.6). Gagne : `statut_attendu: 'draft'` à chaque mise à jour, et sur un 409 ou un 404 la saisie intacte, le brouillon enregistré oublié, « Créer un nouveau devis avec cette saisie » (rien ne part sans ce clic) ; la question d'abandon, posée seulement par les sorties de la table ; saisie décimale soignée, total HT par ligne, taux nommés, mention et avertissement de régime, profil rafraîchi.

**Modale.** Garde tout ce que la V2 énumère. Gagne : `validerPiece` seul juge (V3-1), fin du remplacement silencieux par 30, quantité décimale, champ fautif relié pour chaque règle, cause du serveur au pied, carnet illisible distingué, totaux justes pour une pièce sans TVA applicable (R-121-1), mention et avertissement de régime, inscription au registre avec `vue`.

### 6.6 Ce que l'utilisatrice verra changer

- Le même formulaire, les mêmes libellés, dans Facturer et dans Devis et factures.
- Changements volontaires, chacun couvert par un test qui le dit : quantité 0,5 acceptée des deux côtés ; taux 0 qui ne se dit plus « exonéré » en régime normal ; mention sous les totaux identique à celle du PDF ; avertissement quand une franchisée taxe une ligne ; dans la modale, validité et échéance signalées par un message relié au champ, au lieu d'une bulle du navigateur (champs vides) ou d'un remplacement silencieux par 30 (validité 0) ; une pièce sans TVA applicable montre le même TTC que le PDF ; dans Facturer, question avant de perdre un devis entamé, et seulement dans ce cas.

### 6.7 Hors périmètre, nommé

- Immutabilité d'une facture émise (V2 § 5.8, inchangé).
- `tva_applicable` jamais envoyé à la création par les formulaires (`InvoiceForm.tsx:430-444`) : aucun formulaire ne propose de le poser. Le lire à la modification est, lui, dans le périmètre (constat 6).
- P-075, P-074, la modification d'un devis existant depuis Facturer (V1-Q4), échéance et validité comme règles du moteur (Q-serveur).
- Fermer le chat qui referme le panneau (R-121-2).

## 7. Livraison en lots TDD

Chaque lot : tests écrits d'abord et vus rouges pour la bonne raison (sauf les caractérisations du lot 0) ; un commit par lot ; sabotage ciblé par fonction, jamais par chaîne globale (règle du 27/08) ; les six portes du dépôt ; revue adverse du diff ; recette navigateur sur la pile jetable (17393 et 1420, jamais 17293) quand le lot touche l'affichage. Chaque lot se livre seul. Prérequis : B-1492 et B-1493, tous deux fermés.

**Lot 0. Caractérisation (aucun code applicatif).**
Verts à HEAD, et verts jusqu'au lot 6 (le devis à validité 400 dont on change les notes est déjà figé par le test de B-1493) :
- moteur (`tests/test_f1_coherence_des_couches.py`) : 2,5 × 1,25 € et 1 × 1,005 € traversent base, schéma, PDF et trésorerie à 3,13 € et 1,01 € HT ;
- modale : une facture existante dont l'échéance précède l'émission se marque payée, change de statut et de notes, et s'enregistre ;
- modale : le total HT de chaque ligne s'affiche ;
- les deux hôtes : trois lignes de 33,33 € à 20 % annoncent 120,00 € TTC ;
- coque, à 1440 px : ouvrir le chat depuis Facturer laisse le panneau ; le fermer le referme (fige l'enchaînement `ConversationCanvasPrototype.tsx:1522-1524`, `:1305-1315` sur lequel la table du § 6.4 s'appuie ; à retirer, avec la ligne correspondante de la table, si R-121-2 est corrigé entre-temps).
Critère observable : `pytest` et `vitest` verts, aucun fichier applicatif touché.

**Lot 1. Moteur et store.**
Rouges d'abord :
- `tests/test_p121_statut_attendu.py` : `PUT` avec `statut_attendu='draft'` sur un devis `sent` rend 409, détail « Ce devis n'est plus un brouillon (statut : Envoyé)… », lignes et totaux intacts ; sur un brouillon, 200 ; sans le champ, 200 sur un devis `sent` ; identifiant inconnu, 404 ;
- concurrence : deux mises à jour lancées ensemble sur le même brouillon, l'une avec `statut_attendu='draft'`, l'autre qui passe le statut à `sent` ; quel que soit l'ordre, la base ne contient jamais un devis `sent` dont les lignes viennent de la première ;
- `mention_de_tva` sur toute la table partagée (sabotage : inverser la condition `sans_tva` dans la seule fonction) ;
- `/billing/profile-status` rend `regime_tva` pour les trois régimes et `normal` sans profil ; `billingProfileStore` garde `regimeTva` ;
- `usePrototypeInvoiceData` envoie `statut_attendu: 'draft'` ;
- panneau, 409 simulé par le module d'API : message affiché, saisie intacte, aucun `createInvoice` sans clic, puis « Créer un nouveau devis avec cette saisie » crée une pièce ; même chemin pour un 404.
Critère observable : les tests ci-dessus verts ; aucun parcours de l'application n'est modifié (constat 8).

**Lot 2. Module pur, branché dans la modale.**
Rouges d'abord : `saisieDePiece.test.ts` (les cas de la V2, plus : totaux avec `tvaApplicable` faux ; `mentionDeTva` sur la table partagée ; avertissement de régime pour les deux régimes exonérés ; statut `draft` envoyé quand il diffère du chargé). Dans la modale : validité 0 refusée au lieu d'être remplacée par 30 (`InvoiceForm.tsx:798`), et le texte affiché est celui de `validerPiece`, relié au champ (`aria-describedby`) ; la garde de B-1493 (`:374-382`) devient une règle de `validerPiece`, et son test reste vert ; échéance antérieure refusée à la création, acceptée sur une pièce existante dont on ne touche pas les dates ; pièce `tva_applicable = false` à une ligne de 100 € à 20 % : 100,00 € TTC ; franchise, une ligne à 20 % et une à 0 % : aucune mention 293 B à l'écran, avertissement affiché ; devis Envoyé remis en Brouillon : le moteur reçoit `draft` (le test de B-1492 reste vert, le même cas passe par `requeteDePiece`) ; cause du serveur au pied ; carnet illisible annoncé.
Test existant réécrit : `InvoiceForm.test.tsx:85-113` garde ses assertions (rien ne part ; message « nombres valides » pour « . ») ; son commentaire `:97-99`, qui décrit la validation native, est réécrit, puisque c'est `validerPiece` qui arrête désormais la quantité vide. Aucun autre test ne fige les comportements abandonnés (V2 `:257`).
Critère observable : les tests `InvoiceForm.*` verts (73 relevés par la V2 à `900765fb`, plus les 2 de B-1492), plus les nouveaux ; dans l'app, une validité de 0 affiche un message sous le champ et rien ne part.

**Lot 3. `LignesDePiece` dans les deux hôtes.** Inchangé depuis la V2 (garde unique à la place de `ligneDevis.b1355` et `colonnesDesLignes`, recette à 1280, 1024 et 800 px, 100 % et 125 %, deux thèmes).

**Lot 4. `CorpsDePiece` et `useSaisieDePiece`, migration du panneau.** Inchangé depuis la V2 (test de parité des deux hôtes), plus : mention et avertissement de régime identiques dans les deux hôtes pour une même saisie.

**Lot 5. Registre à surfaces et sorties.**
Rouges d'abord :
- registre : `sortieRetenueParUneSaisie(['vue'])` ignore une garde `panneau` ; `uneSaisieEstModifiee` ne pose aucune question ; les tests existants de `TaskForm` et `EventForm` (B-978, B-991, B-994) restent verts sans modification ;
- un test par ligne de la table du § 6.4, à 1440 px et sous le seuil selon la ligne. Au minimum : à 1440 px, « Nouvelle conversation », ouvrir le chat et « Vider » : aucune question, devis intact ; sous le seuil, « Nouvelle conversation » : question posée, « Continuer la saisie » rend le devis intact ; clic sur une pièce de la carte : question, devis intact ; pastille Board : question ; fermer le chat à 1440 px : question ; action rapide qui pose une vue dans le store : question, store revenu à `null`, devis intact ; tiroir sous le seuil : question posée avant tout changement de conversation (`currentConversationId` inchangé) ; tiroir à 1440 px : aucune question ; rétrécissement avec devis entamé : chat replié, panneau intact, aucune question ;
- une seule question par geste (motif B-994) ;
- garde de source : une écriture brute d'un des huit états ajoutée hors de `changerLePanneau` rougit (sabotage : en ajouter une dans `onOpenInvoice`).
Critère observable : dans l'app, à 1440 px, un devis entamé puis « Nouvelle conversation » ne pose aucune question et le devis reste à côté du chat ; sous 1280 px, le même geste pose « Abandonner les modifications ? ».

**Lot 6. Ménage et garde anti-retour.** Inchangé depuis la V2 (suppression du code mort du panneau, garde contre une seconde liste de taux, un second calcul de totaux ou un alias d'arrondi, recette du parcours de Claire, PDF aux montants de l'écran), plus : la mention de l'écran relevée sur chaque PDF de la recette.

## 8. Plan de tests, en résumé

- **Unitaires** : `saisieDePiece.test.ts` (lot 2), table partagée `mentionsDeTva.cas.json` (lots 1 et 2), `lib/saisieEnCours` (lot 5).
- **Composants** : les tests de la modale (73 à `900765fb`, 75 avec B-1492) et les 29 du panneau, plus ceux des lots 0 à 5.
- **Moteur** : `tests/test_p121_statut_attendu.py` (dont la concurrence), `mention_de_tva`, le régime dans `/billing/profile-status` (lot 1) ; `tests/test_f1_coherence_des_couches.py` étendu (lot 0) ; les tests de facturation existants inchangés et verts.
- **Coque** : la table des sorties (lot 5), la caractérisation de fermer le chat (lot 0), la garde de source (lot 5).
- **Recette navigateur** : lots 3, 5 et 6.

## 9. À reproduire : défauts qui existent sans aucune RFC

- **R-121-1. La modale ignore `tva_applicable` dans ses totaux.** Preuve : `InvoiceForm.tsx:335-340` applique le taux de la ligne sans regarder la pièce, alors que le moteur rend TTC = HT quand `tva_applicable` est faux (`routers/invoices.py:215-217`), que la pièce lue porte le champ (`routers/invoices.py:273`, `services/api/invoices.ts:28`) et que de telles pièces existent (création par l'API, `models/schemas.py:1317` ; migration `models/database.py:219-234`). Reproduction proposée : créer par l'API un devis `tva_applicable: false` à une ligne de 100 € à 20 %, l'ouvrir dans Devis et factures : la modale annonce 120,00 € TTC, la liste et le PDF 100,00 €. Corrigé par construction au lot 2 ; à ficher et reproduire avant, pour qu'il ne dépende pas de ce chantier.
- **R-121-2. Fermer le chat referme aussi le panneau ouvert à côté** (1280 px et plus), et jette un devis entamé sans question. Preuve : § 0, constat 2. À reproduire, puis à décider : si c'est un défaut (le panneau devrait rester, comme à l'ouverture du chat, entrée 9), le correctif retire une ligne de la table du § 6.4.
- **Constat 3, pour mémoire.** Cliquer une pièce de la carte jette déjà un devis entamé aujourd'hui, comme la croix du panneau : le panneau n'a aucune question d'abandon (V2 § 3.3, « absente »). Ce n'est pas une fiche de plus, c'est l'objet du lot 5.
- **Constats 1 et 7** : fichés et fermés pendant la rédaction, B-1493 (`feac6303`) et B-1492 (`b39ac7d8`) (§ 3). Les cinq `required` restants relèvent de V3-1, pas d'une fiche : une pièce existante a toujours ses dates et ses nombres, et le client manquant est déjà refusé par la garde applicative (`InvoiceForm.tsx:363-367`) ; aucun ne bloque donc seul une pièce existante.

## 10. Risques et régressions à protéger

- **Deux gardes de présentation contradictoires** (`ligneDevis.b1355`, `colonnesDesLignes`) : une seule survit, réécrite au lot 3.
- **Identifiants et noms accessibles** (B-234, B-578, lot 5 de la DA) : une table par hôte ; les tests `identifiants`, `nomsAccessibles`, `boutonsNommes` et `da` restent verts.
- **B-011** : pas de second `<form>` ; `noValidate` n'enlève rien au rattachement du bouton.
- **`noValidate`** : aucune garde native ne rattrape plus un oubli de `validerPiece` ; chaque règle a son test, et chaque ancien `required` a un cas vide dans `saisieDePiece.test.ts`.
- **Registre à surfaces** : un appelant qui oublierait de déclarer `panneau` laisserait perdre un devis ; la garde de source et la table couvrent les écritures d'aujourd'hui, pas un nouvel hôte (P-075) qui devra déclarer la sienne.
- **Effet de navigation** : étendre le retour B-994 au panneau touche un effet que BUG-139 et B-816 ont déjà rendu délicat ; les tests `ConversationCanvasPrototype.parite` et ceux de B-994 restent verts.
- **Table de mentions** : si le texte du PDF change, les deux suites rougissent ensemble ; c'est voulu.
- **Précondition** : seul `usePrototypeInvoiceData` l'envoie, un test l'énumère.
- **Largeur** : jsdom ne voit ni débordement ni troncature ; seule la recette prouve B-1355, B-1387 et claire-28.

## 11. Questions pour l'humain

Aucune. Ce chantier n'efface aucune donnée chez les utilisatrices, n'annonce rien publiquement et ne touche pas à la marque. Les choix ouverts sont tranchés au § 5, chacun avec son motif, et R-121-2 relève d'un arbitrage de conception que la règle de délégation couvre.

## Annexe : appuis dans le code (à `feac6303`)

- Modale : `src/frontend/src/components/invoices/InvoiceForm.tsx` : totaux `:331-358` (lignes `:335-340`), envoi `:360-492`, statut envoyé (B-1492) `:438-441`, mise à jour `:452-455`, date de paiement `:494-527`, dialogue `:618-632`, formulaire `:641-646`, `required` `:710`, `:761`, `:771`, `:870`, `:882`, garde de validité (B-1493) `:374-382`, validité `:792-801`, date de paiement hors formulaire `:979-991`, bouton `:1032` ; test `InvoiceForm.test.tsx:85-113`.
- Panneau : `src/frontend/src/components/prototype/InvoiceConversationCard.tsx` : états `:338-349`, enregistrement `:440-462`, états affichés `:643-651`, hôte `:718-744`.
- Données du panneau : `src/frontend/src/components/prototype/usePrototypeInvoiceData.ts:36-72`, `:76-105`, `:157-164`.
- Coque : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx` : garde `:1076-1091`, `openChat` `:1195-1216`, `startConversation` `:1217-1224`, `openEmbeddedView` `:1225-1240`, effet de navigation `:1280-1326`, réouverture B-1386 `:1366-1378`, « Travaux » `:1410-1429`, `fermerLeChat` `:1514-1525`, `collapseScenarioPanel` `:1534-1537`, rétrécissement `:1587-1589`, Échap `:1614-1617`, accueil `:1636-1650`, `chooseScenario` `:1652-1676`, `chooseCapability` `:1678-1715`, `ouvrirDestination` `:1761-1777`, `submitComposer` `:1779-1789`, actions `:1866-1881`, croix du chat `:2065-2068`, pastilles `:2083-2084`, carte `:2219-2233`, ternaire latéral `:2470-2515`.
- Navigation : `src/frontend/src/stores/navigationStore.ts:91-116`. Tiroir : `src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx:258-285`. Vue embarquée : `src/frontend/src/components/prototype/PrototypeUnifiedViewCanvas.tsx:94`.
- Registre : `src/frontend/src/lib/saisieEnCours.ts:12-36` ; `src/frontend/src/hooks/useAbandonDeSaisie.ts:60-83`.
- Moteur : `src/backend/app/routers/invoices.py` : arrondi `:186-233`, réponse `:267-280`, création `:460-470`, mise à jour `:575-600`, profil `:819-845` ; `src/backend/app/models/schemas.py:1240-1248`, `:1312-1340` ; `src/backend/app/models/database.py:219-234` ; `src/backend/app/services/invoice_pdf.py:653-689`.
- Lectures seules du statut : `src/backend/app/services/workspace_tools.py:762`, `src/backend/app/services/notification_service.py:125`, `src/backend/app/services/action_agents.py:465` ; MCP `src/backend/app/services/mcp_therese_server.py:268-269`.
