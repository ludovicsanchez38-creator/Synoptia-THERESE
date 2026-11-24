# Perplexity. Passage au protocole Agent API

Le moteur 0.84 envoie `model`, `messages` et `stream` à `/chat/completions`, puis lit les fragments `choices`. Le banc HTTP strict vérifie que ce client n’atteint pas le contrat Agent API. Le témoin historique conserve un flux Chat Completions lisible. Perplexity documente la reformulation de certaines demandes synchrones et en flux depuis la fin du support Sonar du 27 septembre. Le comportement du compte de Ludo reste à mesurer. [Guide de migration Perplexity](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview).

## Contrat à implémenter

1. Ajouter à l’adaptateur Perplexity la sérialisation de l’historique dans `input` et du niveau publié dans `effort`. Transformer une préférence `sonar-pro` lors de l’appel selon la correspondance officielle `fast`, en laissant l’ancienne préférence relisible.
2. Réutiliser les conversions existantes au format Responses si les évènements Agent API les acceptent. Cartographier les types `message`, `search_results`, les fragments, la fin du flux et l’usage constaté. Conserver les références et les erreurs visibles dans le chat. Vérifier les fonctions et leur continuation avant de les déclarer compatibles.
3. Conserver le consentement par fournisseur et la destination d’envoi. Rejouer une réponse textuelle, des résultats de recherche, une erreur, une annulation et un tour multi-échange avec HTTP simulé. Tester ensuite le chemin réel avec un compte autorisé, selon la grille de prix en vigueur.

Report pour la 0.85. Une simple substitution d’URL laisserait les champs d’entrée et de sortie dans le format historique.
