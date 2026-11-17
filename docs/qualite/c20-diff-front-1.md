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

## Remédiation de la relecture, passe 2

### Rouges observés avant correction

- **Constat 6** : test rétabli depuis l’intégration, `tests/test_c20_b1889_notes_heritees.py::test_note_rattachee_preservee_si_evenement_sans_projet`, lancé seul : `AssertionError: assert None == 'projet-existant'`. XML `/tmp/diff-front-1-r2-c6-rouge.xml` lu : 1 échec, 0 erreur.
- **Constat 1** : `test_c20_identite_profil.py::test_r2_c1_casse_du_volume_et_identite_historique`, lancé seul : `AssertionError: La casse dépend du volume, pas de resolve()`. XML `/tmp/diff-front-1-r2-c1-rouge.xml` lu : 1 échec. Le test appelle la route avec une session SQL simulée ; une première tentative via TestClient a été interrompue pendant son initialisation, sans résultat de test.
- **Constat 2** : `profileStorageIsolation.test.ts::R2-C2 : un ancien lien réorienté ne prouve pas à qui appartenaient le cache et les accords`, lancé seul : `AssertionError: expected 'unchanged' to be 'switched' // Object.is equality`. XML `/tmp/diff-front-1-r2-c2-rouge.xml` lu : 1 échec.
- **Constat 3** : `profileStorageIsolation.test.ts::R2-C3 : les espaces du dossier canonique restent significatifs`, lancé seul : `AssertionError: expected 'unchanged' to be 'switched' // Object.is equality`. XML `/tmp/diff-front-1-r2-c3-rouge.xml` lu : 1 échec.
- **Constat 4** : `consentSync.profiles.test.ts::R2-C4 : le recul de l’horloge ne renverse pas les décisions d’une ancienne file`, lancé seul : `AssertionError: expected [ 'retrait', 'accord' ] to deeply equal [ 'accord', 'retrait' ]`. XML `/tmp/diff-front-1-r2-c4-rouge.xml` lu : 1 échec.
- **Constat 5** : test de démarrage existant renforcé, `App.demarrageAccords.test.tsx::R2-C5 : moteur injoignable cinq fois, le cloisonnement non établi arrête l’application`, lancé seul : `Unable to find role="heading" and name "Cloisonnement du profil impossible"`. XML `/tmp/diff-front-1-r2-c5-rouge.xml` lu : 1 échec ; le canevas était monté sans isolation.

### Corrections, appelants et contrôles voisins

1. **Sémantique du volume.** Les alias de `/api/config/stats` sont comparés par `Path.samefile`, donc par l’identité du dossier sur le volume, au lieu de comparer deux résolutions textuelles. La route expose aussi `data_profile_id`, composé du périphérique, de l’inode et de la date de naissance du dossier quand le système la fournit (notamment macOS). Les deux nouveaux tests couvrent une casse insensible simulée au niveau de `stat` et deux dossiers réellement distincts. La simulation permet le rejeu sur ce volume Linux sans supposer sa sensibilité à la casse. Le chemin canonique et le chemin configuré restent disponibles pour leurs consommateurs. Appelants relus : démarrage, statistiques des réglages, contrôle du profil des accords. Premier contrôle direct : 2 tests verts ; contrôle HTTP avec les voisins des accords : 13 tests verts.

2. **Preuve historique du cache et des accords.** Au démarrage, `App` exige l’identité native annoncée par le moteur. Cette valeur devient le marqueur local et la clé de la file des accords ; elle est donc enregistrée avant de créer le cache. Une autre graphie du même dossier garde la même identité. Un lien réorienté change d’identité, déclenche la purge du cache et laisse intacte la file du dossier précédent. Le moteur vérifie cette même identité à chaque décision ou import ; les anciens clients utilisant un chemin restent contrôlés par `samefile`. Une identité native ancienne ne peut pas être validée par la nouvelle cible d’un lien. Les anciennes files identifiées uniquement par un chemin restent conservées à part : une équivalence constatée aujourd’hui ne prouve pas leur cible passée. Cela implique une purge conservatrice des anciens caches lors du premier passage à cette version, y compris si leur chemin ressemble au chemin courant. Aucune identité historique n’est inventée rétroactivement.

   Les six nouveaux cas du constat 2 couvrent le lien sans preuve, l’identité enregistrée puis le lien réorienté, la graphie sans identité annoncée, deux files anciennes qui ne doivent pas être transmises, et le refus côté moteur après réorientation. Le parcours A → B → A conserve et retransmet uniquement le retrait de A avec son identité enregistrée. Appelants relus : `App`, `queueConsentDecision`, `flushConsentDecisions`, `synchroniserConsentements`, `purgeLocalPersistence`, les gardes de l’Atelier et les deux routes d’écriture des accords. Contrôle voisin après correction : 86 réussites, 3 cas des constats suivants exclus à cette étape ; aucun échec.

3. **Espaces significatifs.** La normalisation ne supprime plus les espaces, y compris pour reconnaître le dossier historique. Sans identité native, une réponse d’alias explicite du moteur peut refuser une équivalence lexicale : les barres finales ne passent plus outre ce refus. Trois cas couvrent l’espace final du dossier canonique, les espaces autour du chemin et le refus du moteur. L’ancien cas B-1868 avec ` /tmp/profil-a/ ` a été déplacé tel quel dans un test exigeant désormais une purge ; il ne constituait pas une variante du même dossier. Les autres cas de barres finales et de racine de lecteur restent contrôlés. Appelants relus : entrée `data_dir`/`data_profile` du démarrage, migration historique et sélection des files. Contrôle voisin : 40 réussites, 2 cas du constat 4 encore exclus ; aucun échec.

4. **Ordre des décisions.** La fusion utilise l’ordre de chaque file et les événements communs, sans trier les dates murales. Les identifiants et dates des événements sont conservés et dédoublonnés. Entre un accord et un retrait dont l’ordre n’est pas prouvé, le retrait est placé après l’accord. Si ces contraintes sont incompatibles, la fusion échoue avant toute écriture ou suppression de source. La même fusion s’applique à l’ancienne file globale. Quatre nouveaux cas contrôlent le recul de l’horloge, le retrait concurrent prioritaire, un réaccord explicitement postérieur dans une file et la conservation intacte de files contradictoires. Les tests existants gardent le dédoublonnage, la reprise après changement de profil, la panne d’écriture de destination et l’invalidation d’une relecture en vol. Appelants relus : migration, isolation, purge, vidage et synchronisation. Premier contrôle voisin : 68 tests verts ; les gardes supplémentaires sont comprises dans la porte frontend finale.

5. **Démarrage sans identité.** L’épuisement des cinq tentatives n’ouvre plus le canevas si la dernière tentative n’a pas établi l’identité et effectué l’isolation. Il affiche l’arrêt de cloisonnement existant. Les erreurs passagères gardent leurs tentatives ; l’échec de la seule vérification de mise en route, après isolation, garde son repli existant. Le test de démarrage antérieur a été renforcé : arrêt visible, isolation non appelée, aucun canevas ni assistant. Trois nouveaux cas couvrent l’identité absente de la réponse, la récupération après un échec passager et le repli après isolation réussie. Appelants et états relus : initialisation de l’authentification, état de vérification, écran d’arrêt, synchronisation, assistant et montage du canevas. Contrôle voisin : 39 tests verts.

6. **Contenu de l’intégration rétabli.** Le HEAD de départ est `d5dbaa0b`, tandis que l’intégration locale est `75498edd`. Les commits manquants sont `2dd3d2b1`, `9eb74c5d`, `fcf446a5` et `75498edd`. Après le rouge du rattachement, leur différence a été appliquée uniquement aux fichiers de travail, sans index. Les 24 fichiers concernés sont identiques octet pour octet à cette intégration : ses 13 fichiers de tests absents sont rétablis (20 cas : 11 backend et 9 frontend), ainsi que ses autres correctifs et son bilan. Le rattachement d’une note existante reste présent si le rendez-vous n’a pas encore de projet ; la note reste migrable lorsque ce projet devient connu. Les deux appelants SQL (bootstrap et Alembic) ont été relus, ainsi que les appelants des autres correctifs reportés (mémoire, provenance, vérification de clé, Atelier, formulaire et piège de focus). Premier contrôle : 170 tests backend verts ; les tests frontend rétablis et leurs voisins figurent dans la porte finale.

   **L’historique Git n’a pas été rebasé.** Un rebasage réécrirait les commits et l’index, incompatibles avec l’interdiction explicite de commiter/indexer et les permissions de cette session. Le contenu manquant est prêt dans cet arbre, non commité ; l’orchestrateur conserve la maîtrise de l’historique. Cela corrige la divergence des fichiers constatée, sans prétendre qu’une fusion ordinaire aurait supprimé les commits d’intégration.

### Tests conservés et contraintes de l’environnement

Les constats 1 à 5 ajoutent **17 cas** (3 backend, 14 frontend) et renforcent deux cas préexistants (espaces et démarrage). Les anciens parcours de conservation du cache et de retour A → B → A utilisent maintenant une identité enregistrée, conformément au nouveau contrat ; les nouvelles reproductions couvrent explicitement le refus des anciennes graphies dépourvues de preuve. Les autres assertions de cache, de retrait, de transmission unique et d’absence d’envoi à B restent présentes. Aucun scénario existant n’a été supprimé ni ignoré à la porte finale.

Le TestClient standard restait bloqué avant les assertions dans `anyio`/`asyncio`. Une sonde indépendante de THÉRÈSE (`call_soon_threadsafe` puis attente d’un événement) a reproduit l’absence de réveil inter-thread. Deux lancements ont été interrompus pendant ce diagnostic ; aucun résultat vert n’en est déduit. Pour les tests HTTP locaux, le module temporaire `/tmp/diff_front_1_r2_polling.py` ajoute un réveil périodique à `BaseEventLoop.run_forever` (2 ms lors de la porte finale), sans modifier les routes, fixtures, transports ni assertions. Il est chargé uniquement par `PYTHONPATH=/tmp PYTEST_PLUGINS=diff_front_1_r2_polling`. Le rejeu normal sur une machine dont les réveils de boucle fonctionnent n’en a pas besoin.

Tous les dossiers de données sont jetables sous `/tmp` via `THERESE_DATA_DIR`. Les transports des tests concernés sont simulés ; aucun service ni fournisseur réel n’est lancé. Vitest emploie `--offline --no-install --configLoader runner --no-cache --maxWorkers=3`, sans écrire dans les dépendances partagées. Les liens `.venv` et `src/frontend/node_modules` étaient déjà non suivis au début et n’ont pas été modifiés. Aucun accès réseau, port interdit, profil personnel ou `.app-loop/`, aucun `rm`, `git add`, commit, dépôt annexe ni bundle. Les deux listes exactes de fichiers sont aussi conservées dans `/tmp/diff-front-1-r2-pytest-files.txt` et `/tmp/diff-front-1-r2-vitest-files.txt`.

### Commandes ciblées de la passe 2

Le lanceur temporaire de réveil est le seul ajout d’environnement local aux commandes ci-dessous ; aucun test n’est substitué. Le contrôle final du test de contrat (`-k r2` dans `test_c20_identite_profil.py`) donne aussi **3 réussites**, XML `/tmp/diff-front-1-r2-contrat.xml` lu, après retrait d’un import du nouveau module de production pour préserver la collecte sur la base sans correctifs. Ces trois cas sont déjà compris dans le périmètre backend final.

```sh
THERESE_DATA_DIR=$(mktemp -d /tmp/diff-front-1-r2-XXXXXX) \
  PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 \
  .venv/bin/python -m pytest \
  tests/test_c20_identite_profil.py \
  tests/test_t4_consentement_moteur.py \
  tests/test_c20_b1888_transaction_activites.py \
  tests/test_c20_b1889_notes_heritees.py \
  tests/test_c20_b1890_activites_sans_contact.py \
  tests/test_c20_b1891_reparation_transaction.py \
  tests/test_c20_b1893_provenance_sans_marque.py \
  tests/test_c20_b2009_motifs_ambigus.py \
  tests/test_c20_b2010_limite_cle.py \
  tests/test_c20_b2011_cle_sans_espace.py \
  tests/test_activity_migration.py \
  tests/test_alembic_stamp.py \
  tests/test_b1348_verification_cle.py \
  tests/test_c19d_b1088_securite_memoire.py \
  tests/test_t4_5_provenance_differee.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-front-1-r2.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
cd src/frontend
npx --offline --no-install vitest run \
  src/App.demarrageAccords.test.tsx \
  src/OnboardingRafraichitLeProfil.test.tsx \
  src/lib/profileStorageIsolation.test.ts \
  src/lib/consentSync.profiles.test.ts \
  src/lib/consentSync.test.ts \
  src/lib/consentSync.demarrage.test.ts \
  src/lib/consent.test.ts \
  src/lib/purgeLocalData.test.ts \
  src/lib/debouncedStorage.test.ts \
  src/services/api/core.profil.test.ts \
  src/services/api/core.test.ts \
  src/services/api/core.accordNonEnregistre.test.ts \
  src/hooks/useDialogFocusTrap.horsTabulation.test.tsx \
  src/hooks/useDialogFocusTrap.isolationRacine.test.tsx \
  src/hooks/useDialogFocusTrap.test.tsx \
  src/hooks/useDialogFocusTrap.autofocusHorsPiege.test.tsx \
  src/hooks/useDialogFocusTrap.isolationTardive.test.tsx \
  src/components/atelier/AgentSession.accordMoteur.test.tsx \
  src/components/atelier/AgentSession.profilChange.b2012.test.tsx \
  src/components/atelier/AgentSession.refusDestination.b2013.test.tsx \
  src/components/atelier/AgentSession.refusHttp.b2013.test.tsx \
  src/components/atelier/AgentSession.profils.test.tsx \
  src/components/atelier/AgentSession.consentement.t4.test.tsx \
  src/components/atelier/AgentSession.confirmation.test.tsx \
  src/components/atelier/AgentSession.echapConfirmation.c9.test.tsx \
  src/components/atelier/AgentSession.c9.test.tsx \
  src/components/atelier/AgentSession.avatars.c9.test.tsx \
  src/components/invoices/InvoiceForm.abandonPaiement.b2014.test.tsx \
  src/components/invoices/InvoiceForm.focusAbandon.b2014.test.tsx \
  src/components/invoices/InvoiceForm.pied.c19d.test.tsx \
  src/components/invoices/InvoiceForm.abandonDeSaisie.b1392.test.tsx \
  src/components/invoices/InvoiceForm.focusInitial.test.tsx \
  src/components/invoices/InvoiceForm.focusEtLibelles.c12.test.tsx \
  src/components/invoices/InvoiceForm.soumission.test.tsx \
  src/components/invoices/InvoiceForm.datePaiement.p155.test.tsx \
  src/components/invoices/InvoiceForm.actionsRapides.b1864.test.tsx \
  src/components/invoices/InvoiceForm.test.tsx \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=default --reporter=junit --outputFile.junit=/tmp/diff-front-1-r2-vitest.xml
npx --offline --no-install tsc --noEmit
npm run lint
```

### Portes finales de la passe 2

Les trois rapports XML ci-dessous ont été lus avec `xml.etree.ElementTree`, en comptant les cas, échecs, erreurs et ignorés. Aucun rouge connu n’est présent dans ce périmètre, aucun échec nouveau ni test ignoré. Les vérifications de Ruff, TypeScript et ESLint terminent avec le code 0 ; aucune correction de lint extérieure aux constats n’a été faite.

| Porte | Périmètre | Réussis | Échecs | Erreurs | Ignorés | Preuve |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pytest | 15 fichiers ciblés | 484 | 0 | 0 | 0 | `/tmp/diff-front-1-r2.xml`, code 0 |
| Vitest | 37 fichiers ciblés, 3 workers | 219 | 0 | 0 | 0 | `/tmp/diff-front-1-r2-vitest.xml`, code 0 |
| Pytest, contrôle du contrat | 3 cas déjà compris dans les 484 | 3 | 0 | 0 | 0 | `/tmp/diff-front-1-r2-contrat.xml`, code 0 |
| Ruff | `src/backend tests`, `--no-fix`, relancé après la porte backend | sans objet | 0 | 0 | sans objet | `All checks passed!`, code 0 |
| TypeScript | `tsc --noEmit` | sans objet | 0 | 0 | sans objet | `/tmp/diff-front-1-r2-tsc.log` vide, code 0 |
| ESLint | `npm run lint` | sans objet | 0 | 0 | sans objet | 27 avertissements existants, seuil 27 ; `/tmp/diff-front-1-r2-eslint.log`, code 0 |
| Git | `git diff --check` et index | sans objet | 0 | 0 | sans objet | aucune erreur d’espacement, index inchangé |

Les correctifs, leurs tests et les fichiers d’intégration reportés sont laissés non commités dans cet arbre. Le HEAD reste `d5dbaa0b` et l’intégration locale contrôlée reste `75498edd`. La suite complète et le rejeu contradictoire sans correctifs restent à l’orchestrateur.

## Remédiation de la relecture, passe 3

Départ constaté : `7b941459`, base commune avec l’intégration locale `a498d9d3` : `75498edd`. Les dépendances `.venv` et `src/frontend/node_modules` sont des liens non suivis déjà présents. Aucun index ni historique modifié.

### Rouges isolés avant les correctifs

- **C1** — `profileStorageIsolation.test.ts`, filtre `R3-C1 : garde` (3 variantes, options réelles de `App`) : `AssertionError: Les données anciennes doivent rester récupérables: expected null not to be null`. Preuve : `/tmp/diff-front-1-r3-c1-rouge.xml`.
- **C2** — `consentSync.profiles.test.ts`, `R3-C2 : un retrait ancien bloque la réactivation au démarrage réel puis au rechargement` : `AssertionError: promise resolved "undefined" instead of rejecting`. Preuve : `/tmp/diff-front-1-r3-c2-rouge.xml`.
- **C3** — `consentSync.profiles.test.ts`, filtre `R3-C3` : `AssertionError: promise resolved "undefined" instead of rejecting` au deuxième démarrage de B. Preuve : `/tmp/diff-front-1-r3-c3-rouge.xml`.
- **C4** — `test_c20_identite_profil.py::test_r3_c4_un_inode_reutilise_ne_reprend_pas_l_identite_du_dossier_precedent` : `AssertionError: Un inode réutilisé doit désigner un nouveau profil` (`directory:7:42:0` des deux côtés). Preuve : `/tmp/diff-front-1-r3-c4-rouge.xml`, lu.
- **C4, garde de transition** — deux cas frontend `R3-C4` : `AssertionError: promise resolved "undefined" instead of rejecting` et `AssertionError: the given combination of arguments (null and string) is invalid for this assertion.` La migration de l’ancienne identité numérique doit elle aussi conserver cache et retrait en attente. Preuve : `/tmp/diff-front-1-r3-c4-transition-rouge.xml`.
- **C5** — test rétabli `test_les_deux_nettoyages_epargnent_un_backend_tiers[wmic_absent-wmic_absent]`, puis `test_les_nettoyages_refusent_les_options_ambigues[python-port_repete]`, chacun seul : `AssertionError: assert ['414'] == []`. Preuves : `/tmp/diff-front-1-r3-c5-rouge.xml` et `/tmp/diff-front-1-r3-c5-python-rouge.xml`.
- **C6** — `SplashScreen.relanceDemarrage.b1912.test.tsx`, seul cas `sidecar : relance le moteur et reprend le démarrage` : `TestingLibraryElementError: Unable to find an accessible element with the role "button" and name "Relancer le moteur local"`. Le harnais Rust rétabli échoue aussi seul sur le contrat de génération absent : `AssertionError: error[E0061]: this function takes 4 arguments but 3 arguments were supplied`. Preuves : `/tmp/diff-front-1-r3-c6-rouge.xml` et `/tmp/diff-front-1-r3-c6-rust-rouge.xml`.
- **C7** — `b1854-garde-parcours.test.ts::R3-C7 : laisse les statistiques fournir la vraie identité du moteur jetable`, seul : `AssertionError: expected Object{ status: 200, …(2) } to be 'moteur' // Object.is equality`. Preuve : `/tmp/diff-front-1-r3-c7-rouge.xml`.
- **C8** — contre-épreuve rétablie `test_preuve_refuse_les_evenements_manquants_ou_non_surs[aucun_evenement-openrouter]`, seule : `Failed: DID NOT RAISE <class 'AssertionError'>`. Preuve : `/tmp/diff-front-1-r3-c8-rouge.xml`.
- **C9** — `b1854-garde-parcours.test.ts::refuse les mutations sur les routes bouchonnées`, seul : `AssertionError: expected Object{ status: 200, …(2) } to match object { status: 405 }`. Preuve : `/tmp/diff-front-1-r3-c9-rouge.xml`.
- **C10** — les deux tests rétablis de l’historique : `Error: expect(element).not.toContainElement(element)` et `AssertionError: expected +0 to be 1 // Object.is equality`. Preuve : `/tmp/diff-front-1-r3-c10-rouge.xml` (2 échecs).
- **C11** — test rétabli `App.lienEvitement.b1915.test.tsx`, seul : `AssertionError: expected 0 to be greater than or equal to 50`. Preuve : `/tmp/diff-front-1-r3-c11-rouge.xml`.
- **C2, garde du correctif** — `R3-C2 : une file ancienne illisible suspend les accords sans casser leur lecture`, seul : `SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)`. La lecture des accords doit considérer une file illisible comme ambiguë sans faire tomber l’écran. Preuve : `/tmp/diff-front-1-r3-c2-illisible-rouge.xml`.

### Corrections, appelants et contrôles voisins

1. **Données anciennes conservées.** Avant de retirer les clés actives, `purgeLocalPersistence` copie leurs valeurs brutes dans `therese:unassigned-profile-data`, avec le marqueur antérieur et les contenus du stockage local et de session. Cela inclut les brouillons, `therese-chat` et les stores sans préfixe. Une panne de cette écriture arrête l’isolation avant la purge. Cette réserve survit aux rechargements et aux changements de profil ; l’effacement explicitement demandé par la personne la retire. Aucun rattachement automatique ne se fonde sur la seule résolution actuelle d’un chemin. Les quatre nouvelles variantes de conservation/panne utilisent toutes les options passées par `App` ; une cinquième garde couvre l’effacement volontaire. Appelants relus : démarrage, `PrivacyTab.handleDeleteAll`, désarmement des écritures différées et migration du chat. Premier contrôle voisin : **62 réussites** ; contrôle final de la persistance : **88 réussites** avec les accords et gardes du parcours.

2. **Retrait ambigu prioritaire.** Les files anciennes identifiées seulement par un chemin bloquent désormais la synchronisation et les envois métier du profil natif. Le contrôle intervient avant le vidage, avant chaque décision et avant de publier une réponse GET/import. Les lectures d’accords n’annoncent pas d’autorisation tant qu’une file est ambiguë, y compris si elle est illisible. Le retrait ancien reste intact pendant le démarrage et le rechargement. Les alias constatés aujourd’hui restent insuffisants pour prouver la destination historique : ils ne provoquent pas de fusion automatique. Les deux anciens cas R2-C2 sont renforcés : ils exigeaient un GET malgré une file ambiguë ; ils exigent maintenant un refus et zéro appel, en conservant toutes leurs assertions de non-transmission et de conservation. Trois nouveaux cas couvrent le retrait ancien, le GET tardif et le JSON illisible. Appelants relus : `hasCloudConsent`, `listCloudConsents`, `memoryCardGrantsForRequest`, `viderLesAccords`, `App` et l’Atelier. La première correction affectait les accords avant identification ; la garde est maintenant bornée au profil actif, les tests existants restent verts.

3. **File globale non attribuée.** Le premier passage sans marqueur enregistre durablement `therese:unidentified-consent-outbox`. La purge conserve ce marqueur avec la file. Une identité native apparue après coup ne sert jamais à lui attribuer rétrospectivement un propriétaire. Le nouveau test rejoue trois démarrages de B puis un changement vers C, sans transfert ni réactivation. Appelants relus : les deux appels à `migrateConsentOutbox` (isolation et purge), vidage et synchronisation. Contrôle voisin après correction : **83 réussites**.

4. **Identité durable du dossier.** Le moteur crée exclusivement `.therese-profile-id` dans le dossier de données et y synchronise un UUID. L’identité comprend ce nonce, le périphérique et l’inode : une création successive avec inode réutilisé diffère, une modification de contenu ou un lien vers le même dossier ne diffère pas. Un marqueur incomplet est refusé sans remplacement. Les trois nouveaux cas backend vérifient ces comportements et le refus HTTP 409 de l’ancienne identité. Deux gardes frontend protègent la transition depuis l’ancien identifiant numérique : cache conservé en attente, retrait non réactivé. Le test de volume insensible à la casse simule maintenant aussi les ouvertures de fichier sur ce volume, en gardant ses assertions d’identité. Appelants relus : statistiques et vérification des deux routes d’écriture des accords. Contrôle voisin : **16 réussites backend**, puis **85 frontend** avant les dernières gardes.

5. **Intégration relue rétablie.** Les 12 commits entre `75498edd` et la révision du verdict `a498d9d3` ont été reportés dans les fichiers de travail, sans rebasage ni index. La comparaison finale de ces **37 fichiers** donne **32 identiques octet pour octet**. Les cinq adaptations sont explicites : `App` conserve les correctifs de profil du lot ; son test de lien reçoit ce contrat de démarrage ; le test de garde exécute le vrai parcours sans dépendance Playwright ; le parcours reçoit les statistiques réelles ; le harnais Rust simule aussi `resource_dir()` et l’argument possédé de `env` sous Linux. Les autres corrections et contre-épreuves du lot bancs sont conservées telles quelles, y compris les attentes bornées et le nettoyage des tâches de test. Le nettoyage Windows Rust/Python exige la ligne de commande exacte, sans faire confiance au seul nom `backend.exe`. Appelants relus : lancement du sidecar, point d’entrée Python, commande manuelle, et bancs restaurés de persistance, calendrier, attribution et traitements. Les **37 tests voisins du sidecar et du nettoyage** sont verts dans le XML final.

   Pendant cette passe, `c20/integration` a avancé de `a498d9d3` à `c127023a` (quatre commits du lot instrument : `428c385b`, `4fe2f96b`, `1cb57d8b`, `c127023a`). Cette différence ultérieure porte sur trois fichiers : `docs/qualite/c20-instrument.md` et les deux fichiers `tests/couverture/couverture-ecran.*`. Elle est signalée pour l’intégration par l’orchestrateur ; le report reste borné à la révision citée dans le verdict, sans réviser ce nouveau lot. Aucun raisonnement ne suppose qu’une fusion à trois voies supprimerait les commits d’intégration. HEAD reste `7b941459` et l’index reste inchangé.

6. **Reprise du moteur rétablie.** Le bouton revient après les erreurs de lancement, de port et de délai. Les relances manuelles sont sérialisées et portent une génération ; les anciennes relances différées, terminaisons et notifications sont écartées. Les tests de l’intégration couvrent également double clic, nouvel échec pendant l’IPC et santé tardive. Appelants relus : `SplashScreen`, `restart_backend`, `schedule_sidecar_retry`, `handle_sidecar_termination` et `SidecarStatusBanner`. **47 tests de SplashScreen** réussis ; les simulations Rust rétablies sont dans les 37 cas voisins ci-dessus. Deux erreurs de compilation du double Linux (`path()` absent puis `env` trop restrictif) ont été corrigées dans le harnais, sans toucher au code de production ni réduire les assertions.

7. **Statistiques du parcours.** Le bouchon des statistiques est retiré ; le GET atteint le moteur jetable, dont `App` reçoit réellement `data_profile_id`. L’assertion du scénario Images compare l’accord au marqueur actif fourni par ce démarrage, au lieu du chemin factice. Le nouveau cas R3-C7 exerce la garde réelle du parcours et exige la continuation vers le moteur. Appelants relus : initialisation commune du parcours, contrat de `App` et assertion d’enregistrement de l’accord. Les trois gardes du parcours sont vertes après le correctif suivant.

8. **Preuve de non-fuite.** Le test exige au moins une erreur et parcourt récursivement tous les champs des événements, y compris les arguments d’outil. Les six contre-épreuves de l’intégration sont rétablies. Appelants et producteurs relus : test de frontière, contre-épreuve et flux simulés OpenRouter/Ollama. **45 tests réussis** dans les deux fichiers voisins ; aucun fournisseur réel utilisé.

9. **Garde du parcours.** La méthode est contrôlée avant tout bouchon. Seul le calcul ROI pur est autorisé par la garde à rejoindre le moteur ; le scénario vérifie deux résultats distincts. Le bouchon de génération d’image est limité au scénario qui contrôle son accord. Les deux contre-épreuves rétablies vérifient le refus des mutations et le passage du calcul. **3 tests de garde réussis** avec R3-C7. Les parcours navigateur complets restent hors de cette exécution sans réseau ni ports de service.

10. **Historique accessible.** Ouverture, suppression et confirmation sont des commandes distinctes. La suppression reste visible et sa description accessible désigne la décision. Les deux tests rétablis vérifient structure, clavier, opacité et description. Appelants relus : consultation, suppression, conservation de la décision et gestion d’erreur. **7 tests voisins réussis** ; les autres fichiers BoardPanel sont également verts dans la porte finale.

11. **Lien d’évitement.** La classe complète `focus:z-50` remplace l’interpolation et l’import devenu inutile est retiré. Le test rétabli scanne les sources avec Tailwind et vérifie le z-index calculé au focus. Il utilise les nouveaux champs de statistiques et la collecte des profils. Appelants relus : rendu du lien et cible `main-content` du canevas. **14 tests voisins réussis** avec le démarrage et la fin de mise en route.

### Banc isolé et limites de preuve

Les premières tentatives HTTP ont été interrompues dans le portail de threads de Starlette, avant l’entrée dans l’application. Le même blocage a été reproduit avec un `TestClient(Starlette())` vide : le bac refuse l’écriture sur le socket de réveil d’asyncio. Un module temporaire `/tmp/diff-front-1-r3-pytest/reveil_local.py` remplace uniquement ce socket interne par un tube `os.pipe`, sans modifier les horloges, les transports HTTP en mémoire ni les assertions. Le contrôle de connexion `tests.bancs_sans_reseau` compte **zéro tentative** à la porte finale. Une première variante de réveil périodique a aussi passé les 16 tests d’identité/accords, mais plus lentement ; le rejeu final utilise le tube.

Playwright est absent des dépendances de cet arbre. Le test Vitest de garde transpile et exécute le fichier réel dans une VM, avec les mêmes doubles de dépendances et les mêmes assertions que l’intégration. Les tests Node purs de garde utilisent `/tmp/diff-front-1-r3-node/setup.mjs`, un chargeur qui fournit uniquement un objet `chromium` dont le lancement lève une erreur : aucun navigateur ni service n’est ouvert. Le premier passage backend donnait 136 réussites et un échec d’import Playwright dans la garde Node ; le cas isolé puis le périmètre final complet passent avec ce double. Les deux adaptations temporaires sont extérieures au dépôt et ne changent aucun test métier.

Les tests ajoutés pour C1–C4 et C7 représentent **15 cas**, en plus des contre-épreuves rétablies de l’intégration. Aucun test préexistant n’est supprimé, ignoré ou affaibli. Aucune suite complète, aucun réseau, fournisseur LLM, service sur les ports interdits, accès au profil personnel ou à `.app-loop/`. Aucun `rm`, `git add`, commit, dépôt annexe ou bundle. Les deux liens de dépendances non suivis restent tels qu’au départ.

### Portes finales de la passe 3

Les XML finaux ont été lus avec `xml.etree.ElementTree` : décompte des cas, échecs, erreurs et ignorés, puis vérification qu’il n’en reste aucun en échec. Les lignes des rouges isolés ci-dessus proviennent des journaux et XML également lus.

| Porte | Périmètre | Réussis | Échecs | Erreurs | Ignorés | Preuve |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pytest | 18 fichiers ciblés | 137 | 0 | 0 | 0 | `/tmp/diff-front-1-r3.xml`, sortie 0 |
| Vitest | 49 fichiers ciblés, 3 workers maximum | 254 | 0 | 0 | 0 | `/tmp/diff-front-1-r3-vitest.xml`, sortie 0 |
| Node | garde de couverture, filtre sans navigateur | 1 | 0 | 0 | 0 | `/tmp/diff-front-1-r3-node.log`, sortie 0 |
| Ruff | `src/backend tests`, sans correction automatique | sans objet | 0 | 0 | sans objet | `All checks passed!`, sortie 0 |
| TypeScript | `tsc --noEmit` | sans objet | 0 | 0 | sans objet | `/tmp/diff-front-1-r3-tsc.log`, sortie 0 |
| ESLint | `npm run lint` | sans objet | 0 | 0 | sans objet | 27 avertissements préexistants, sortie 0 |
| Git | espacement et index | sans objet | 0 | 0 | sans objet | `git diff --check`, index inchangé |

Les quatre cas Ollama connus ainsi que la recette Debian sont compris dans les 137 réussites ; aucun rouge connu n’a été retranché du total. Les deux bancs de commandes non concernés ne sont pas lancés.

Commandes de rejeu ciblé depuis cet arbre (les adaptations `/tmp` ne sont nécessaires que dans ce bac sans sockets et sans Playwright) :

```sh
THERESE_DATA_DIR=$(mktemp -d /tmp/diff-front-1-r3-rejeu-XXXXXX) \
  NODE_OPTIONS='--import /tmp/diff-front-1-r3-node/setup.mjs' \
  PYTHONPATH=/tmp/diff-front-1-r3-pytest PYTHONDONTWRITEBYTECODE=1 \
  OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_c20_identite_profil.py tests/test_t4_consentement_moteur.py \
  tests/test_c20_windows_zombies.py tests/test_c20_relance_sidecar.py \
  tests/test_b1261_instance_unique.py tests/test_b954_b955_tueur_de_zombies.py \
  tests/test_sidecar_attend_la_fin_du_processus.py tests/test_frontiere_erreurs.py \
  tests/test_b1851_preuve_frontiere.py tests/test_actions_traitement.py \
  tests/test_b2033_charges.py tests/test_pluriel_fournisseur.py \
  tests/test_b1852_preuve_attribution.py tests/test_r3_4_ollama.py \
  tests/test_b1806_banc_ollama.py tests/test_securite_f2_recette_deb.py \
  tests/test_b1807_recette_deb.py tests/test_b2029_couverture.py \
  -q -p no:cacheprovider -p reveil_local -p tests.bancs_sans_reseau \
  --timeout=120 --junitxml=/tmp/diff-front-1-r3.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
NODE_OPTIONS='--import /tmp/diff-front-1-r3-node/setup.mjs' \
  node --test --test-name-pattern='la garde autorise les lectures' \
  tests/couverture/couverture-ecran.test.mjs
cd src/frontend
npx --offline --no-install vitest run \
  src/App.lienEvitement.b1915.test.tsx src/App.demarrageAccords.test.tsx \
  src/OnboardingRafraichitLeProfil.test.tsx src/components/SplashScreen*.test.tsx \
  src/components/ui/SidecarStatusBanner.test.tsx src/components/board/BoardPanel*.test.tsx \
  src/lib/profileStorageIsolation.test.ts src/lib/consentSync*.test.ts src/lib/consent.test.ts \
  src/lib/purgeLocalData.test.ts src/lib/debouncedStorage.test.ts src/lib/chatPersistence*.test.ts \
  src/services/api/core*.test.ts src/components/atelier/AgentSession.profils.test.tsx \
  src/components/atelier/AgentSession.consentement.t4.test.tsx \
  src/components/settings/PrivacyTab.test.tsx \
  src/components/calendar/CalendarPanel.reconnexion*.test.tsx \
  src/components/calendar/CalendarPanel.reconciliationAvantEvenements.test.tsx \
  src/components/chat/MessageBubble.b1970.test.tsx src/components/chat/MessageBubble.test.tsx \
  src/test/b1854-garde-parcours.test.ts \
  --maxWorkers=3 --configLoader runner --no-cache \
  --reporter=default --reporter=junit --outputFile.junit=/tmp/diff-front-1-r3-vitest.xml
npx --offline --no-install tsc --noEmit
npm run lint
```
