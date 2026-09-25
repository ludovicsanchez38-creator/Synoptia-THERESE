# RFC P-121 : un seul formulaire de devis, pour la création et la modification

Rédigé le 25/09/2026. Proposition acceptée par Ludo le 25/09 (« Je valide tout sauf la 141 »), sous une contrainte explicite : **aucune perte de fonctionnalité**. Aucun code avant la validation de ce document.

## 1. Le constat

Claire, persona du cycle 13 (`docs/campagnes/2026-09-25-personas-c13/rapports/claire.md`, claire-31, étapes 5.2 et 5.8, captures 68 et 74) :

- elle **crée** son devis dans le panneau « Facturer » : quantité « 1 » et prix « 0 » sans étiquette visible, TVA « 0% », ligne qui déborde du panneau (claire-28) ;
- elle le **modifie** dans « Modifier DEV-2026-001 », la modale de Devis et factures : colonnes étiquetées, TVA « 0% (exonéré… » tronquée, description coupée ;
- même objet, deux présentations.

Depuis, B-1355 a donné un en-tête de colonnes au panneau et B-1358 a rendu ses accents à la confirmation de conversion. Reste le fond, que l'inventaire ci-dessous rend visible : ce sont deux formulaires, avec des règles différentes, et plusieurs correctifs n'ont été posés que d'un côté.

## 2. Ce qui existe

### 2.1 Deux formulaires, deux hôtes

| | Panneau « Facturer » | Modale de « Devis et factures » |
|---|---|---|
| Composant | `DevisDraftForm` (`components/prototype/InvoiceConversationCard.tsx:314-673`) | `InvoiceForm` (`components/invoices/InvoiceForm.tsx`, 974 lignes) |
| Hôte | `InvoiceWorkspaceCanvas` (`:680-738`), panneau non modal à côté de la conversation, de 440 à 620 px de large (`ConversationCanvasPrototype.tsx:336`) | `InvoicesPanel.tsx:616-623`, modale `role="dialog"` de 896 px au plus |
| Ouverture | « Nouveau devis » et « Préparer un devis » (`InvoiceConversationCard.tsx:185`, `:221`) posent `'new-devis'` (`ConversationCanvasPrototype.tsx:2015-2018`) | « Nouveau devis ou facture » (`InvoicesPanel.tsx:213-216`), clic sur une ligne (`:218-221`) |
| Données | `usePrototypeInvoiceData.ts` : création `:73-83` (type forcé à `devis`), contact `:85-102` | appels directs à l'API (`InvoiceForm.tsx:12`) |
| Pièce existante | détail en lecture seule (`InvoiceConversationCard.tsx:257-312`) | modification complète |

### 2.2 Inventaire des capacités et tests qui les protègent

Chemins des tests : `P/` = `src/frontend/src/components/prototype/`, `I/` = `src/frontend/src/components/invoices/`.

**Périmètre**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Type de pièce | devis seul, forcé deux fois (`:385`, `usePrototypeInvoiceData.ts:74`) | devis, facture, avoir (`Segments`, `:614-629`) ; type par défaut du filtre, B-388 (`:128-130`) | `I/InvoiceForm.typeParDefaut`, `I/InvoiceForm.da` (Segments), `I/InvoiceForm.focusEtLibelles.c12` (B-1035) |
| Modifier une pièce | non | oui (`:409-412`) | `I/InvoiceForm.focusEtLibelles.c12` (B-1038), `I/InvoiceForm.focusInitial` |
| Statut | non (toujours brouillon) | sélecteur (`:655-662`), passage à payée, acceptée ou refusée confirmé (`:429-446`) | `I/InvoiceForm.test` (« ne permet pas de contourner la confirmation via le sélecteur de statut ») |
| Marquer payée, accepter, refuser | non | `:451-501`, confirmation par `requestExternalAction` | `I/InvoiceForm.test` (paiement confirmé), `I/InvoiceForm.da` (Refuser en secondaire) |
| Convertir un devis en facture | non | `:503-532` et dialogue `:931-970` (30 jours, virement), Échap dans l'ordre (B-228), double-clic (B-1397), accents (B-1358) | `I/InvoiceForm.conversionDoubleClic.b1397`, `I/InvoiceForm.conversionAccents.b1358`, `I/InvoiceForm.echap`, `I/InvoicesPanel.conversion.c12` (B-1067) |
| Conditions de paiement en lecture | non | `:834-859` | **aucun** |

**Client**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Client déjà à l'écran présélectionné (entrée 2) | `contactInitial` (`:326-329`) | non | `P/DevisHeriteLeClient` (3) |
| Premier client créé sans quitter, avec téléphone et adresse (B2) | `:460-534` | non | `P/InvoiceConversationCard.test` (« crée le premier contact dans le canevas ») |
| Carnet illisible distingué d'un carnet vide, dans le formulaire | `:535-543` | non : l'erreur est avalée (`:250-252`), le sélecteur paraît vide | **aucun** (les tests B-015 portent sur la liste et le détail) |
| Client hors des 200 récents (B-568) | non | `getContact` (`:242-249`) | `I/InvoiceForm.clientHorsFenetre` |
| Plafond de 200, liste tronquée annoncée | `:574-578` | `:234-238`, `:647-652` | `P/InvoiceConversationCard.brouillonEnregistre`, `I/InvoiceForm.test` (lot F) |

**Saisie et montants**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Date du jour | date civile locale (`:116-127`) | `toISOString().split('T')[0]` (`:134`, `:140-142`) : date UTC, un devis créé à 0 h 30 à Paris prend la date de la veille | **aucun** |
| Validité | champ libre, refusée si inférieure à 1 (`:411-412`) | nombre de 1 à 365, valeur invalide remplacée en silence par 30 (`:693-704`) | **aucun** |
| Devises | cinq codes nus (`:586-590`) | cinq codes avec symbole (`:52-58`) | `I/InvoiceForm.devisesEtDecimales` |
| Taux de TVA | « 20% » à « 0% » (`:622-624`) | « 20% (normale) » à « 0% (exonéré) » (`:44-50`) | `I/InvoiceForm.devisesEtDecimales` (taux) |
| Saisie des montants | virgule acceptée (`:141-145`) | frappe invalide refusée avec sélection rendue (B-1393), collage « 1 000,50 € » (B-1400) (`:96-110`, `:274-301`) | `I/InvoiceForm.saisieDesMontants.b1393`, `I/InvoiceForm.test` (décimaux), `I/InvoiceForm.devisesEtDecimales` |
| Totaux arrondis au centime à chaque ligne, comme le serveur (B-017) | oui (`:350-369`) | **non** (`:309-329`) : trois lignes de 33,33 € à 20 % affichent 119,99 € pour une pièce enregistrée à 120,00 € | `P/InvoiceConversationCard.montantConfirme` (3), côté panneau seulement |
| Total HT par ligne | non | `:797-799` | **aucun** |
| Disposition des lignes | grille et en-tête visuel (B-1355, `:609-627`), en-tête masqué sous `sm` | tableau fixe, colonnes numériques en rem (B-1387, `:707-822`) | `P/InvoiceConversationCard.ligneDevis.b1355` (2) et `I/InvoiceForm.colonnesDesLignes` (1) : **deux gardes contradictoires** |

**Validation et enregistrement**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Règles | client, au moins une ligne, description, quantité ≥ 1, prix ≥ 0, émission, échéance ≥ émission, validité ≥ 1 (`:400-414`) | client, au moins une ligne, description par ligne (BUG-132), nombres valides, quantité ≥ 1, prix ≥ 0 (`:334-382`) ; **ni échéance ni validité** | `P/InvoiceConversationCard.test` (« relie la validation au premier champ de devis fautif »), `I/InvoiceForm.test` (BUG-132, décimaux), `I/InvoiceForm.da` (BUG-132 par ligne), `I/InvoiceForm.soumission` (champs requis) |
| Message d'erreur | sous le formulaire ; pour chaque règle, champ fautif focalisé et relié par `aria-invalid` et `aria-describedby` (`:416-423`) | au pied (B-1039, B-1068, `:871-879`) ; seul le champ description est relié | `I/InvoiceForm.focusEtLibelles.c12` (B-1039, B-1068), `P/InvoiceConversationCard.test` |
| Cause renvoyée par le serveur (D203) | dans le panneau (`:451-454`) | notification seulement (`:420-424`) | `P/InvoiceConversationCard.cycle6` |
| Confirmation avant création | instantané figé, champs verrouillés, revalidation, « ne génère aucun PDF et n'envoie rien » (`:416-458`, `:561-566`, `:648-665`) | création directe (`:403-427`) | `P/InvoiceConversationCard.test` (« demande confirmation et ignore un double clic ») |
| Un seul envoi par geste | `savingRef` (`:433-444`) | un seul bouton rattaché au formulaire (B-011, `:592`, `:924`) | `P/InvoiceConversationCard.test`, `I/InvoiceForm.soumission` (4) |
| Après l'enregistrement | le panneau reste ouvert : « DEV-… enregistré comme brouillon », bouton inactif tant que rien ne change (B-575), avertissement après retouche (B-377) (`:639-646`, `:667-669`) | la modale se ferme, notification « Devis créé » ou « Devis mis à jour » (B-1038), focus rendu (B-1036) | `P/InvoiceConversationCard.brouillonEnregistre` (2), `I/InvoiceForm.focusEtLibelles.c12` |
| Retouche après enregistrement | « Enregistrer le brouillon » crée un **second** devis (`createDevisDraft`, jamais de mise à jour) ; Claire l'a relevé (étape 5.5) | sans objet | **aucun** |

**Profil émetteur, accessibilité, clavier**

| Capacité | Facturer | Modale | Tests |
|---|---|---|---|
| Profil incomplet ou illisible | instantané lu au chargement (`:548-559`), périmé après un passage aux Réglages | store partagé rafraîchi (`:118-127`), bandeau « illisible » (B-001, `:604-612`) | `I/InvoiceForm.test` (P0-PROD-2), `I/InvoiceForm.profilIllisible` (3) |
| Question « Abandonner les modifications ? » (B-1392) | **absente** ; le formulaire n'est pas inscrit dans `lib/saisieEnCours.ts` : fermer le panneau (`ConversationCanvasPrototype.tsx:1373-1376`), changer de parcours ou Échap jettent la saisie | `useQuestionDAbandonDeModale` (`:193-204`, `:913-919`) | `I/InvoiceForm.abandonDeSaisie.b1392` (3) |
| Focus, Échap, piège | panneau non modal (règle de la 0.48.1) | piège (B-1031), focus initial (B-1370), pile d'Échap (B-228) | `I/InvoiceForm.focusEtLibelles.c12`, `I/InvoiceForm.focusInitial`, `I/InvoiceForm.echap` |
| Noms accessibles et identifiants des lignes | « Description ligne n » et suivants | idem, identifiants uniques | `I/InvoiceForm.nomsAccessibles`, `I/InvoiceForm.identifiants`, `I/InvoiceForm.boutonsNommes`, `I/InvoiceForm.francais` |

En tout : 58 tests dans 19 fichiers `InvoiceForm.*` ; 22 tests dans 7 fichiers `InvoiceConversationCard.*`, dont 12 portent sur le formulaire et 10 sur la liste, le détail et le titre ; 3 dans `DevisHeriteLeClient` ; 2 dans `usePrototypeInvoiceData` ; et trois fichiers `InvoicesPanel.*` qui passent par la modale (`conversion.c12`, `creationSousFiltre`, `clavier`).

### 2.3 Ce que l'inventaire révèle

Chaque formulaire porte des correctifs que l'autre n'a pas reçus :

- **au panneau seul** : l'arrondi au centime (B-017), la date civile, la validation de l'échéance et de la validité, le champ fautif relié pour chaque règle, la cause du serveur à l'écran (D203), la distinction carnet illisible et carnet vide (B-015) ;
- **à la modale seule** : la question d'abandon (B-1392), la saisie décimale soignée (B-1393, B-1400), le client hors fenêtre (B-568), le profil rafraîchi et le bandeau « illisible » (B-001), les colonnes en rem (B-1387).

Deux défauts dorment encore : la modale annonce un total qui peut différer d'un centime de la pièce créée, et le panneau crée un doublon quand on retouche un brouillon déjà enregistré. C'est l'argument principal pour un seul formulaire : tant qu'il y en a deux, chaque correctif ne se pose qu'une fois sur deux.

### 2.4 Décisions déjà prises à respecter

- Lot 5 de la DA (`docs/plans/2026-09-11-da-lot5-devis-design.md`, décision 3) : le formulaire de Devis et factures **reste une modale** ; la création en page (P-075, acceptée, non livrée) est au portail. P-121 ne tranche pas P-075 : il le prépare, puisqu'une page deviendrait un troisième hôte du même formulaire.
- Règle de la 0.48.1 : un panneau côte à côte n'est pas une modale. Le panneau Facturer ne reçoit ni piège de focus ni `aria-modal`.
- P-074 (convertir depuis la ligne de la liste), acceptée, non livrée : hors périmètre.

## 3. Options

| | A. Un formulaire, deux hôtes | B. La modale seule | C. Le panneau seul | D. Aligner l'apparence |
|---|---|---|---|---|
| Idée | Un corps de saisie commun (champs, lignes, règles, totaux), monté par le panneau Facturer et par la modale ; chaque hôte garde son cycle de vie | « Préparer un devis » ouvre `InvoiceForm` ; `DevisDraftForm` disparaît | Le panneau Facturer apprend la modification, les statuts et la conversion ; la vue Devis et factures y renvoie | Mêmes libellés et mêmes colonnes, deux codes |
| Pour | Aucune capacité ne dépend d'un portage d'hôte ; un correctif d'un côté profite à l'autre ; P-075 devient un troisième hôte | Un seul composant, un seul cycle de vie | Côte à côte partout | Petit |
| Contre | Remanie le plus gros formulaire du dépôt sous environ 85 tests ; deux cycles de vie à documenter | La modale recouvre la conversation, alors que Facturer promet d'agir à côté ; l'enregistrement qui reste ouvert, le client hérité, le premier client et la confirmation sont à porter dans une modale ; perte ressentie | Contredit la décision 3 du lot 5 ; statuts, paiement et conversion dans 440 px (claire-28 débordait déjà) ; la vue Devis et factures perd sa modale | Ne répond pas au besoin ; la divergence revient au prochain correctif (B-017 en est la preuve) |
| Effort | Moyen (six lots, dont un de gardes) | Moyen | Large | Petit |

## 4. Recommandation : l'option A

C'est la seule option où la contrainte de Ludo se vérifie ligne par ligne : l'inventaire du § 2.2 devient une liste de tests, et chaque capacité aujourd'hui « d'un seul côté » passe des deux côtés par construction.

### 4.1 Découpage

- `components/invoices/saisieDePiece.ts`, **module pur** : taux de TVA et devises (une seule liste, libellés de la modale), ligne vide, `totauxDePiece` (arrondi B-017, miroir de `routers/invoices.py::_montants_de_ligne`), `validerPiece` (union des deux jeux de règles, § 4.3), `requeteDePiece`, date du jour par `lib/civilDate.ts::localDateKey`, nettoyage et analyse des montants (B-1393, B-1400).
- `useSaisieDePiece(initiale)` : l'état de la saisie, les montants en texte, le drapeau « modifiée » que consomment la question d'abandon et l'avertissement B-377.
- `LignesDePiece` : les lignes, leur en-tête, le total HT par ligne, « Ajouter une ligne », « Supprimer la ligne n ».
- `CorpsDePiece` : client, dates, devise, validité, notes, lignes, totaux ; type et statut seulement quand l'hôte les demande. Le message d'erreur est placé par l'hôte (pied de la modale, bas du panneau), mais son texte et son rattachement au champ sont communs.
- **Hôtes** : `InvoiceWorkspaceCanvas` (panneau) et `InvoiceForm` (modale) ne gardent que ce qui tient à leur cycle de vie (§ 4.4).
- Chaque hôte garde **ses identifiants actuels** (une table d'identifiants par hôte : `devis-*` pour le panneau ; `contact`, `issueDate`, `invoiceform-*` pour la modale). Les tests et le lot 5 qui les citent restent valides, et deux hôtes montés ensemble ne partagent aucun identifiant.

### 4.2 Une présentation

- Libellés visibles au-dessus de chaque champ, ceux de la modale (validés au lot 5). Les noms accessibles propres au panneau (« Client du devis », « Échéance du devis ») deviennent ceux du formulaire commun.
- Taux de TVA nommés partout (« 0% (exonéré) »). La colonne TVA est élargie pour que le taux choisi se lise en entier à 125 % (Claire le voyait tronqué dans la modale).
- **Une même ligne, deux dispositions selon la place** : tableau étiqueté (B-1387) dans la modale ; dans le panneau, trop étroit pour les 32,5 rem de colonnes fixes, la même ligne s'empile : description sur toute la largeur, puis Quantité, Prix HT, TVA et Total HT étiquetés, puis « Supprimer ». Le choix se fait par requête de conteneur (`@container` de Tailwind 4), pas par la largeur de la fenêtre : à écran égal, le panneau et la modale n'ont pas la même largeur. Mêmes libellés, même ordre, mêmes champs.

### 4.3 Des règles

- Validation : l'union des deux. Client, au moins une ligne, description de chaque ligne (règle BUG-132 de la modale, erreur par ligne), nombres valides, quantité ≥ 1, prix ≥ 0, date d'émission, échéance ≥ émission, validité de 1 à 365 (une valeur invalide n'est plus remplacée en silence par 30).
- Messages : ceux de la modale (« Renseigne la description d'au moins une ligne. », « Renseigne la description de cette ligne, ou supprime-la. »), plus ceux que seul le panneau connaissait pour l'échéance et la validité.
- Chaque règle focalise et relie son champ (`aria-invalid`, `aria-describedby`), comme le faisait le panneau.
- Totaux B-017 partout : la modale cesse d'annoncer 119,99 € pour 120,00 €.
- Date civile partout.
- Profil émetteur : le store partagé (`useBillingProfileStore`) des deux côtés, bandeau « illisible » compris.
- Cause du serveur à l'écran (D203) des deux côtés : dans le panneau comme aujourd'hui, au pied de la modale en plus de la notification.

### 4.4 Ce que chaque hôte garde

**Panneau Facturer** : devis seulement, sans statut ; client hérité de l'écran (entrée 2) ; création du premier client ; carnet illisible (B-015) ; confirmation sur instantané figé ; il reste ouvert après l'enregistrement (B-575, B-377). Il gagne :

- la question d'abandon B-1392 et son inscription dans `lib/saisieEnCours.ts`, que la coque consulte déjà (`ConversationCanvasPrototype.tsx:990`) et que la fermeture du panneau (`:1373-1376`) devra consulter aussi ;
- après « Confirmer le brouillon », **une retouche met à jour ce devis** au lieu d'en créer un second : le bouton devient « Enregistrer les modifications », l'appel passe par `updateInvoice`, la confirmation reste (question 1).

**Modale** : type, statut et confirmations sensibles ; payée, accepter, refuser ; conversion et son dialogue ; conditions de paiement en lecture ; client hors fenêtre ; piège de focus, Échap, B-011 (bouton rattaché par `form=`) ; fermeture et notification après l'enregistrement. Elle gagne : B-017, la date civile, les règles d'échéance et de validité, le champ fautif relié, la cause du serveur au pied.

### 4.5 Ce que l'utilisateur verra changer

- Même formulaire, mêmes libellés, dans Facturer et dans Devis et factures.
- Facturer : lignes étiquetées, taux nommés, total HT par ligne, question avant de perdre un devis entamé, plus de doublon après retouche.
- Devis et factures : total juste au centime, date du jour juste après minuit, refus d'une échéance antérieure à l'émission, validité invalide signalée au lieu d'être corrigée en silence.

Hors périmètre : les deux formulaires refusent une quantité inférieure à 1, alors que le moteur accepte 0,5 (`tests/test_f1_coherence_des_couches.py:220`). La règle reste inchangée ici ; c'est une décision métier à prendre à part.

## 5. Livraison en lots TDD

Chaque lot : tests rouges d'abord, vérifiés rouges pour la bonne raison ; un commit ; sabotage ciblé par fonction (règle du 27/08) ; six portes ; revue adverse du diff.

0. **Gardes de parité et de caractérisation.** Un test monte les deux hôtes et compare les libellés, les options de TVA et de devises, le message pour une même saisie fautive, et les totaux de trois lignes à 33,33 € (rouge aujourd'hui). Caractérisation des capacités sans test : conditions de paiement en lecture, total HT par ligne, carnet illisible dans le formulaire, date du jour à 0 h 30 heure de Paris, doublon après retouche (rouge, attendu).
1. **Module pur `saisieDePiece.ts`**, branché d'abord dans la modale, qui gagne B-017, la date civile, l'échéance et la validité. Tests unitaires du module. Les 58 tests `InvoiceForm.*` passent, sauf ceux qui citeraient un comportement volontairement changé (validité remplacée par 30) : ils sont réécrits dans le même commit, avec leur intention.
2. **`LignesDePiece`** dans les deux hôtes, avec la disposition par requête de conteneur. `ligneDevis.b1355` et `colonnesDesLignes` fusionnent en une garde sur le composant commun (colonnes nommées, `min-w-0`, table fixe en rem). Recette navigateur obligatoire : jsdom ne mesure aucune largeur.
3. **`CorpsDePiece` et `useSaisieDePiece`**, migration du panneau : la confirmation, le premier client et le client hérité restent dans l'hôte ; profil par le store partagé ; libellés communs (les tests qui citent les anciens noms accessibles du panneau sont adaptés, assertions conservées).
4. **Ce que le panneau gagne** : question d'abandon B-1392, inscription dans `saisieEnCours`, fermeture du panneau retenue ; mise à jour après confirmation au lieu d'un second devis.
5. **Ménage et garde anti-retour** : suppression du code mort du panneau (`parseDecimal`, `arrondirCentimes`, lignes et validation propres) ; une garde qui échoue si une seconde liste de taux de TVA ou un second calcul de totaux réapparaît hors de `saisieDePiece.ts` (même principe que `lexiqueTitres.test.ts`) ; recette finale.

## 6. Plan de tests

**Unitaires** (`saisieDePiece.test.ts`) : totaux (trois lignes de 33,33 € à 20 % = 120,00 € ; lignes à 0 %, 5,5 %, 2,1 %) ; validation règle par règle, ordre et champ désigné ; date du jour avec une heure factice à 0 h 30 et à 23 h 30, fuseau de Paris ; montants « 1 000,50 € », « 12,5 », « -2 », chaîne vide.

**Composants** :

- parité des deux hôtes (lot 0) ;
- panneau : confirmation, double-clic, premier client, client hérité, carnet illisible, B-575, B-377, question d'abandon (Échap, fermeture du panneau, changement de parcours), mise à jour après confirmation (un seul `createInvoice`, puis `updateInvoice`) ;
- modale : les 58 tests existants, plus les règles gagnées.

**Intégration** :

- `usePrototypeInvoiceData` crée puis met à jour le même devis ;
- la liste de Devis et factures montre une seule pièce après une retouche dans Facturer ;
- `InvoicesPanel.conversion.c12` (B-1067) et `creationSousFiltre` (B-569) passent sans modification ;
- côté moteur, rien ne change : `tests/test_f1_coherence_des_couches.py` (trois lignes de 33,33 € à 20 %, base, schéma, PDF et outil de trésorerie d'accord) reste la référence du miroir client et doit rester vert.

**Recette navigateur** (pile jetable 17393 et 1420, jamais 17293) :

- le parcours de Claire (étapes 5.1 à 5.10) à 1280, 1024 et 800 px, à 100 % et 125 %, en thème clair et sombre ;
- vérifier que « 0% (exonéré) » se lit en entier et que « Supprimer la ligne » reste dans le cadre du panneau ;
- vérifier que le PDF du devis et celui de la facture convertie portent les montants de l'écran ;
- vérifier que la question d'abandon apparaît en quittant Facturer avec un devis entamé ;
- captures avant et après.

## 7. Risques et régressions à protéger

- **Deux gardes de présentation contradictoires** (`ligneDevis.b1355`, `colonnesDesLignes`) : l'une est réécrite, et le commit le dit.
- **Identifiants et noms accessibles** (B-234, B-578, lot 5 ; `InvoiceForm.identifiants`, `nomsAccessibles`, `boutonsNommes`, `da`) : une table d'identifiants par hôte.
- **B-011** : le bouton d'envoi de la modale vit hors du bloc défilant et reste rattaché par `form="invoice-form"` ; le corps commun ne doit pas créer un second `<form>`.
- **Focus et Échap** : focus initial différent selon l'hôte (B-1370) ; pile d'Échap et ordre du dialogue de conversion (B-228) ; aucun piège dans le panneau (0.48.1).
- **Montants** : B-017 change l'affichage de la modale au centime près dans de rares cas. C'est le correctif ; `montantConfirme` est étendu à la modale.
- **Validité** : la modale refusera une validité invalide au lieu de la remplacer par 30.
- **Largeur** : jsdom ne voit ni débordement ni troncature ; seule la recette prouve B-1355, B-1387 et claire-28.
- **Question d'abandon dans le panneau** : elle consulte la même source que la coque (`sortieRetenueParUneSaisie`), sans poser deux questions pour un seul geste (motif B-994).
- **Mise à jour après confirmation** : un brouillon supprimé entre-temps dans Devis et factures renvoie 404. Le panneau le dit et repropose la création, sans rien perdre de la saisie.

## 8. Questions pour Ludo

1. Retoucher un devis que Facturer vient d'enregistrer : mettre à jour ce devis (recommandé), ou en créer un second (comportement actuel) ?
2. La confirmation en deux temps (« Confirmer le brouillon ») reste-t-elle propre à Facturer (recommandé), ou s'étend-elle à la création dans Devis et factures ?
3. Taux de TVA nommés partout, « 0% (exonéré) » (recommandé), ou taux nus ?
4. Facturer doit-il aussi modifier un devis existant, aujourd'hui en lecture seule ? Recommandation : pas dans ce chantier.

## Annexe : appuis dans le code

- Panneau : `src/frontend/src/components/prototype/InvoiceConversationCard.tsx` : instantané `:41-58`, dates `:116-127`, montants `:137-145`, détail en lecture seule `:257-312`, formulaire `:314-673` (totaux `:350-369`, validation `:400-414`, confirmation `:416-458`, premier client `:460-534`, champs `:561-636`, états `:638-669`), hôte `:680-738`.
- Données du panneau : `src/frontend/src/components/prototype/usePrototypeInvoiceData.ts:73-102`.
- Coque : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx` : rendu `:372-385`, largeur du panneau `:336`, ouverture `:2006-2020`, sorties retenues `:990`, `:1201`, `:1332`, fermeture du panneau `:1373-1376`.
- Modale : `src/frontend/src/components/invoices/InvoiceForm.tsx` : listes `:44-83`, montants `:88-110`, profil `:118-127`, dates `:133-143`, abandon `:193-204`, contacts `:227-253`, saisie décimale `:274-301`, totaux `:309-329`, envoi `:331-449`, actions `:451-532`, champs `:614-704`, lignes `:707-822`, conditions `:834-859`, pied `:871-929`, conversion `:931-970`.
- Hôte de la modale : `src/frontend/src/components/invoices/InvoicesPanel.tsx:213-251`, `:616-623`.
- Abandon : `src/frontend/src/hooks/useQuestionDAbandonDeModale.ts`, `src/frontend/src/lib/saisieEnCours.ts`.
- Serveur : `src/backend/app/routers/invoices.py` (montants `:185-230`, mise à jour `:503`, conversion `:953`) ; référence des montants `tests/test_f1_coherence_des_couches.py`.
