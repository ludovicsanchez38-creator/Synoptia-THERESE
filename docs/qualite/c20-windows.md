# Cycle 20 : régressions Windows, B-2056

Travail dans cet arbre, branche `c20/windows`, depuis `3e19a048`.
Le rapport `/tmp/junit-windows-effe9cdb.xml` a été analysé pour les cinq
fichiers : 30 échecs et 8 erreurs, ces dernières concernant l'installation
et le nettoyage de quatre cas paramétrés. Aucun commit ni ajout à l'index.

## 1. Agenda et flux SSE : produit

**Cause exacte.** `src/backend/app/services/ollama_budget.py:9` appelait
`os.sysconf`, absent sous Windows. Son traitement d'`AttributeError`
retournait immédiatement 8 192 jetons, sans mesurer la RAM Windows.
La configuration fictive demandait une fenêtre de 128 000 jetons, mais
`fenetre_ollama` la plafonnait donc à 8 192 sur cette plateforme.

La suppression de `os.sysconf` sur macOS reproduit **exactement les sept
mêmes noms de cas en échec** que le JUnit Windows, sur les 75 cas existants.
Les traces locales identifient deux conséquences distinctes :

- `memory_card_context.py:258`, appelé par `chat.py:3196`, retire des groupes
  d'outils sous ce faux plafond. Quatre cas lèvent ensuite l'assertion du
  faux modèle sur `list_calendar_events` ou `search_emails`. Le traitement
  de `chat.py:3462` transforme cette exception en événement SSE `error`.
- Les trois autres cas atteignent le refus de `borner_payload`, dans
  `memory_card_context.py:168`, via `llm.py:1017`. Ils perdent ainsi le texte
  avant l'appel au modèle. Il s'agit bien d'un chemin produit affecté,
  indépendamment des assertions des faux modèles.

**Correction.** `ollama_budget.py:13` réutilise, lorsque `sysconf` échoue,
le détecteur existant `system_resources.detect_system_memory`. Sa branche
Windows utilise `GlobalMemoryStatusEx` (`system_resources.py:65`). Les
seuils 8/16 Gio et le repli prudent à 8 192 si la mesure reste indisponible
sont conservés. La fenêtre annoncée par le modèle reste un plafond.

**Preuve rouge puis verte.** Les tests ajoutés à
`tests/test_b1797_agenda_sans_outil.py:18` suppriment réellement `sysconf`,
sélectionnent Windows et simulent seulement la mesure native de RAM.
Ils couvrent 4, 8, 16 et 32 Gio, l'échec de mesure, une petite fenêtre modèle,
et un flux HTTP/SSE complet avec les deux morceaux de texte et `done`.
Avant correction : 6 cas, 4 échecs, dont le flux SSE ; après : 6 réussites.
Les 75 cas préexistants passent aussi avec absence de `sysconf` et mesure
Windows simulée de 32 Gio. Aucun bornage ni accord fournisseur n'est désactivé.

**Limite.** L'appel réel à l'API mémoire Windows n'a pas été exécuté sur ce
Mac. La mesure de RAM et la suite complète sur le runner Windows restent
à vérifier par l'orchestrateur. Une machine réellement peu dotée conserve
son plafond prudent et peut toujours refuser un contexte trop volumineux.

## 2. Compagnons PDF et sauvegardes : test

**Permissions.** Les assertions initiales de
`tests/test_b1861_pdf_emis.py:216`, `:282` et `:515` exigeaient partout le
mode POSIX `0600`. Le produit crée le compagnon avec
`O_WRONLY | O_CREAT | O_EXCL`, mode `0o600`, puis écrit explicitement en
UTF-8 (`src/backend/app/routers/invoices.py:507`). La publication utilise
un lien physique (`invoices.py:563`) : elle conserve les droits du fichier.
Le code ne pose aucune ACL Windows privée spécifique sur ce compagnon.
Les droits d'accès Windows dépendent donc des ACL héritées du dossier.

`_verifier_mode_compagnon`, ajouté à
`tests/test_b1861_pdf_emis.py:15`, exige un fichier ordinaire, conserve
l'exigence `0600` sur POSIX, et vérifie les indicateurs lecture/écriture
exposés par `stat` sous Windows. Le commentaire explique explicitement que
ces indicateurs **ne prouvent pas un accès réservé au propriétaire**.
Les assertions de contenu, reprise après interruption, liens physiques,
identité de l'émetteur et refus des PDF modifiés restent exécutées.

**Membre tar.** L'ancienne ligne 346 convertissait le chemin relatif avec
`str(Path)`, donnant des antislashs sous Windows. La sauvegarde produit
appelle `tar.add(..., arcname=...)` avec les racines `invoices`, etc.
(`src/backend/app/routers/data.py:1598`). `TarFile.gettarinfo` de la bibliothèque
standard convertit les séparateurs natifs en `/` : le nom écrit est portable.
C'est la recherche du membre dans le test qui était incorrecte.
La nouvelle ligne 361 utilise `.as_posix()` et conserve `islnk()`.

**Limite.** Le comportement réel des ACL héritées et la restauration NTFS
doivent être rejoués sous Windows. Le produit ne garantit pas ici une
confidentialité équivalente à `0600` sur Windows ; changer ce test n'ajoute
pas une telle garantie. Le chiffrement de la sauvegarde ne protège pas
le compagnon JSON présent dans son dossier d'origine.

## 3. Chargeur Node : test

**Cause exacte.** `tests/test_b2029_couverture.py:57` passait `str(chargeur)`
à `--experimental-loader`. Le chemin `C:\...` est interprété comme un
schéma d'URL ESM non accepté, d'où `ERR_UNSUPPORTED_ESM_URL_SCHEME` dans le
JUnit. La ligne utilise maintenant `chargeur.resolve().as_uri()`.
Le chargeur interdit toujours le lancement de Chromium ; les sept requêtes
restent des objets simulés, sans connexion aux URL ni aux ports cités.
Les assertions sur l'acquittement exact et les six refus sont inchangées.

**Limite.** Le chargeur fonctionne sur le Node du Mac ; la résolution d'une
URL `file:///C:/...` par le Node Windows reste à confirmer en CI.

## 4. Identifiants pytest trop longs : test

**Cause exacte.** Le paramétrage commençant à
`tests/test_c20_b1812_export_config.py:503` utilisait les quatre textes
volumineux comme identifiants implicites. Pytest les recopiait dans
`PYTEST_CURRENT_TEST`, dépassant la limite Windows de 32 767 caractères
pendant l'installation puis le nettoyage de chaque cas.

La ligne 511 donne quatre `ids=` courts. Les textes, l'égalité exacte de
sortie et le seuil de cinq secondes restent identiques.

**Limite.** Les quatre corps de test passent sur macOS. La création des
variables d'environnement par pytest sous Windows sera confirmée en CI.

## 5. Sortie du harnais de relance : test

**Cause exacte.** Les anciennes lignes 154 et 156 de
`tests/test_c20_relance_sidecar.py` décodaient implicitement la sortie avec
`text=True`, puis filtraient les journaux par leur préfixe Unicode
`[THÉRÈSE]`. Le JUnit montre le préfixe mal décodé `[THÃ‰RÃˆSE]` : la ligne
de journal intercalée restait donc dans la liste des états.

Le harnais balise maintenant ses cinq états par `ETAT ` en ASCII. La sortie
est capturée en octets (`:170`) et `_lire_etats` (`:13`) décode uniquement
les charges utiles de ces lignes. L'assertion compare toujours toute la
séquence ordonnée : `1`, `2`, `false 0`, `true 1`, `false`. Aucun tri, aucune
conversion en ensemble, aucune attente supplémentaire. Les diagnostics de
compilation sont lus explicitement en UTF-8.
Trois cas supplémentaires injectent un journal intercalé UTF-8, CP1252 ou
contenant des octets indécodables, avec fins de ligne CRLF.

**Limite.** Le harnais Rust et ses trois branches simulées sont compilés et
exécutés sur macOS ; la création réelle du processus Windows reste à rejouer.

## Portes et preuves locales

Les commandes ont été exécutées sans réseau, fournisseur réel ni ouverture
des ports interdits, avec `OLLAMA_BASE_URL=http://127.0.0.1:9`. Le client
HTTP de test reste en mémoire. Les données sont jetables, sous le répertoire
temporaire imposé par `tests/conftest.py`, sans accès à `~/.therese`.
Le venv préexistant a été référencé localement par `.venv`, sans installation
ni synchronisation ; `PYTHONDONTWRITEBYTECODE=1` évite d'y écrire.
UV utilise `UV_OFFLINE=1 UV_NO_SYNC=1 UV_NO_CACHE=1` pour les portes statiques.

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest \
  tests/test_b1797_agenda_sans_outil.py tests/test_b1861_pdf_emis.py \
  tests/test_b2029_couverture.py tests/test_c20_b1812_export_config.py \
  tests/test_c20_relance_sidecar.py -q -p no:cacheprovider --timeout=120 \
  --junitxml=.pytest_cache/b2056-cinq-fichiers.xml
uv run ruff check src/backend tests
uv run mypy src/backend/app --ignore-missing-imports --no-error-summary \
  --cache-dir=/dev/null | grep -c " error:"
```

| Porte | Résultat vérifié |
| --- | --- |
| Cinq fichiers demandés | 279 réussites, 0 échec, 0 erreur, 0 ignoré |
| Agenda, condition Windows simulée, cas préexistants | 75 réussites, 0 échec |
| Voisins : petite machine et `test_system_resources.py` | 7 réussites, 0 échec |
| Ruff, `src/backend tests` | 0 erreur |
| Mypy à froid | 922 lignes ` error:`, compte attendu ; sortie mypy 1 |
| Diff et index | `git diff --check` propre, index vide |

Les XML et traces restent dans `.pytest_cache/b2056-*`, ignorés par Git :
`b2056-produit-rouge.xml`, `b2056-agenda-sans-sysconf.xml`,
`b2056-sept-erreurs.log`, `b2056-cinq-fichiers.xml`,
`b2056-agenda-windows-simule-vert.xml`, `b2056-voisins-ram.xml`,
`b2056-mypy.log`. Les comptes sont lus dans les XML, le teardown pouvant
couper le résumé console. La suite principale complète et le workflow
Windows ne sont pas annoncés verts à partir de ces seules preuves macOS.
