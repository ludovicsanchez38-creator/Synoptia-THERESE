# Revue SQL de MAIN11, préparation instrument seulement

Acteur lecteur : `/root`. Racine examinée :
`/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3`.

Le contrat `complements/contrats-normalises-proposes.json` a été lu
intégralement par MAIN, résultat outil `9c24df`.
SHA-256 attendu :
`f53d7e7159cf81b473a3b47a202e24ab841b18c922152d4b0f20beeb2b9d0c4e`.
La définition historique `fe8cdc0f…` reste distincte et non réécrite.

Périmètre conservé : checkout QA historique
`2d69e30c9c6dd18823ee6102271876003a6a67cc`, 36 sources et modes déclarés,
deux groupes B1753/B1760. Le contrat conserve ses champs
`root_reviewed=false`, `root_review_required=true` et
`prepared_unreviewed_no_execution_claim` : cette note externe constate
une lecture et ne réécrit pas la préparation pour fabriquer une admission.

Relations B1753 : registre et tâches de fond vides à la fin du premier
test et au début du suivant, sans changer les assertions du produit.
Relations B1760 : dix nouveaux exports liés nodeid/UUID/HTTP/persistance/PDF,
échéance cohérente dans l'en-tête et la première ligne automatique, ancienne
échéance absente, suffixe personnalisé et conditions conservés, contenu émis
immuable. SQLCipher réel reste requis pour le harnais ; le runtime plaintext
n'en constitue pas la preuve.

Les environnements déclarés dans `wrapper_blueprint.py`, lu par MAIN
(`f731dd`), isolent HOME, données et sorties SQL dans cette racine QA,
désactivent le keyring, les services externes et les téléchargements.
Les trois groupes SQL et sélecteurs restent fermés. Les valeurs de revue
passées aux enfants portent ce même SHA, acteur et identifiant de racine.

Cette lecture ne qualifie ni SQLCipher exécuté, ni les cinq calibrations,
ni la Session/RPC réelle, ni les contrôles B1753/B1760, ni deux rondes
produit. Aucune exécution native n'a encore eu lieu au moment de cette note.
L'appel outil MAIN exact et les autres contrôles de pré-lancement restent
nécessaires. FULL, A/B et release restent fermés.
