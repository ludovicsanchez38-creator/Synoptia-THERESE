# WRAPPER13 : préparation et revue distinctes

Revue indépendante de la proposition d’Environment favorable pour une préparation uniquement. PLAN 0956da6b74598f64639c4dd491cdaf21378247b14316a5ac7e2084cd018529e9, 4918 octets. Quinze références physiques rehashées, SHA et tailles exacts ; les quatre diffs forward/inverse ont été reconstruits byte-exacts. Le dossier natif futur était absent lors de cette lecture.

## Proposition revue

Le profil MAIN12 de 2 439 octets reçoit exactement les 60 octets suivants :

```scheme
(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))
```

Il est byte-exact au profil getconf préparé. Aucun droit réseau, écriture, lecture data, délai, autre Mach ou IOKit n’est ajouté. Les 35 fonctions du builder hors `future_root` et `checked_chrome_successor` sont identiques à l’AST de MAIN12. Ces deux différences bornent une seule racine et vérifient la chaîne MAIN11 → MAIN12 → dirhelper. Zéro fonction ajoutée ou retirée. Les contrôles historiques IPS restent inchangés.

Les dix tests purs d’Env ont été lus dans le vrai log bb83fcc7 ; ils n’ont pas été rejoués par le relecteur. MAIN a indiqué son propre rejeu 1c8b53 de dix cas en 0,333 s, distinct de la transcription auteur. Aucun de ces faits n’admet Chrome.

## Checker préparé par le relecteur

Le checker `verify-prepared-wrapper13.mjs` est dérivé du MAIN12 a626e401, intégralement lu et préservé sous `preimages/`. Quinze ancres uniques sont documentées ; leur inversion reproduit exactement les octets d’origine. Nouveau pin : 834caa7e1988ca2502cd4978ad3b67488c2be270a89dbc94b183b1571a2ea2f1, 29121 octets.

Les changements sont la racine 8612, les pins builder/proposition/profile, les libellés correspondants et la vérification explicite MAIN12 + dirhelper, byte-exact à getconf. Le champ de provenance lie aussi les index MAIN12 et getconf. Les contrôles 79 sources, Git 3 579, SQL 36, sorties 11/8/28/18, cinq Chrome, délais 50/5/8, historique V2 rouge et trois exceptions Apple exactes demeurent. Les blocs non ciblés du texte original sont conservés.

HEAD documentaire exigé : d1486c2ad1d1879b1c10196fe269e16b35b85e6e, vérifié fraîchement par MAIN selon son retour outil 9ce380. Le checkout produit historique reste 2d69e30c9c6dd18823ee6102271876003a6a67cc. Aucune autorité MAIN12 n’est promue : l’autorité13 et son observation réelle doivent être créées séparément par /root puis liées par la construction.

Ce checker n’a pas été lancé. Aucune vérification syntaxique via Node, construction, import G1, native, Chrome, service ou décision n’a eu lieu ici. Une première erreur de mon outil de lecture, KeyError('files'), est consignée dans le reçu ; elle ne concernait pas le produit et la lecture corrigée a utilisé le vrai champ `refs`.

Commande future, à exécuter par MAIN seulement après sa revue et sa construction exactes :

```sh
node /private/tmp/therese-c17-wrapper13-static-controls-rbBJ653M/verify-prepared-wrapper13.mjs /private/tmp/therese-c17-wrapper-canary-8612f55886284332a3ac6a7bc9615021
```

Avis limité à la préparation. Le retour natif ROOT12 reste rouge, la causalité du fatal Chrome n’est pas déduite du différentiel getconf, et aucune admission A/B FULL ou release n’est prononcée.
