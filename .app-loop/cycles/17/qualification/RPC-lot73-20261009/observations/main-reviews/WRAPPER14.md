# WRAPPER14 : revue MAIN préparatoire

INDEX auteur lu MAIN `974077` :
`/private/tmp/therese-c17-wrapper14-chromium-tmp-SYH6Mx/INDEX.json`,
SHA `e135223b023a771e3080f7ecb280ad350098783afbeeb5133d3221b6880ed7e6`,
14 704 octets. README/runner/diffs/tests lus MAIN `dee246`, `e2d9b8`,
`a06015` ; contrats autorité/build lus `dd595f`.

Delta limité : racine future `187602c6…`, cinq environnements Chrome avec
MAC_CHROMIUM_TMPDIR égal à leur TMPDIR QA, garde validate_environment
restreinte à cette racine, mode Chrome et cinq stages fermés. Les
ensembles globaux ENV et profil Chrome SHA2ec/2499 octets restent intacts.
Les quatre autres modes/environnements et les délais n'ont pas de nouveau
droit. Cette préparation ne prouve pas le comportement de Chrome154.

Rejeu réel MAIN `802797`, session88041, terminal `16fa28` code0 :
23 tests en 4,850 s, 18 sources avant/après égales, zéro tentative OS,
G1 non importé, constructeur et natif non appelés. ROOT a exécuté la suite
sous gardes unittest.mock (Popen/run/socket/system/execve/kill), sans lancer
run_pure.py qui code l'acteur auteur en dur. Le champ de cet autre reçu
n'a donc pas été réétiqueté. Les sorties réellement retournées par les deux
outils sont la preuve de ce rejeu ; aucun sink complet fictif n'est créé.

Les rouges historiques, y compris les préimages des tests et du runner,
restent des observations de leurs versions exactes. La revue/checker externe
doit les joindre de façon bornée, jamais accepter un SHA historique comme
SHA actuel d'un fichier modifié. Aucune admission native/FULL/release ici.
