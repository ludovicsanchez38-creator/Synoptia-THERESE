# FULL v2 : revue MAIN et rejeu pur réel

Préparation distincte du canari natif. Auteur de la correction :
`/root/environment_routes` ; revue et rejeu ici : `/root`.

Gel lu : `/private/tmp/therese-c17-full-physical-builder-v2-dxGPne/INDEX.json`,
SHA `2e6fa077f923236cd1a5c87143f2fbd82f1d18f74269e5b6278c9cb825a08659`,
38 532 octets. README et runner lus intégralement MAIN `5c62ef`, quatre
diffs directs code/tests/runner/README lus MAIN `22980d`. La revue v1 avait
déjà lu les corps du constructeur ; aucun nouveau code non relu n'est admis.
Le petit libellé README « six diffs » est inexact : INDEX et revue indépendante
portent bien huit avec les deux sens du README. Le gel n'a pas été réécrit.

Les corrections préparatoires traitent les trois constats v1 : parent
auxiliaire uniquement dans la branche Chrome, ancien brut B1760 gardé hors
de la future ronde (projection de définition seule), origines des quatre
aliases de calibration et seconde source Node tracées. Les diffs ne
qualifient ni G1, ni Chrome, ni l'isolation OS.

Rejeu MAIN réel `16313e`, code 0 :

```text
/Users/synoptia/.local/share/uv/python/cpython-3.13.5-macos-aarch64-none/bin/python3.13 -I -B run_pure.py --actor /root
```

Reçu direct :
`/private/tmp/therese-c17-full-physical-builder-v2-dxGPne/proofs/pure-d7jzy2lq/receipt.json`,
SHA `66872c25bbdee7ed80a1fc29001008a081a6683998fb3998934cce602abd956d`,
66 299 octets. 55 tests, zéro failure/error/skip, sources avant/après égales.
MAIN `d48cf1` réhash les 88 références sources et sinks sans écart.
Le champ acteur est une déclaration CLI ; l'appel outil réel est l'origine
de ce rejeu, pas une autorité OS créée par une chaîne JSON.

Les fixtures Git, signature, Chrome, chemins et enrollments sont synthétiques.
Le runner bloque les appels Popen, socket et os.system ; il ne lance aucun
produit/G1, profil Apple, service ou ronde physique. Les anciennes erreurs
et leurs reçus restent historiques, jamais remplacés par ce passage.

Avis MAIN : favorable pour préparation fermée uniquement. Aucune source
QA actuelle, autorisation physique A/B, admission runtime, naissance de
processus, ronde propre ou release n'est acquise. `MAC_CHROMIUM_TMPDIR`
n'est pas intégré dans ce gel ; v3 est une préparation distincte et doit
faire l'objet de ses propres diffs, contrôles et preuves.
