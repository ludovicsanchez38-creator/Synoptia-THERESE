# RFC P-121 (V2) : un seul formulaire de devis, pour la création et la modification

Rédigé le 26/09/2026 sur `main` à `900765fb`. Remplace la V1 du 25/09 (`docs/plans/2026-09-25-rfc-p121-un-formulaire-de-devis.md`), jugée NO-GO par la revue adverse B (`docs/plans/revues/2026-09-25-revue-rfc-p109-p125.md`, section P-121). Proposition acceptée par Ludo le 25/09 sous une contrainte explicite : **aucune perte de fonctionnalité**. Les décisions 26 à 29 du 25/09 (`docs/plans/2026-09-25-questions-rfc-pour-ludo.md`, section « Décisions du 25/09/2026 ») sont posées ici comme des faits. Aucun code avant la validation de ce document.

Chemins relatifs à `src/frontend/src/` (écran) et `src/backend/app/` (moteur), sauf mention. Toutes les lignes citées ont été relues à `900765fb`.

## 0. Ce qui change depuis la V1

- L'inventaire est refait à HEAD. Quatre défauts qui fondaient la V1 sont corrigés, chacun dans un seul hôte ou dans les deux : B-1411, B-1412, B-1413 et B-1428 (§ 3.1). La question 1 de la V1 est donc tranchée par le code, et le lot 4 de la V1 était à moitié fait.
- Les décisions 26 à 29 sont intégrées (§ 2). Deux d'entre elles demandent un changement du moteur, que la V1 excluait : une précondition de statut sur la mise à jour (décision 29) et le régime de TVA exposé au formulaire (décision 28).
- Les règles nouvelles (échéance, validité) ne s'appliquent qu'à la création ou au champ modifié (décision 27) : aucune pièce existante ne devient inenregistrable.
- Les questions 2 à 4 de la V1, et la quantité décimale laissée hors périmètre, sont tranchées ici avec leur motif.
- Le lot 1 (moteur et store) se livre seul et règle déjà le constat 5 de la revue.

## 1. Le constat

Claire, persona du cycle 13 (`docs/campagnes/2026-09-25-personas-c13/rapports/claire.md`, claire-31, étapes 5.2 et 5.8), crée son devis dans le panneau « Facturer » et le modifie dans la modale de « Devis et factures » : même objet, deux présentations, et surtout deux codes aux règles différentes. Depuis, chaque correctif de devis a dû être posé deux fois (B-1411 et B-017, B-1413 et la date civile du panneau), ou ne l'a été que d'un côté (§ 3.4). Tant qu'il y a deux formulaires, un correctif sur deux manque à l'un des deux.

## 2. Décisions tranchées

| Nº | Décision | Origine | Ce qu'elle impose ici |
|---|---|---|---|
| 26 | Arrondi commercial au demi-centime supérieur, en valeur absolue, identique au moteur et à l'écran | Ludo par délégation, 25/09 ; livré par B-1428 (`2a2a7cdc`) | Le module commun n'arrondit que par `lib/auCentime.ts:8-13` ; lot 0 ajoute un cas demi-centime qui traverse base, schéma, PDF et trésorerie |
| 27 | Échéance postérieure à l'émission et validité de 1 à 365 jours : vérifiées à la création, ou quand le champ est modifié | Ludo par délégation, 25/09 | `validerPiece` reçoit l'état chargé ; une pièce existante qui viole la règle reste enregistrable tant qu'on ne touche pas ce champ |
| 28 | Le libellé du taux 0 suit le régime déclaré au profil (P-119) | Ludo par délégation, 25/09 | `regime_tva` exposé par `/billing/profile-status` et gardé dans `useBillingProfileStore` |
| 29 | Un devis envoyé ou accepté ne se retouche pas depuis Facturer, refus côté serveur comme à l'écran | Ludo par délégation, 25/09 | Précondition `statut_attendu` sur `PUT /api/invoices/{id}` ; Facturer envoie toujours `draft` |
| V1-Q1 | Retoucher un devis que Facturer vient d'enregistrer met à jour ce devis | Livré par B-1412 (`152caa71`) | Conservé tel quel, complété par la décision 29 |
| V1-Q2 | La confirmation en deux temps (« Confirmer le brouillon ») reste propre à Facturer | Tranché ici | Motif : le panneau vit à côté d'une conversation qui peut préremplir le devis, la confirmation sur instantané figé protège de ce préremplissage ; dans la modale, la saisie est entièrement celle de l'utilisatrice, « Créer » suffit, et un clic de plus n'y protège de rien |
| V1-Q3 | Remplacée par la décision 28 | | |
| V1-Q4 | Facturer ne modifie pas un devis existant dans ce chantier | Tranché ici | Motif : la modification complète (statuts, paiement, conversion) ne tient pas dans 440 px (claire-28 débordait déjà), et P-075 (création en page, acceptée) décidera de l'hôte suivant ; le détail en lecture seule reste, avec « Ouvrir dans Devis et factures » |
| Q-quantité | Les deux formulaires acceptent une quantité décimale strictement positive (0,5), comme le moteur | Tranché ici | Motif : le moteur l'accepte et le documente (`models/schemas.py:1284-1286`, `:1293`, « une demi-journée de formation »), la pièce sort juste au PDF (`tests/test_f1_coherence_des_couches.py:220-240`) ; le refus à l'écran est une perte sans raison. Aucun test ne fige le refus (recherche de « égale à 1 » et « quantité doit » vide dans les tests des deux formulaires) |
| Q-serveur | Échéance et validité ne deviennent pas des règles du moteur | Tranché ici | Motif : le moteur reçoit aussi des pièces du serveur MCP (`services/mcp_therese_server.py:133`, `:269`) et de l'API ; les y refuser changerait ces chemins, qui ne sont pas le sujet de P-121 |

Aucune question ne reste ouverte (§ 10).

## 3. Ce qui existe à HEAD

### 3.1 Réglé depuis la V1, à ne pas reproposer

| Fiche | Ce qui est fait | Où |
|---|---|---|
| B-1411 | La modale arrondit chaque ligne au centime, puis somme des lignes arrondies | `components/invoices/InvoiceForm.tsx:331-358` ; test `InvoiceForm.totalAuCentime.b1411.test.tsx` |
| B-1412 | Après « Confirmer le brouillon », une retouche met à jour le même devis | `components/prototype/InvoiceConversationCard.tsx:341-344`, `:448-451` ; `components/prototype/usePrototypeInvoiceData.ts:74-95` ; tests `InvoiceConversationCard.retoucheSansDoublon.b1412.test.tsx`, `usePrototypeInvoiceData.test.tsx` |
| B-1413 | La modale prend la date civile locale | `InvoiceForm.tsx:151-163` (`localDateKey`) ; test `InvoiceForm.dateCivile.b1413.test.tsx` |
| B-1428 | Une seule règle d'arrondi, demi-centime vers le haut : moteur `_au_centime` (`routers/invoices.py:186-191`, `Decimal(repr(valeur))` et `ROUND_HALF_UP`), écran `auCentime` (`lib/auCentime.ts:8-13`) | Tests `tests/test_b1428_arrondi_commercial.py` (2,5 × 1,25 = 3,13 ; 1,005 = 1,01 ; avoir symétrique) et `lib/auCentime.test.ts` |
| B-1439 | La modale ne propose plus de statut à la création (le moteur crée toujours un brouillon) | `InvoiceForm.tsx:712-731` ; test `InvoiceForm.statutALaCreation.b1439.test.tsx` |
| B-1456 | Un décimal enregistré se relit avec la virgule | `InvoiceForm.tsx:93-96` ; test `InvoiceForm.virguleRelue.b1456.test.tsx` |
| P-136 | Avertissement non bloquant : facture avec TVA de plus de 150 € HT sans numéro de TVA de l'émetteur | `InvoiceForm.tsx:648-659` ; test `InvoiceForm.numeroDeTva.p136.test.tsx` |
| P-139 | Date du premier envoi gardée (`sent_at`), jamais réécrite | `routers/invoices.py:684-688`, appelée par la mise à jour (`:586-588`) ; migration `b8c9d0e1f2a3` |
| P-154 | Un avoir cite sa facture d'origine | `InvoiceForm.tsx:139-149`, `:430`, `:762-777` ; moteur `routers/invoices.py:590-592` ; test `InvoiceForm.factureDOrigine.p154.test.tsx` |
| P-155, P-138 | Date réelle du paiement, jamais future ; un brouillon payé se signale | `InvoiceForm.tsx:196`, `:481-514`, `:968-983` ; test `InvoiceForm.datePaiement.p155.test.tsx` |

La « troisième copie de l'arrondi » relevée par la revue a disparu avec B-1428 : il reste une seule fonction, `auCentime`, que chaque formulaire renomme localement (`InvoiceForm.tsx:46-47`, `arrondirAuCentime` ; `InvoiceConversationCard.tsx:130-135`, `arrondirCentimes`). La garde du lot 6 vise ces deux alias.

### 3.2 Deux formulaires, deux hôtes

| | Panneau « Facturer » | Modale de « Devis et factures » |
|---|---|---|
| Composant | `DevisDraftForm` (`InvoiceConversationCard.tsx:310-678`) | `InvoiceForm` (`InvoiceForm.tsx`, 1 071 lignes) |
| Hôte | `InvoiceWorkspaceCanvas` (`InvoiceConversationCard.tsx:685-744`), dans le panneau contextuel de la coque, non modal, de 440 à 620 px (`ConversationCanvasPrototype.tsx:350`), monté à `:388-400` | `InvoicesPanel.tsx:616-623`, modale `role="dialog"` de `max-w-4xl` (`InvoiceForm.tsx:605-618`) |
| Ouverture | « Nouveau devis » et « Préparer un devis » (`InvoiceConversationCard.tsx:181-184`, `:217`) posent `'new-devis'` (`ConversationCanvasPrototype.tsx:2228-2231`) | `handleCreateNew` et `handleEdit` (`InvoicesPanel.tsx:213-221`) |
| Données | `usePrototypeInvoiceData.ts` : création forcée en devis (`:96`), mise à jour B-1412 (`:77-86`), premier contact (`:107-124`) | appels directs à l'API (`InvoiceForm.tsx:13`) |
| Pièce existante | détail en lecture seule (`InvoiceConversationCard.tsx:253-308`, « Lecture seule ici » `:302-305`) | modification complète |

### 3.3 Inventaire des capacités et de leurs gardes

`P/` = `components/prototype/`, `I/` = `components/invoices/`. « Aucun » signale une capacité sans test.

**Périmètre**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Type de pièce | devis seul, forcé deux fois (`InvoiceConversationCard.tsx:386`, `usePrototypeInvoiceData.ts:96`) | devis, facture, avoir, choisis à la création seulement (`InvoiceForm.tsx:671-686`) ; type par défaut du filtre, B-388 (`:135-137`) | `I/InvoiceForm.typeParDefaut`, `I/InvoiceForm.da` |
| Modifier une pièce | non (décision V1-Q4) | oui (`InvoiceForm.tsx:439-442`) | `I/InvoiceForm.focusEtLibelles.c12`, `I/InvoiceForm.focusInitial` |
| Statut | toujours brouillon | en modification seulement (B-1439, `:712-731`) ; passage à payée, acceptée ou refusée confirmé (`:459-476`) | `I/InvoiceForm.test` (« ne permet pas de contourner la confirmation via le sélecteur de statut »), `I/InvoiceForm.statutALaCreation.b1439` |
| Payée avec sa date, accepter, refuser | non | `:481-542`, `:968-994` | `I/InvoiceForm.test`, `I/InvoiceForm.datePaiement.p155`, `I/InvoiceForm.da` |
| Convertir un devis en facture | non | `:544-573`, dialogue `:1028-1067` | `I/InvoiceForm.conversionDoubleClic.b1397`, `I/InvoiceForm.conversionAccents.b1358`, `I/InvoiceForm.echap` |
| Facture d'origine d'un avoir | non | `:139-149`, `:762-777` | `I/InvoiceForm.factureDOrigine.p154` |
| Conditions de paiement en lecture | non | `:920-945` | `I/InvoiceForm.conditionsAccentuees.b1450` |
| Avertissement numéro de TVA (P-136) | non (Facturer ne fait que des devis) | `:648-659` | `I/InvoiceForm.numeroDeTva.p136` |

**Client**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Client déjà à l'écran présélectionné | `contactInitial` (`InvoiceConversationCard.tsx:326`) | non | `P/DevisHeriteLeClient` |
| Premier client créé sans quitter, avec téléphone et adresse | `:465-538` | non | `P/InvoiceConversationCard.test` |
| Carnet illisible distingué d'un carnet vide | `:496-548` | **non** : l'erreur est avalée (`InvoiceForm.tsx:272-274`), le sélecteur paraît vide | `P/InvoiceConversationCard.contactsIndisponibles` ; **aucun** côté modale |
| Client hors des 200 récents (B-568) | non | `:264-271` | `I/InvoiceForm.clientHorsFenetre` |
| Liste tronquée annoncée | `:579-583` | `:704-709` | `P/InvoiceConversationCard.brouillonEnregistre`, `I/InvoiceForm.test` |

**Saisie et montants**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Date du jour | civile, par un calcul maison (`InvoiceConversationCard.tsx:117-128`) | civile, `localDateKey` (`InvoiceForm.tsx:151-163`) | `I/InvoiceForm.dateCivile.b1413` ; **aucun** côté panneau |
| Validité | texte libre, refusé sous 1 (`:412-413`) | nombre de 1 à 365, valeur invalide **remplacée en silence par 30** (`InvoiceForm.tsx:787`) | **aucun** |
| Devises | cinq codes nus (`:592-594`) | cinq codes avec symbole (`:57-63`) | `I/InvoiceForm.devisesEtDecimales` |
| Taux de TVA | nus, « 20% » à « 0% » (`:627-629`) | nommés, dont « 0% (exonéré) » (`:49-55`) | `I/InvoiceForm.devisesEtDecimales`, `I/InvoiceForm.francais` |
| Saisie des montants | `parseDecimal` : virgule acceptée, « 1 000,50 € » refusé (`:137-141`) | frappe invalide refusée avec sélection rendue (B-1393, `:296-323`), collage « 1 000,50 € » nettoyé (B-1400, `:102-108`) | `I/InvoiceForm.saisieDesMontants.b1393`, `I/InvoiceForm.devisesEtDecimales` |
| Quantité | refusée sous 1 (`:406-407`) | refusée sous 1 (`:408-411`) | **aucun** (voir Q-quantité) |
| Totaux au centime | `auCentime` (`:351-370`) | `auCentime` (`:335-358`) | `P/InvoiceConversationCard.montantConfirme`, `I/InvoiceForm.totalAuCentime.b1411` |
| Total HT par ligne | non | `:883-885` | **aucun** |
| Disposition des lignes | grille, en-tête visuel masqué sous `sm` (B-1355, `:614-632`) | tableau fixe, colonnes en rem (B-1387, `:799-901`) | `P/InvoiceConversationCard.ligneDevis.b1355` et `I/InvoiceForm.colonnesDesLignes` : deux gardes de présentation contradictoires |

**Validation et enregistrement**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Règles | client, une ligne, description, quantité ≥ 1, prix ≥ 0, émission, échéance ≥ émission, validité ≥ 1 (`:401-415`) | client, une ligne, description par ligne (BUG-132), nombres valides, quantité ≥ 1, prix ≥ 0 (`:363-411`) ; **ni échéance ni validité** | `P/InvoiceConversationCard.test`, `I/InvoiceForm.test`, `I/InvoiceForm.da`, `I/InvoiceForm.soumission` |
| Champ fautif relié | pour chaque règle, `aria-invalid` et `aria-describedby` (`:575`, `:586-597`, `:624-626`) | description seulement (`:837-848`), les autres règles écrivent au pied (`:957-965`) | `I/InvoiceForm.focusEtLibelles.c12`, `P/InvoiceConversationCard.test` |
| Cause renvoyée par le serveur (D203) | dans le panneau (`:456-458`, `:681-683`) | notification seulement (`InvoiceForm.tsx:450-453`) | `P/InvoiceConversationCard.cycle6` |
| Confirmation avant création | instantané figé, champs verrouillés, revalidation (`:417-463`, `:566-571`, `:653-670`) | création directe | `P/InvoiceConversationCard.test` |
| Un seul envoi par geste | `savingRef` (`:434-446`) | bouton rattaché au formulaire (B-011, `InvoiceForm.tsx:633`, `:1021`) | `P/InvoiceConversationCard.test`, `I/InvoiceForm.soumission` |
| Après l'enregistrement | le panneau reste ouvert, succès puis avertissement à la retouche (B-575, B-377, `:645-651`) | la modale se ferme, notification (`:442-449`) | `P/InvoiceConversationCard.brouillonEnregistre`, `I/InvoiceForm.focusEtLibelles.c12` |
| Retouche d'un brouillon enregistré | mise à jour du même devis (B-1412), **sans relire son statut** : un devis passé à « Envoyé » dans Devis et factures verrait ses lignes réécrites | sans objet | `P/InvoiceConversationCard.retoucheSansDoublon.b1412` |

**Profil émetteur, abandon, clavier**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Profil incomplet ou illisible | instantané lu au chargement (`usePrototypeInvoiceData.ts:45-55`, bandeaux `InvoiceConversationCard.tsx:553-564`), périmé après un passage aux Réglages | store partagé rafraîchi (`InvoiceForm.tsx:128-134`), bandeau « illisible » (`:661-669`) | `I/InvoiceForm.test`, `I/InvoiceForm.profilIllisible` |
| « Abandonner les modifications ? » (B-1392) | **absente** | `useQuestionDAbandonDeModale` (`:217-226`, `:1010-1016`) | `I/InvoiceForm.abandonDeSaisie.b1392` |
| Inscription dans `lib/saisieEnCours.ts` | **non** | **non** : le hook de la modale ne s'y inscrit pas (`hooks/useQuestionDAbandonDeModale.ts:18-75`) ; seuls `TaskForm` et `EventForm` le font, par `hooks/useAbandonDeSaisie.ts:73-83` | aucun |
| Focus, Échap, piège | panneau non modal (règle de la 0.48.1) | piège (`:206-207`), pile d'Échap (`:230-233`), focus initial (B-1370, `:681`, `:694`) | `I/InvoiceForm.focusInitial`, `I/InvoiceForm.echap` |
| Noms accessibles et identifiants | « Client du devis » (`:575`), « Échéance du devis » (`:589`), `devis-*` | `contact`, `issueDate`, `invoiceform-*` | `I/InvoiceForm.nomsAccessibles`, `I/InvoiceForm.identifiants`, `I/InvoiceForm.boutonsNommes`, `I/InvoiceForm.francais` |

Sorties qui démontent le panneau sans rien demander : la croix et `onClose` (`ConversationCanvasPrototype.tsx:2512-2514`) mènent à `collapseScenarioPanel` (`:1535-1538`), qui ne consulte pas `sortieRetenueParUneSaisie` ; `openChat` referme le panneau sous le seuil côte à côte (`:1207`) ; un effet le referme quand la fenêtre rétrécit avec le chat ouvert (`:1587-1589`). Les sorties de vue, elles, consultent déjà le registre (`:1082`, `:1293`, `:1500-1502`).

### 3.4 Ce que l'inventaire révèle encore

- **Au panneau seul** : le champ fautif relié pour chaque règle, la cause du serveur à l'écran, les règles d'échéance et de validité, le carnet illisible distingué.
- **À la modale seule** : la question d'abandon, la saisie décimale soignée (B-1393, B-1400), le client hors fenêtre, le profil rafraîchi et son bandeau « illisible », le total HT par ligne, les colonnes en rem.
- **Aux deux, à tort** : le refus d'une quantité décimale que le moteur accepte ; le libellé « 0% (exonéré) » (modale) ou « 0% » (panneau) quel que soit le régime, alors que P-119 (`7d1cbfc8`) fait déclarer au profil l'assujettissement, la franchise ou l'exonération formation (`services/user_profile.py:42-45`) et que le PDF en tire sa mention (`services/invoice_pdf.py:682-685`).
- **Aucun** des deux n'est inscrit dans le registre des saisies en cours.

### 3.5 Tests existants (comptés par `npx vitest list` à `900765fb`)

- `I/InvoiceForm.*` : 27 fichiers, 73 tests.
- `P/InvoiceConversationCard.*` : 8 fichiers, 23 tests ; `P/DevisHeriteLeClient` : 3 ; `P/usePrototypeInvoiceData` : 3.
- Les fichiers `I/InvoicesPanel.*` simulent la modale (`vi.mock('./InvoiceForm')`, par exemple `InvoicesPanel.conversion.c12.test.tsx:22`, `InvoicesPanel.creationSousFiltre.test.tsx:26`) : ils protègent le contrat d'hôte (`invoice`, `defaultDocumentType`, `onClose`, `onSave`), qui ne change pas. La V1 disait à tort qu'ils passaient par la modale.
- Moteur : `tests/test_b1428_arrondi_commercial.py`, `tests/test_f1_coherence_des_couches.py` (33,33 × 3 et 0,5 × 33,33 à travers base, schéma, PDF et trésorerie ; aucun cas de demi-centime exact), `tests/test_routers_invoices.py`, `tests/test_p139_date_d_envoi.py`, `tests/test_p154_avoir_et_sa_facture.py`, `tests/test_p155_date_de_paiement.py`.

### 3.6 Décisions antérieures à respecter

- Lot 5 de la DA, décision 3 (`docs/plans/2026-09-11-da-lot5-devis-design.md:39`) : le formulaire de Devis et factures reste une modale. P-075 (création en page, acceptée, non livrée) deviendrait un troisième hôte du corps commun ; P-121 le prépare sans le trancher.
- Règle de la 0.48.1 : le panneau côte à côte n'a ni piège de focus ni `aria-modal`.
- P-074 (convertir depuis la ligne de la liste), acceptée, non livrée : hors périmètre.

## 4. Options et recommandation

Les quatre options de la V1 restent les bonnes, et la revue ne les a pas contestées : A (un corps de saisie commun, deux hôtes qui gardent leur cycle de vie), B (la modale seule), C (le panneau seul), D (aligner l'apparence). B jette la promesse de Facturer (agir à côté de la conversation) ; C contredit la décision 3 du lot 5 ; D ne règle rien, et § 3.4 montre que la divergence revient au correctif suivant.

**Recommandation : A.** C'est la seule option où « aucune perte de fonctionnalité » se vérifie ligne par ligne : chaque ligne du § 3.3 devient un test, et chaque capacité « d'un seul côté » passe des deux côtés par construction, sauf celles qui tiennent au cycle de vie d'un hôte (§ 5.6).

## 5. Conception

### 5.1 Moteur : deux ajouts, aucune migration

**Précondition de statut (décision 29).** `UpdateInvoiceRequest` (`models/schemas.py:1328-1340`) gagne `statut_attendu: str | None = None`. Dans `update_invoice` (`routers/invoices.py:530-652`), quand le champ est fourni, la requête commence par une écriture conditionnelle, **avant** la lecture actuelle de la pièce et de ses lignes (`_get_invoice_with_lines`, `:541`) : `UPDATE invoices SET updated_at = :maintenant WHERE id = :id AND status = :statut_attendu`. L'ordre compte : c'est cette écriture qui prend le verrou, la relecture vient ensuite. Aucune ligne touchée : une relecture distingue l'absence (404, comme `:543-544`) du statut changé (409, détail en français qui nomme le statut réel, par exemple « Ce devis est passé à « Envoyé » dans Devis et factures : il ne se retouche plus ici. »). Pourquoi une écriture plutôt qu'une lecture : avec SQLite, la transaction qui a écrit tient le verrou d'écriture jusqu'à son commit, donc aucun changement de statut ne peut s'intercaler entre la garde et la réécriture des lignes (`:601-640`). Sans `statut_attendu`, la route se comporte exactement comme aujourd'hui : la modale, qui l'appelle pour toute pièce et tout statut (`InvoiceForm.tsx:439-442`), ne perd rien.

**Régime de TVA exposé (décision 28).** `/billing/profile-status` (`routers/invoices.py:819-845`) renvoie aussi `regime_tva` (`normal`, `franchise` ou `exoneration_formation`, `models/schemas.py:793`), lu sur le profil déjà chargé (`:826-832`) ; sans profil, `normal`. `useBillingProfileStore` (`stores/billingProfileStore.ts:30-75`) le garde à côté de `missing` et de `tvaIntraRenseigne`.

Aucune colonne ne change : le régime vit dans le profil JSON (`services/user_profile.py:42-45`), la précondition n'est pas stockée. La tête Alembic reste `b8c9d0e1f2a3` (`models/database.py:619`).

### 5.2 Le module pur `components/invoices/saisieDePiece.ts`

- `tauxDeTva(regime)` : une seule liste, libellés de la modale (`InvoiceForm.tsx:49-55`) pour 20, 10, 5,5 et 2,1 %. Le taux 0 se nomme selon le régime : « 0% » en régime normal (une ligne à 0 % d'un assujetti peut être un export ou une autoliquidation : la dire « exonérée » affirmerait ce qu'on ne sait pas), « 0% (franchise, art. 293 B) » et « 0% (exonération formation) ». La mention légale complète, celle que le PDF imprime (`services/invoice_pdf.py:683`, `:685`), s'écrit une fois sous les totaux dès qu'une ligne est à 0 % hors régime normal : le sélecteur reste lisible à 125 %, là où Claire voyait « 0% (exonéré… » tronqué.
- `ligneVide(regime)` : taux par défaut 20 % en régime normal, 0 % en franchise et en exonération formation. Motif : Claire, en franchise, devait changer le taux de chaque ligne ; les autres taux restent proposés, sans blocage.
- `DEVISES` : la liste de la modale (`InvoiceForm.tsx:57-63`).
- `totauxDePiece(lignes)` : arrondi de chaque ligne par `auCentime`, somme des lignes arrondies, TVA déduite du TTC et du HT, miroir de `_montants_de_ligne` et `_calculate_invoice_totals` (`routers/invoices.py:194-233`). Les formulaires n'envoient pas `tva_applicable` (défaut `True`, `models/schemas.py:1317`) : le cas `tva_applicable=False` du moteur (`:216-217`) n'a pas de miroir, et n'en a pas besoin tant qu'aucun formulaire ne le pose (§ 5.8).
- `analyserMontant(texte)` : nettoyage B-1400 (espaces, insécables, symbole euro), virgule ou point, refus du signe moins ; rend un nombre ou `null`.
- `validerPiece(saisie, reference)` : `reference` est la pièce chargée, `null` à la création. Rend la première erreur (message et champ) et la liste des lignes sans description. Règles, dans l'ordre : client ; au moins une ligne ; description de chaque ligne (règle BUG-132, erreur par ligne) ; nombres valides ; quantité strictement positive ; prix positif ou nul ; date d'émission ; échéance postérieure ou égale à l'émission **si `reference` est nulle, ou si l'émission ou l'échéance diffère de `reference`** ; pour un devis, validité entière de 1 à 365 **aux mêmes conditions** (décision 27).
- `requeteDePiece(saisie)` et `dateDuJour()` (par `localDateKey`, `lib/civilDate.ts:10`, qui remplace le calcul maison du panneau).

### 5.3 Les composants

- `useSaisieDePiece(initiale)` : l'état, les montants en texte, le drapeau « modifiée » (consommé par la question d'abandon et par l'avertissement B-377).
- `LignesDePiece` : lignes, en-tête, total HT par ligne, « Ajouter une ligne », « Supprimer la ligne n ».
- `CorpsDePiece` : client, dates, devise, validité, notes, lignes, totaux, mention du régime ; type et statut seulement quand l'hôte les demande. Le texte d'erreur et son rattachement au champ sont communs ; l'endroit où il s'affiche appartient à l'hôte (pied de la modale, bas du panneau).
- Chaque hôte garde **ses identifiants** par une table passée au corps (`devis-*` pour le panneau ; `contact`, `issueDate`, `invoiceform-*` pour la modale) : les tests et le lot 5 de la DA qui les citent restent valides, et deux hôtes montés ensemble n'ont aucun identifiant commun.
- Le corps ne crée pas de second `<form>` : la modale garde son bouton hors du bloc défilant, rattaché par `form="invoice-form"` (B-011, `InvoiceForm.tsx:628-633`, `:1021`).

### 5.4 Une présentation

- Libellés visibles au-dessus de chaque champ, ceux de la modale (validés au lot 5). Les noms accessibles du panneau (« Client du devis », « Échéance du devis ») deviennent ceux du corps commun.
- Une même ligne, deux dispositions selon la place réelle : tableau étiqueté (B-1387) quand il tient, lignes empilées sinon (description sur toute la largeur, puis Quantité, Prix HT, TVA et Total HT étiquetés, puis « Supprimer »). Le choix se fait par requête de conteneur (`@container` de Tailwind 4, `tailwindcss` en `^4.0.0` dans `src/frontend/package.json:63`), pas par la largeur de la fenêtre, puisqu'à écran égal le panneau et la modale n'ont pas la même largeur. Ce serait la première requête de conteneur du dépôt (aucune occurrence de `@container` sous `src/frontend/src`).

### 5.5 Les règles, résumé

Union des deux jeux (§ 5.2), décision 27 pour les règles nouvelles, champ fautif focalisé et relié pour chaque règle, arrondi `auCentime` partout, date civile partout, profil par le store partagé des deux côtés (bandeau « illisible » compris), cause du serveur affichée des deux côtés (au pied de la modale en plus de la notification).

### 5.6 Ce que chaque hôte garde, ce qu'il gagne

**Panneau Facturer.** Garde : devis seulement, sans statut ; client hérité (entrée 2) ; création du premier client ; carnet illisible ; confirmation sur instantané figé ; il reste ouvert après l'enregistrement (B-575, B-377) ; mise à jour du même brouillon (B-1412). Gagne :

- `statut_attendu: 'draft'` à chaque mise à jour (`usePrototypeInvoiceData.ts:77-86`). Sur un 409, le panneau dit que le devis a changé de statut dans Devis et factures, garde la saisie intacte, oublie le brouillon enregistré (`brouillonEnregistre` à `null`) et propose « Créer un nouveau devis avec cette saisie » : rien ne part sans ce clic. Un 404 (brouillon supprimé entre-temps) suit le même chemin.
- la question d'abandon et son inscription dans `lib/saisieEnCours.ts` ; la croix et `collapseScenarioPanel` la consultent ; `openChat` sous le seuil aussi, puisqu'il passe par `blockStreamingNavigation` (`ConversationCanvasPrototype.tsx:1196`, `:1082`) ;
- l'effet de rétrécissement (`:1587-1589`), qui n'est pas un geste et ne peut pas poser de question : quand une saisie est retenue, il replie le chat plutôt que le panneau. Motif : le brouillon du composeur est déjà écrit sous la clé de sa conversation au démontage (B-1377, `hooks/useAutosave.ts:155-177`), le devis entamé ne l'est nulle part ;
- saisie décimale soignée, total HT par ligne, libellés et taux nommés, profil rafraîchi.

**Modale.** Garde : type à la création, statut en modification, confirmations sensibles ; payée avec sa date, accepter, refuser ; conversion et son dialogue ; facture d'origine ; avertissement du numéro de TVA ; conditions de paiement en lecture ; client hors fenêtre ; piège de focus, pile d'Échap, B-011 ; fermeture et notification après l'enregistrement. Gagne : échéance et validité vérifiées (décision 27), fin du remplacement silencieux par 30, quantité décimale, champ fautif relié pour chaque règle, cause du serveur au pied, carnet illisible distingué, inscription dans `saisieEnCours`.

### 5.7 Ce que l'utilisatrice verra changer

- Le même formulaire, les mêmes libellés, dans Facturer et dans Devis et factures.
- **Changements volontaires de comportement**, chacun couvert par un test qui le dit :
  - une quantité de 0,5 est acceptée des deux côtés ;
  - le taux 0 ne se dit plus « exonéré » en régime normal ; en franchise et en exonération formation, il porte son régime, la mention légale s'écrit sous les totaux, et une ligne nouvelle part à 0 % ;
  - dans la modale, une validité invalide est signalée au lieu d'être remplacée par 30, et une échéance antérieure à l'émission est refusée à la création ou quand l'une des deux dates change ;
  - dans Facturer, la retouche d'un devis passé à « Envoyé » ou « Accepté » est refusée avec son motif, et la saisie reste.
- Facturer : lignes étiquetées, total HT par ligne, question avant de perdre un devis entamé.

### 5.8 Hors périmètre, nommé

- **Immutabilité d'une facture émise.** La modale réécrit aujourd'hui les lignes d'une facture envoyée ou payée (`InvoiceForm.tsx:439-442`, moteur `routers/invoices.py:601-640`). C'est un vrai sujet légal (une facture émise se corrige par un avoir), mais ni P-121 ni les 36 décisions ne le portent. La décision 29 vise Facturer, et l'étendre ici retirerait une capacité à la modale, contre la contrainte de Ludo. C'est une frontière de ce chantier, pas un risque de celui-ci.
- `tva_applicable`, jamais envoyé par les formulaires (`models/schemas.py:1317` ; `InvoiceForm.tsx:420-431` ; `InvoiceConversationCard.tsx:383-399`), alors que le PDF s'en sert (`services/invoice_pdf.py:682`).
- P-075 (création en page), P-074 (convertir depuis la liste), la modification d'un devis existant depuis Facturer (décision V1-Q4).
- Échéance et validité comme règles du moteur (décision Q-serveur).

## 6. Réponse à la revue

| Nº | Gravité | Constat de la revue | Réponse | Où |
|---|---|---|---|---|
| 1 | P2 | Inventaire périmé : B-1411, B-1412, B-1413 corrigés après la RFC, question 1 déjà tranchée, gardes « rouges » devenues vertes, lot 4 à moitié fait, comptes de tests faux, troisième copie de l'arrondi | Inventaire refait à `900765fb` ; les trois fiches sont `fixed` dans `.app-loop/bugs.json` et citées avec leur code ; question 1 retirée (décision V1-Q1) ; gardes de totaux déplacées en caractérisation verte (lot 0) ; lot « panneau » réduit à ce qui manque ; comptes relevés par `vitest list` (27 fichiers et 73 tests côté modale, 8 et 23 côté panneau) ; la troisième copie a disparu avec B-1428, il reste deux alias d'une même fonction, visés par la garde du lot 6 | § 0, § 3.1, § 3.5, lots 0, 5, 6 |
| 2 | P2 | `totauxDePiece` n'était pas le miroir du moteur aux demi-centimes (`round` de Python contre `Math.round`) | Décision 26, livrée par B-1428 : une seule règle des deux côtés (`routers/invoices.py:186-191`, `lib/auCentime.ts:8-13`), tests unitaires en place ; le module commun n'a pas d'autre arrondi ; le lot 0 fait traverser 2,5 × 1,25 € et 1,005 € par base, schéma, PDF et outil de trésorerie, et `saisieDePiece.test.ts` reprend ces cas | § 2, § 5.2, lots 0 et 2 |
| 3 | P2 | L'union des règles rendait inenregistrables des pièces existantes (échéance antérieure créée par l'API ou le MCP), statut compris | Décision 27 : `validerPiece` reçoit la pièce chargée et n'applique échéance et validité qu'à la création ou au champ modifié ; validité réservée aux devis ; caractérisation au lot 0 : « facture existante à échéance antérieure : on la marque payée, on change son statut et ses notes » | § 5.2, lots 0 et 2 |
| 4 | P3 | « 0% (exonéré) » partout ignore P-119 ; faux pour une franchise | Décision 28 : régime exposé par le moteur et gardé par le store, libellé du taux 0 dérivé du régime, mention légale sous les totaux, taux par défaut selon le régime | § 5.1, § 5.2, lots 1 et 2 |
| 5 | P3 | La mise à jour après confirmation ne regardait pas le statut courant : un devis envoyé ou accepté verrait ses lignes réécrites | Décision 29 : précondition `statut_attendu` vérifiée par une écriture conditionnelle, qui tient le verrou d'écriture jusqu'au commit (plus sûr qu'une relecture côté écran, que la revue demandait) ; 409 au panneau, saisie gardée, nouveau devis proposé ; la modale inchangée | § 5.1, § 5.6, lot 1 |
| 6 | P3 | Références décalées dès le commit de la RFC | Toutes les références relues à `900765fb` ; la liste des sorties du panneau est donnée par fonction, et le lot 5 teste chaque sortie plutôt qu'une liste de lignes | § 3, annexe, lot 5 |

Les quatre questions que la revue adressait à Ludo sont les décisions 26 à 29.

## 7. Livraison en lots TDD

Chaque lot : tests écrits d'abord et vus rouges pour la bonne raison (sauf les caractérisations du lot 0, vertes par définition) ; un commit par lot ; sabotage ciblé par fonction, jamais par chaîne globale (règle du 27/08) ; les six portes du dépôt ; revue adverse du diff ; recette navigateur sur la pile jetable (17393 et 1420, jamais 17293) quand le lot touche l'affichage. Chaque lot se livre seul.

**Lot 0. Caractérisation (écran et moteur, aucun code applicatif).**
Tests, verts à HEAD, qui doivent le rester jusqu'au lot 6 :
- moteur, dans `tests/test_f1_coherence_des_couches.py` : une facture de 2,5 × 1,25 € et une de 1 × 1,005 € ; base, schéma, PDF et outil de trésorerie disent 3,13 € et 1,01 € HT ;
- modale : une facture existante dont l'échéance précède l'émission se marque payée, change de statut et de notes, et s'enregistre ;
- modale : le total HT de chaque ligne s'affiche (aujourd'hui sans test) ;
- les deux hôtes : trois lignes de 33,33 € à 20 % annoncent 120,00 € TTC.
Critère observable : `pytest` et `vitest` verts, aucun fichier applicatif touché.

**Lot 1. Moteur et store (livrable seul, règle déjà le constat 5).**
Rouges d'abord :
- `tests/test_p121_statut_attendu.py` : `PUT` avec `statut_attendu='draft'` sur un devis `sent` rend 409 et laisse lignes et totaux intacts en base ; sur un brouillon, 200 ; sans le champ, 200 sur un devis `sent` (la modale ne perd rien) ; identifiant inconnu, 404 ;
- `/billing/profile-status` rend `regime_tva` pour les trois régimes, et `normal` sans profil ;
- `billingProfileStore` garde `regimeTva` ;
- `usePrototypeInvoiceData` envoie `statut_attendu: 'draft'` ;
- panneau : statut passé à `sent` entre deux confirmations, un seul `updateInvoice` refusé, message affiché, saisie intacte, aucun `createInvoice` sans clic, puis « Créer un nouveau devis avec cette saisie » crée une pièce.
Critère observable : dans l'app, un devis créé dans Facturer puis passé à « Envoyé » dans Devis et factures ne se retouche plus depuis Facturer, et la liste ne bouge pas.

**Lot 2. Module pur, branché dans la modale.**
Rouges d'abord : `saisieDePiece.test.ts` (totaux : 33,33 × 3, 2,5 × 1,25, 1,005, taux 0, 5,5 et 2,1 ; validation règle par règle, ordre et champ désigné, avec et sans pièce de référence, champ changé ou non ; quantité 0,5 acceptée, 0 et -2 refusées ; date du jour avec une horloge factice à 0 h 30 et 23 h 30, fuseau de Paris ; montants « 1 000,50 € », « 12,5 », « -2 », chaîne vide ; libellés des taux et taux par défaut pour les trois régimes). Dans la modale : validité 0 refusée avec message (et non remplacée par 30) ; échéance antérieure refusée à la création, acceptée sur une pièce existante dont on ne touche pas les dates ; chaque règle focalise et relie son champ ; cause du serveur au pied ; carnet illisible annoncé ; mention du régime sous les totaux.
Aucun test existant ne fige les trois comportements abandonnés : aucun n'affirme « 0% (exonéré) » (`InvoiceForm.francais.test.tsx:58-66` ne vérifie que l'absence de sa forme sans accents), `validite_jours: 30` n'apparaît que dans des données de test, jamais dans une assertion sur le remplacement, et aucun ne pose une quantité entre 0 et 1. `InvoiceForm.test.tsx:85-113` (quantité vide, puis « . », refusées avec « nombres valides ») reste vert sans modification : `analyserMontant('.')` rend `null`. Si la suite révèle un autre test figé, il est réécrit dans le même commit, intention conservée et dite.
Critère observable : les 73 tests `InvoiceForm.*` verts, plus les nouveaux ; dans l'app, une validité de 0 dans un devis affiche un message et rien ne part.

**Lot 3. `LignesDePiece` dans les deux hôtes.**
Rouges d'abord : une garde unique sur le composant commun (colonnes nommées, `min-w-0`, total HT par ligne, identifiants de chaque hôte) remplace `ligneDevis.b1355` et `colonnesDesLignes`, et le commit dit laquelle des deux intentions de présentation est réécrite. Recette navigateur obligatoire, jsdom ne mesurant aucune largeur : « 0% (franchise, art. 293 B) » lisible en entier et « Supprimer la ligne » dans le cadre du panneau, à 1280, 1024 et 800 px, à 100 % et 125 %, thèmes clair et sombre.
Critère observable : dans Facturer, chaque ligne montre ses étiquettes et son total HT ; aucune capture de la recette ne montre de texte tronqué ni de bouton hors cadre.

**Lot 4. `CorpsDePiece` et `useSaisieDePiece`, migration du panneau.**
Rouge d'abord : le test de parité monte les deux hôtes et compare libellés, options de TVA et de devises, message pour une même saisie fautive et totaux. La confirmation sur instantané, le premier client et le client hérité restent dans l'hôte ; profil par le store partagé ; les tests qui citent les anciens noms accessibles du panneau sont adaptés, assertions conservées.
Critère observable : le test de parité vert ; dans l'app, compléter le profil dans les Réglages pendant qu'un devis est ouvert dans Facturer fait disparaître le bandeau sans rouvrir le panneau.

**Lot 5. Abandon et sorties.**
Rouges d'abord, un test par sortie de chaque hôte, énumérées à partir des fonctions et non des lignes : panneau modifié puis croix, Échap, changement de parcours, choix d'une capacité, « Nouvelle conversation », `openChat` sous le seuil : la question est posée, rien n'est perdu ; panneau intact : il se ferme sans question ; rétrécissement de la fenêtre avec le chat ouvert et un devis entamé : le chat se replie, le panneau reste ; modale modifiée : inscrite dans `saisieEnCours`, et une sortie de vue la retient ; une seule question par geste (motif B-994).
Critère observable : dans l'app, un devis entamé dans Facturer puis « Nouvelle conversation » fait apparaître « Abandonner les modifications ? », et « Continuer la saisie » rend le devis intact.

**Lot 6. Ménage et garde anti-retour.**
Suppression du code mort du panneau (`parseDecimal`, `todayIso`, `dueDateIso`, les deux alias d'arrondi, lignes et validation propres). Garde qui échoue si une seconde liste de taux, un second calcul de totaux ou un alias d'arrondi réapparaît hors de `saisieDePiece.ts` et `lib/auCentime.ts`, sur le modèle de `lib/lexiqueTitres.test.ts`. Les `round(…, 2)` de l'outil de trésorerie (`services/workspace_tools.py:530-532`, `:570`) somment des montants déjà au centime et ne font que corriger le bruit binaire : une somme de montants à deux décimales ne tombe jamais sur un demi-centime, la règle 26 n'y est pas en jeu. La garde, côté écran, ne les vise pas. Recette finale : le parcours de Claire (étapes 5.1 à 5.10), PDF du devis et de la facture convertie aux montants de l'écran, captures avant et après.
Critère observable : la garde anti-retour rougit quand on réintroduit à la main une liste de taux dans `InvoiceConversationCard.tsx` (sabotage), et le parcours de Claire se déroule sans écart entre écran, liste et PDF.

## 8. Plan de tests, en résumé

- **Unitaires** : `saisieDePiece.test.ts` (lot 2) ; `lib/auCentime.test.ts` inchangé.
- **Composants** : les 73 tests de la modale et les 29 du panneau (23, plus `DevisHeriteLeClient` et `usePrototypeInvoiceData`), plus ceux des lots 0 à 5.
- **Moteur** : `tests/test_p121_statut_attendu.py` et le régime dans `/billing/profile-status` (lot 1) ; `tests/test_f1_coherence_des_couches.py` étendu (lot 0) ; `tests/test_b1428_arrondi_commercial.py`, `tests/test_routers_invoices.py`, `tests/test_p139_date_d_envoi.py`, `tests/test_p154_avoir_et_sa_facture.py` et `tests/test_p155_date_de_paiement.py` inchangés et verts.
- **Contrat d'hôte** : les `I/InvoicesPanel.*` inchangés et verts.
- **Recette navigateur** : lots 3 et 6.

## 9. Risques et régressions à protéger

- **Deux gardes de présentation contradictoires** (`ligneDevis.b1355`, `colonnesDesLignes`) : une seule survit, réécrite au lot 3, et le commit le dit.
- **Identifiants et noms accessibles** (B-234, B-578, lot 5 de la DA) : une table par hôte ; les tests `InvoiceForm.identifiants`, `nomsAccessibles`, `boutonsNommes` et `da` restent verts sans modification.
- **B-011** : pas de second `<form>` ; le bouton de la modale reste rattaché par `form=`.
- **Focus et Échap** : focus initial différent selon l'hôte (B-1370), ordre du dialogue de conversion (B-228), aucun piège dans le panneau.
- **Régime inconnu** (profil illisible) : les libellés retombent sur le régime normal, « 0% » nu ; aucune mention légale n'est affirmée sans lecture réussie.
- **Précondition** : un appelant qui l'enverrait par erreur recevrait un 409 inattendu ; seul `usePrototypeInvoiceData` l'envoie, et un test l'énumère.
- **Largeur** : jsdom ne voit ni débordement ni troncature ; seule la recette prouve B-1355, B-1387 et claire-28.
- **Sorties du panneau** : l'effet de rétrécissement change de comportement (il replie le chat quand un devis est entamé) ; le lot 5 le teste, et la recette le vérifie à 1279 puis 1281 px.

## 10. Questions pour l'humain

Aucune. Ce chantier n'efface aucune donnée chez les utilisatrices, n'annonce rien publiquement et ne touche pas à la marque. Les choix qui restaient ouverts sont tranchés au § 2, chacun avec son motif.

## Annexe : appuis dans le code (à `900765fb`)

- Modale : `src/frontend/src/components/invoices/InvoiceForm.tsx` : arrondi `:46-47`, listes `:49-88`, montants `:93-116`, profil `:128-134`, type par défaut `:135-137`, avoir `:139-149`, dates `:151-163`, validité `:166-168` et `:779-790` (remplacement par 30 `:787`), date du paiement `:196`, abandon `:217-226` et `:1010-1016`, contacts `:250-275`, saisie décimale `:296-323`, totaux `:331-358`, envoi `:360-479`, payée `:481-514`, accepter et refuser `:516-542`, conversion `:544-573` et `:1028-1067`, bandeaux `:634-669`, type `:671-686`, statut `:712-731`, lignes `:799-901`, conditions `:920-945`, pied `:957-1026`.
- Panneau : `src/frontend/src/components/prototype/InvoiceConversationCard.tsx` : instantané `:42-59`, dates `:117-128`, arrondi `:130-135`, montants `:137-141`, carte `:147-251`, détail `:253-308`, formulaire `:310-678` (totaux `:351-370`, requête `:383-399`, validation `:401-415`, confirmation `:417-463`, premier client `:465-548`, champs `:566-641`, états `:643-674`), cause du serveur `:681-683`, hôte `:685-744`.
- Données du panneau : `src/frontend/src/components/prototype/usePrototypeInvoiceData.ts:36-124`.
- Coque : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx` : largeur `:350`, hôte `:388-400`, garde `:1076-1090`, `openChat` `:1195-1215`, vue retenue `:1293`, `collapseEmbeddedView` `:1500-1502`, `collapseScenarioPanel` `:1535-1538`, rétrécissement `:1587-1589`, carte `:2219-2233`, fermeture du panneau `:2512-2514`.
- Hôte de la modale : `src/frontend/src/components/invoices/InvoicesPanel.tsx:213-226`, `:616-623`.
- Abandon : `src/frontend/src/lib/saisieEnCours.ts:17-32`, `src/frontend/src/hooks/useQuestionDAbandonDeModale.ts`, `src/frontend/src/hooks/useAbandonDeSaisie.ts:73-83`.
- Profil : `src/frontend/src/stores/billingProfileStore.ts:30-75` ; `src/frontend/src/services/api/config.ts:149-150` ; `src/backend/app/services/user_profile.py:42-45` ; `src/backend/app/services/invoice_pdf.py:682-685`.
- Moteur : `src/backend/app/routers/invoices.py` : arrondi `:186-233`, création `:438-527`, mise à jour `:530-652`, premier envoi `:684-688`, profil `:819-845` ; `src/backend/app/models/schemas.py:793`, `:1273-1340` ; `src/backend/app/models/database.py:619`.
- Arrondi : `src/frontend/src/lib/auCentime.ts:8-13`, `lib/auCentime.test.ts`, `tests/test_b1428_arrondi_commercial.py`, `tests/test_f1_coherence_des_couches.py:220-240` ; trésorerie `src/backend/app/services/workspace_tools.py:530-576`.
