# Cycle 20 : diff-front-1

Arbre `gpt/c20-diff-front-1`, base constatée `4dfc79d1`. Aucun commit ni push : l'index Git est interdit en écriture dans ce bac à sable. Aucun service en ligne ni fournisseur LLM appelé. Les chemins de profil des tests sont des chaînes fictives en mémoire.

Les candidats sont examinés dans l'ordre demandé. Les doublons renvoient à leur première preuve. Les erreurs ci-dessous ont été observées avant correction, puis recopiées ici avant l'édition du code de production.

| ID | Verdict | Test (chemin::nom) | Rouge observé (aucun commit) | Correctif |
| --- | --- | --- | --- | --- |
| B-1868 | confirme | `src/frontend/src/lib/profileStorageIsolation.test.ts::B-1868 conserve le cache du même dossier` (5 cas) | `AssertionError: expected 'switched' to be 'unchanged' // Object.is equality` | non commité |
| B-1869 | rejete | `src/frontend/src/components/atelier/AgentCatalog.modeles.test.tsx::conserve le fournisseur et le modèle choisis quand ils ne sont plus proposés` | Aucun : test existant vert | sans changement |
| B-1870 | confirme | `src/frontend/src/components/settings/LLMTab.effortOpenAI.test.tsx::B-1870 : Astra propose Très élevé et transmet xhigh à l’enregistrement` | `TestingLibraryElementError: Unable to find an accessible element with the role "option" and name /Très élevé/` | non commité |
| B-1871 | rejete | `src/frontend/src/components/atelier/AgentSession.c9.test.tsx::dit que les outils ne sont pas confirmés quand le serveur ne répond pas` et `AgentSession.avatars.c9.test.tsx::sans profil serveur, l’invite ne liste pas les outils de la table locale` | Aucun : 4 tests existants verts | sans changement |
| B-1872 | rejete | `src/frontend/src/components/atelier/AgentSession.avatars.c9.test.tsx::sans profil serveur, l’invite ne liste pas les outils de la table locale` | Aucun : deux nœuds distincts, invite et confirmation | sans changement |
| B-1873 | rejete | `AgentSession.outilsJumeaux.c9.test.tsx::le premier bloc reçoit « contenu de a », le second « contenu de b »` ; sonde supplémentaire par bloc, décrite ci-dessous | Aucun : sonde verte avant toute correction | sans changement |
| B-1988 | rejete | `src/frontend/src/components/invoices/InvoicesPanel.clavier.test.tsx::ouvrir le PDF depuis la ligne n’ouvre pas aussi le formulaire` | Aucun : bouton déjà nommé par `aria-label`, ligne 573 | sans changement |
| B-1990 | rejete | `src/frontend/src/components/atelier/AgentCatalog.modeles.test.tsx::conserve le fournisseur et le modèle choisis quand ils ne sont plus proposés` | Aucun : conservation explicite du modèle configuré | sans changement |
| B-1992 | confirme | `src/frontend/src/components/invoices/InvoicesPanel.da.test.tsx::B-1992 : un avoir payé affiche son remboursement` (2 cas) | `TestingLibraryElementError: Unable to find an element with the text: Remboursé le 02/04/2026.` ; même erreur pour `Remboursé` sans date | non commité |
| B-1993 | confirme | `src/frontend/src/components/invoices/statutsFacture.b1993.test.ts::B-1993 : les statuts s’accordent avec le type de pièce` ; `presentationFacture.test.ts::B-1993 : la facture historique %s garde un libellé féminin` ; `InvoicesPanel.da.test.tsx::B-1993 : les filtres du type %s portent les libellés de ce type` | `AssertionError: expected 'Accepté' to be 'Acceptée' // Object.is equality` (idem Refusé, Expiré, Converti) ; `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Envoyé"` | non commité |
| B-1994 | confirme | `src/frontend/src/components/invoices/InvoicesPanel.da.test.tsx::B-1994 : une erreur de chargement nomme devis, factures et avoirs` | `Error: expect(element).toHaveTextContent()` ; reçu : `Chargement impossibleImpossible de charger les factures pour le moment.Réessayer` | non commité |
| B-1996 | rejete | `src/frontend/src/lib/coutAffiche.test.ts::affiche des dollars, jamais des euros non convertis` ; `LimitsTab.cycle6.test.tsx::affiche 0 et une barre à 0 %, ni 50 ni NaN` | Aucun : unité USD explicite dans le code et dans l’aide du champ | sans changement |
| B-1997 | rejete | `src/frontend/src/lib/coutAffiche.test.ts::affiche des dollars, jamais des euros non convertis` | Aucun : nom historique du champ, valeur en dollars | sans changement |
| B-1998 | rejete | `src/frontend/src/components/atelier/AgentSession.c9.test.tsx::dit que les outils ne sont pas confirmés quand le serveur ne répond pas` | Aucun : invite et carte de confirmation distinctes | sans changement |
| B-1999 | rejete | `src/frontend/src/components/atelier/AgentSession.avatars.c9.test.tsx::sans profil serveur, l’invite ne liste pas les outils de la table locale` | Aucun : invite et carte de confirmation distinctes | sans changement |

## Exécution des tests

Le premier lancement standard de Vitest est bloqué avant tout test : `EPERM: operation not permitted` lors de la création de `node_modules/.vite-temp`. Ce dossier pointe vers le dépôt principal. Les lancements suivants utilisent `--configLoader runner --no-cache`, sans écrire dans les dépendances partagées, et `--maxWorkers=3`. `npx --no-install` interdit tout téléchargement implicite.

## Causes confirmées et chemins de production

- **B-1868.** `App.tsx:145` appelle réellement `isolateDataProfilePersistence` avec le dossier annoncé par le moteur. Avant correction, cinq variantes n'ayant pour différence qu'un slash final déclenchaient `switched`, effaçaient le cache et rechargeaient. `profileStorageIsolation.ts:13-20,32-40` compare maintenant les chemins sans slash final, en préservant les racines `/` et `C:/`. Le marqueur existant reste inchangé, car les accords en attente sont rattachés à cette identité. Les scénarios de changement réel de profil et les cinq tests voisins d'isolement des accords restent verts. Portée volontaire : ni développement de `~`, ni assimilation d'une barre inverse à `/`, ni résolution de liens symboliques ou changement de casse. Sur POSIX, ces graphies ne garantissent pas le même dossier. Le code backend construit un `Path` à partir du dossier fourni, sans expansion du tilde (`src/backend/app/config.py:69-73`).
- **B-1870.** `LLMTab.tsx:732` appelle `effortXhighPropose` pour construire le sélecteur. Astra manquait dans l'ensemble de `effortOpenAI.ts:24`, alors que le contrat interne `tests/test_p057_gpt6_astra.py::test_gpt_6_astra_est_au_catalogue_openai_avec_sa_fiche` autorise déjà `xhigh`. L'ajout d'Astra suffit. Le nouveau test exige l'option accessible, le changement de valeur et l'appel d'enregistrement exact avec `xhigh`. Cette vérification porte sur la cohérence de THÉRÈSE, pas sur les capacités actuelles d'un fournisseur externe.
- **B-1992.** `InvoicesPanel.tsx:508` appelle `cellulesStatut` pour chaque ligne. La branche `paid` de `presentationFacture.ts:175-176` réutilise maintenant `libelleStatutPiece`, déjà utilisé par le formulaire (`InvoiceForm.tsx:611,853`). Elle affiche « Remboursé », avec ou sans date, pour un avoir. Les factures conservent « Payée ». La date et la tonalité de succès restent contrôlées.
- **B-1993.** La fonction partagée, appelée par le formulaire, les filtres (`InvoicesPanel.tsx:390`) et le repli de ligne (`presentationFacture.ts:212`), accorde désormais accepté, refusé, expiré et converti avec « facture ». Le repli continue d'afficher le statut historique réel, même pour une ancienne combinaison type/statut qui n'est plus proposée à la création. Les filtres emploient le type sélectionné ; sans type précis, ils gardent l'accord féminin historique. Les nouveaux tests couvrent les quatre statuts, leur repli dans une ligne de facture et les filtres Devis/Avoirs.
- **B-1994.** Le `catch` de `loadInvoices` (`InvoicesPanel.tsx:145`) alimente directement l'alerte de chargement. Le message inclut maintenant devis, factures et avoirs. Le nouveau test déclenche un rejet HTTP simulé, contrôle le texte et conserve une action « Réessayer » activée.

## Motifs des rejets

- **B-1869 et B-1990.** Le commentaire de tête de B-649 est ancien. La décision explicite portée par le commit existant `ccff1831` (« Confidentialité : supprimer les replis des agents, du Board et de l’Atelier ») a remplacé la substitution automatique par la conservation du modèle configuré et modifié l'assertion en conséquence. Le code courant le dit à `AgentCatalog.tsx:106-107` et ajoute une option visible « choix conservé » à la ligne 182. Le défaut du profil vient du modèle configuré dans le moteur (`src/backend/app/routers/agents.py:496,510`). Les trois tests des deux fichiers du catalogue sont verts. Aucun retour à l'ancien remplacement automatique.
- **B-1871, B-1872, B-1998 et B-1999.** Les textes ne visent pas le même nœud. L'invite sans message affiche « Outils non confirmés par le serveur » (`AgentSession.tsx:854`). Après saisie et envoi, la carte de confirmation affiche « Outils déclarés : non confirmés par le serveur » (`:749`). Les deux fichiers passent ensemble, soit quatre tests ; la confirmation sans modèle reste désactivée et aucun lancement d'agent n'est effectué dans ce scénario.
- **B-1873.** La faiblesse des assertions globales du test ancien est réelle, mais le défaut fonctionnel allégué n'est pas reproduit. Le traitement choisit déjà le premier appel du même outil encore sans résultat (`AgentSession.tsx:428-443`). Une sonde temporaire reprend le flux du test existant et exige exactement deux boutons, puis contrôle chaque bloc avec `within` : le premier contient seulement « contenu de a », le second seulement « contenu de b ». Résultat : un test vert avant toute correction. Pour respecter « aucun changement » sur un rejet, la sonde a été déplacée dans `/tmp/diff-front-1-AgentSession.sondeB1873.test.tsx` ; sortie dans `/tmp/diff-front-1-B-1873-sonde.log`. Le test existant reste inchangé. Le constat de couverture est conservé ici, sans le transformer en bug prouvé du composant.
- **B-1988.** Le bouton est un vrai bouton, contient le texte visible « PDF » et possède déjà un `aria-label` explicite comprenant l'action et l'identité de la pièce (`InvoicesPanel.tsx:567-580`). Il ne dépend donc pas du seul `title`. Les cinq tests des fichiers clavier et libellé accessible passent. Le test PDF utilise un simulacre sans retour de fichier et journalise une erreur attendue ; ce test ne prouve pas l'ouverture d'un PDF natif, seulement l'absence d'ouverture du formulaire.
- **B-1996 et B-1997.** Le commentaire du test correspond à l'interface réelle : `coutAffiche.ts:14` fixe `$`, `LimitsTab.tsx:221-231` affiche et explique cette unité. Le moteur définit le plafond comme un montant USD malgré son nom historique (`token_tracker.py:282-284`) et le compare à des coûts en USD (`:719-724`). Le test `coutAffiche.test.ts::affiche des dollars, jamais des euros non convertis` et les deux cas `tests/test_b1475_unite_des_couts.py::test_la_consommation_dit_son_unite` confirment ce contrat. Le renommage des champs reste une dette existante ; aucun taux de change n'a été inventé.

## Assertions existantes mises à jour

Aucun scénario ni garde existant n'a été supprimé. Ces changements d'attendu sont nécessaires pour ne plus figer les formulations corrigées :

- B-1992 : dans `InvoicesPanel.da.test.tsx`, l'avoir payé attend désormais exactement « Remboursé le » au lieu de « Payé le » ; la vérification de l'absence de « Payée » reste en place.
- B-1993 : `presentationFacture.test.ts` attend « Convertie » pour une facture historique convertie, en conservant les contrôles du ton neutre et de l'absence d'impayé. `InvoicesPanel.filtreType.test.tsx` attend « Envoyé » dans la rangée Devis ; la liste complète et le bouton sélectionné restent vérifiés.
- B-1994 : les trois tests existants d'erreur (`InvoicesPanel.da.test.tsx`, `InvoicesPanel.test.tsx`, `InvoicesPanel.chargementEchoue.test.tsx`) attendent la formulation complète. Les contrôles de reprise, de compteur et de troncature restent intacts.

## Règles à trancher et limites

Aucun candidat `regle_a_trancher` : les règles utiles sont déjà fixées dans le code, les tests ou l'historique Git vérifié. Les chemins avec `~`, barres inverses, liens symboliques ou différences de casse ne sont pas fusionnés par hypothèse. Le rendu natif Tauri, les lecteurs d'écran réels et les fournisseurs LLM n'ont pas été sollicités. La suite complète et le rejeu des rouges sur la base restent à l'orchestrateur.

## Portes finales

La dernière passe des 48 fichiers frontend a été rejouée après la garde sur la racine de lecteur et donne 280 réussites. TypeScript et ESLint ont également été relancés sur cet état final.

Les rapports XML ont été lus avec `xml.etree.ElementTree`, en comptant les éléments `testcase`, `failure`, `error` et `skipped`, sans dépendre de la console tronquée.

| Porte | Périmètre | Passés | Échoués | Erreurs | Ignorés | Résultat |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pytest | 3 fichiers voisins des contrats utilisés | 18 | 0 | 0 | 0 | code 0 ; `/tmp/diff-front-1-pytest.xml` |
| Vitest | 48 fichiers ciblés, 3 workers maximum | 280 | 0 | 0 | 0 | code 0 ; `/tmp/diff-front-1-vitest.xml` |
| Vitest, recontrôle | `InvoicesPanel.da.test.tsx` après retrait de l'option de test invalide | 16 | 0 | 0 | 0 | code 0 ; `/tmp/diff-front-1-vitest-recontrole.xml` ; cas déjà compris dans les 280 |
| Ruff | `src/backend tests`, sans correction | sans objet | 0 | 0 | sans objet | code 0, `All checks passed!` |
| TypeScript | `npx --no-install tsc --noEmit` | sans objet | 0 | 0 | sans objet | code 0, aucune erreur après correction du test |
| ESLint | `npm run lint` | sans objet | 0 | 0 | sans objet | code 0, 27 avertissements, seuil existant 27 |

Premier contrôle TypeScript : une erreur `TS2769` dans le nouveau test `InvoicesPanel.da.test.tsx`, ligne 319, car `getByRole` n'accepte pas l'option `exact`. Cette option superflue a été retirée : une chaîne passée à `name` exige déjà le nom exact. Le fichier rejoué seul après cet ajustement donne 16 réussites ; TypeScript termine ensuite avec le code 0. Noms des tests en échec aux portes finales Pytest/Vitest : aucun. `git diff --check` est également vert. Les 27 avertissements ESLint portent sur `react-hooks/exhaustive-deps` et `react-refresh/only-export-components` aux lignes non modifiées.

### Commandes de rejeu

Le backend a été exécuté avec un dossier jetable créé sous `/tmp` et fourni uniquement au processus de test, afin de ne jamais employer un profil personnel. Commande exécutée, avec cette isolation supplémentaire :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_p057_gpt6_astra.py tests/test_effort_openai_parite_frontend.py tests/test_b1475_unite_des_couts.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-front-1-pytest.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Dans `src/frontend`, la liste exacte des 48 fichiers est conservée dans `/tmp/diff-front-1-vitest-files.txt`. Elle comprend `profileStorageIsolation`, ses voisins de persistance et d'accords, `effortOpenAI`, les tests `LLMTab`, les tests `InvoicesPanel`, `presentationFacture`, `statutsFacture`, trois fichiers du formulaire consommateurs des libellés, puis les fichiers des candidats rejetés. Aucun lancement de la suite complète :

```sh
npx --no-install vitest run \
  src/components/atelier/AgentCatalog.cycle6.test.tsx \
  src/components/atelier/AgentCatalog.modeles.test.tsx \
  src/components/atelier/AgentSession.avatars.c9.test.tsx \
  src/components/atelier/AgentSession.c9.test.tsx \
  src/components/atelier/AgentSession.outilsJumeaux.c9.test.tsx \
  src/components/invoices/InvoiceForm.datePaiement.p155.test.tsx \
  src/components/invoices/InvoiceForm.test.tsx \
  src/components/invoices/InvoicesPanel.causePdf.test.tsx \
  src/components/invoices/InvoicesPanel.causeSuppression.test.tsx \
  src/components/invoices/InvoicesPanel.chargementEchoue.test.tsx \
  src/components/invoices/InvoicesPanel.clavier.test.tsx \
  src/components/invoices/InvoicesPanel.conversion.c12.test.tsx \
  src/components/invoices/InvoicesPanel.creationSousFiltre.test.tsx \
  src/components/invoices/InvoicesPanel.cycle6.test.tsx \
  src/components/invoices/InvoicesPanel.da.test.tsx \
  src/components/invoices/InvoicesPanel.debordement.p162.test.tsx \
  src/components/invoices/InvoicesPanel.etatVideParDefaut.test.tsx \
  src/components/invoices/InvoicesPanel.fermetureSaisie.b1866.test.tsx \
  src/components/invoices/InvoicesPanel.filtreType.test.tsx \
  src/components/invoices/InvoicesPanel.focusSuppression.c10.test.tsx \
  src/components/invoices/InvoicesPanel.largeurEtroite.test.tsx \
  src/components/invoices/InvoicesPanel.libelleAccessible.b1615.test.tsx \
  src/components/invoices/InvoicesPanel.nomDialogue.b1980.test.tsx \
  src/components/invoices/InvoicesPanel.squelette.b1982.test.tsx \
  src/components/invoices/InvoicesPanel.statutInconnu.test.tsx \
  src/components/invoices/InvoicesPanel.test.tsx \
  src/components/invoices/InvoicesPanel.troncature.test.tsx \
  src/components/invoices/presentationFacture.dateDEnvoi.p139.test.ts \
  src/components/invoices/presentationFacture.envoiNonTrace.b1449.test.ts \
  src/components/invoices/presentationFacture.test.ts \
  src/components/invoices/statutsFacture.b1993.test.ts \
  src/components/invoices/statutsProposes.test.tsx \
  src/components/settings/LLMTab.autres.test.tsx \
  src/components/settings/LLMTab.clesDoubles.test.tsx \
  src/components/settings/LLMTab.da.test.tsx \
  src/components/settings/LLMTab.effortOpenAI.test.tsx \
  src/components/settings/LLMTab.modeles.c18m1.test.tsx \
  src/components/settings/LLMTab.ollamaCloud.b1160.test.tsx \
  src/components/settings/LLMTab.ollamaCloud.test.tsx \
  src/components/settings/LLMTab.qwen.test.tsx \
  src/components/settings/LLMTab.refusAnnonce.test.tsx \
  src/components/settings/LLMTab.test.tsx \
  src/components/settings/LimitsTab.cycle6.test.tsx \
  src/lib/consentSync.profiles.test.ts \
  src/lib/coutAffiche.test.ts \
  src/lib/effortOpenAI.test.ts \
  src/lib/profileStorageIsolation.test.ts \
  src/lib/purgeLocalData.test.ts \
  --maxWorkers=3 --configLoader runner --no-cache --reporter=default --reporter=junit --outputFile.junit=/tmp/diff-front-1-vitest.xml
npx --no-install tsc --noEmit
npm run lint
```

### Preuves des rouges isolés

Les cinq candidats confirmés ajoutent **19 cas de test**, tous observés rouges sur la cause attendue avant leur correction : B-1868 (5), B-1870 (1), B-1992 (2), B-1993 (10), B-1994 (1). Journaux :

- `/tmp/diff-front-1-B-1868-rouge.log` : 5 échecs, 4 tests existants ignorés par le filtre.
- `/tmp/diff-front-1-B-1870-rouge.log` : 1 échec, 7 tests existants ignorés.
- `/tmp/diff-front-1-B-1992-rouge.log` : 2 échecs, 11 tests existants ignorés.
- `/tmp/diff-front-1-B-1993-rouge.log` : les 8 échecs de fonctions pures donnent les quatre accords masculins incorrects. Le premier essai des deux tests d'écran attendait à tort le vide général sous un filtre ; l'attente de chargement du test a été rectifiée avant correction de production, puis les deux écrans ont échoué sur l'absence du bouton « Envoyé », dans `/tmp/diff-front-1-B-1993-filtres-rouge.log` (2 échecs, 13 ignorés).
- `/tmp/diff-front-1-B-1994-rouge.log` : 1 échec, 15 tests existants ignorés.

Garde ajoutée pendant la relecture de B-1868 : `profileStorageIsolation.test.ts::B-1868 : une racine de lecteur reste distincte du chemin relatif au lecteur`. La première version du correctif assimilait `C:/` à `C:`. Le test a donné `AssertionError: expected 'unchanged' to be 'switched' // Object.is equality`, recopié ici avant ajustement (`/tmp/diff-front-1-B-1868-garde-racine-rouge.log`). Ce vingtième cas protège le correctif ; il porte sur une régression de la première correction et n'est pas compté parmi les 19 rouges initiaux.

Les changements sont laissés non commités dans l'arbre. Aucun `git add`, commit, push, dépôt annexe ou bundle n'a été tenté.

## Remédiation de la relecture, passe 1

Reprise sur `5f70dd49`, arbre initialement propre. Les deux constats P1 sont confirmés. Les informations ci-dessus décrivent la passe initiale ; les preuves et limites de cette remédiation figurent ici.

### Rouges isolés avant correction

- **Constat 1, moteur** : `tests/test_c20_identite_profil.py::test_r1_c1_stats_identifient_le_dossier_reel`, lancé seul. `AssertionError: Le moteur doit annoncer le dossier canonique`. XML `/tmp/diff-front-1-r1-c1-rouge.xml` lu : 1 échec, aucune erreur.
- **Constat 1, cache** : `profileStorageIsolation.test.ts::R1-C1 : conserve le cache sous un ancien chemin avec .. vérifié par le moteur`, lancé seul. `AssertionError: expected 'switched' to be 'unchanged' // Object.is equality`. XML `/tmp/diff-front-1-r1-c1-front-rouge.xml` lu : 1 échec, 11 ignorés par le filtre, aucune erreur.
- **Constat 2, retrait** : `consentSync.profiles.test.ts::R1-C2 : reprend le retrait sous A/ après A → B → A avant de relire les accords`, lancé seul. `AssertionError: expected [] to deeply equal [ { …(8) } ]`. XML `/tmp/diff-front-1-r1-c2-rouge.xml` lu : 1 échec, 5 ignorés par le filtre, aucune erreur. Le retrait n'est pas transmis au retour dans A.
- **Constat 1, branchement** : `App.demarrageAccords.test.tsx::R1-C1 : fait vérifier les anciennes identités avant le cloisonnement`, lancé seul : `AssertionError: expected "vi.fn()" to be called with arguments: [ [ …(2) ] ]` ; reçu `[]`.
- **Constat 1, transport simulé** : `core.profil.test.ts::R1-C1 : transmet les chemins à vérifier sans les normaliser dans une URL`, lancé seul : `AssertionError: expected [] to deeply equal [ '/profils/intermediaire/../A', …(1) ]`.
- **Constat 2, garde sur plusieurs files** : `consentSync.profiles.test.ts::R1-C2 : fusionne les files équivalentes dans l’ordre sans doublon ni décision de B`, lancé seul : `AssertionError: expected [ { event_id: 'accord', …(6) } ] to deeply equal []`. La copie de l'accord restait dans l'ancienne file après acquittement et risquait de revenir.

### Correctifs et contrôles voisins

Le constat 1 fait annoncer par `/api/config/stats` l'identité `data_profile`, résolue sur disque, en conservant le chemin configuré `data_dir`. La même route vérifie les identités anciennes du marqueur et des files locales ; le frontend conserve son cache uniquement si le moteur confirme l'équivalence, ou si la différence se limite aux barres finales déjà reconnues. Un chemin traversant un lien symbolique vers un autre dossier et un intermédiaire inexistant ne sont pas acceptés comme alias. Le marqueur courant reste stable pour les opérations en vol.

Après ce premier correctif, relecture des appelants : démarrage `App`, statistiques des réglages, dossier affiché à la mise en route, purge et gardes de profil de l'Atelier. Tests voisins : **9 tests backend réussis** (identité et accords moteur), **54 tests frontend réussis** sur 10 fichiers. Le test du constat 2, encore rouge à cette étape, est seul exclu par le filtre. XML lus : `/tmp/diff-front-1-r1-c1-voisins.xml` et `/tmp/diff-front-1-r1-c1-voisins-front.xml`.

Le constat 2 réunit les files des identités équivalentes dans celle du profil actif avant toute purge ou synchronisation. Les événements gardent leur identifiant et leur date, sont dédoublonnés et remis dans l'ordre chronologique. La destination est écrite avant le retrait des anciennes clés et sa révision est incrémentée pour invalider une relecture antérieure. Les files des autres dossiers restent intactes. Le scénario d'aller-retour est étendu à un ancien chemin avec `..` confirmé par le moteur.

Garde de migration ajoutée à la relecture du correctif : remplacer le chemin configuré par sa résolution perdait le suffixe historique `.therese` quand ce dossier était un lien. Le test backend isolé a donné `AssertionError: Le chemin configuré reste nécessaire à la migration historique` ; celui du frontend, `AssertionError: expected '/profils/.therese' to be '/profils/A' // Object.is equality`. Les deux champs sont donc distincts : le chemin configuré conserve la règle de migration existante, l'identité résolue sert au cloisonnement. XML : `/tmp/diff-front-1-r1-c1-historique-rouge.xml` et `/tmp/diff-front-1-r1-c1-historique-front-rouge.xml`.

La lecture des identités locales est aussi couverte par l'arrêt de cloisonnement : son déplacement avant les statistiques ne doit pas transformer une panne déterministe du stockage en simple échec réseau réessayé. Le nouveau test `App.demarrageAccords.test.tsx::R1-C1 : une identité locale illisible arrête le démarrage avant les statistiques` a d'abord échoué seul avec `Unable to find role="heading" and name "Cloisonnement du profil impossible"` (`/tmp/diff-front-1-r1-c1-lecture-rouge.xml`, 1 échec). La collecte et l'isolation utilisent maintenant le même arrêt ; les erreurs réseau des statistiques gardent leur traitement existant.

Après le correctif du constat 2, les appelants relus sont `queueConsentDecision`, `flushConsentDecisions`, `synchroniserConsentements`, `purgeLocalPersistence` et le démarrage. Les tests voisins couvrent aussi les gardes d'accord avant une requête métier et avant une mission de l'Atelier. Deux gardes supplémentaires vérifient qu'une réponse GET ancienne ne réactive pas un accord après la fusion et qu'un refus d'écriture de la destination conserve la file source, le marqueur et le cache. Ces gardes passent sans ajustement supplémentaire de production.

### Portes finales de la passe 1

**15 cas ajoutés** : 10 pour le constat 1 (3 backend, 7 frontend), 5 pour le constat 2. Aucun test préexistant supprimé, ignoré ou affaibli. Les nouvelles reproductions restent dans les tests pour le rejeu de l'orchestrateur sans les correctifs.

| Porte | Périmètre | Passés | Échecs | Erreurs | Ignorés | Preuve |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pytest | 2 fichiers, identité du profil et accords moteur | 10 | 0 | 0 | 0 | code 0 ; `/tmp/diff-front-1-r1.xml` |
| Vitest | 13 fichiers ciblés, 3 workers maximum | 83 | 0 | 0 | 0 | code 0 ; `/tmp/diff-front-1-r1-vitest.xml` |
| Ruff | `src/backend tests`, sans correction automatique | sans objet | 0 | 0 | sans objet | code 0 ; `All checks passed!` |
| TypeScript | `tsc --noEmit` | sans objet | 0 | 0 | sans objet | code 0 |
| ESLint | `npm run lint` | sans objet | 0 | 0 | sans objet | code 0 ; 27 avertissements existants ; `/tmp/diff-front-1-r1-eslint.log` |
| Git | `git diff --check` | sans objet | 0 | 0 | sans objet | code 0 ; aucun changement indexé |

Les XML finaux ont été lus avec `xml.etree.ElementTree`, en comptant les cas, échecs, erreurs et ignorés. Aucun rouge connu exclu des comptes finaux, aucun autre rouge restant. Ruff avait signalé l'ordre des imports (`I001`) dans le nouveau fichier `test_c20_identite_profil.py` ; seul cet import ajouté a été rectifié avant le rejeu vert.

Commandes de rejeu depuis la racine de cet arbre, puis son dossier frontend :

```sh
THERESE_DATA_DIR=$(mktemp -d /tmp/diff-front-1-r1-XXXXXX) \
  PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 \
  .venv/bin/python -m pytest \
  tests/test_c20_identite_profil.py tests/test_t4_consentement_moteur.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-front-1-r1.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
cd src/frontend
npx --offline --no-install vitest run \
  src/lib/profileStorageIsolation.test.ts \
  src/lib/consentSync.profiles.test.ts \
  src/lib/consentSync.test.ts \
  src/lib/consentSync.demarrage.test.ts \
  src/lib/consent.test.ts \
  src/lib/purgeLocalData.test.ts \
  src/lib/debouncedStorage.test.ts \
  src/App.demarrageAccords.test.tsx \
  src/OnboardingRafraichitLeProfil.test.tsx \
  src/services/api/core.profil.test.ts \
  src/services/api/core.test.ts \
  src/services/api/core.accordNonEnregistre.test.ts \
  src/components/atelier/AgentSession.profils.test.tsx \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=default --reporter=junit --outputFile.junit=/tmp/diff-front-1-r1-vitest.xml
npx --offline --no-install tsc --noEmit
npm run lint
```

Les options Vitest évitent toute écriture de cache dans les dépendances partagées ; `--offline --no-install` interdit le téléchargement. Les appels HTTP des scénarios sont simulés ou traités en mémoire par TestClient, les dossiers backend sont jetables sous `/tmp`, et les chemins frontend sont fictifs. Aucune suite complète, aucun service lancé, aucun accès réseau ni fournisseur LLM, aucun usage des ports interdits, du profil personnel ou de `.app-loop/`. Aucun `rm`, `git add`, commit, dépôt annexe ou bundle. Les 11 fichiers concernés restent non commités dans cet arbre, prêts pour le rejeu contradictoire.
