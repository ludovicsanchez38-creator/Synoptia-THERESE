# Lot M2 (cycle 18) : `gpt-6.1-sol` et le transport Responses

Date : 09/10/2026. Branche `grok/c18-lot-m2`, base `b517daed`.
Aucun appel réel : une fiche ne prouve pas l'accès du compte de Ludo.

## Sources lues avant le code

Fiche modèle, lue en entier le 09/10/2026 :
<https://developers.openai.com/api/docs/models/gpt-6.1-sol>

- Identifiant : `gpt-6.1-sol`. Aucun autre snapshot n'est nommé sur la fiche.
- `reasoning.effort` : `low`, `medium` (défaut), `high`, `xhigh`, `max`.
  `none` et `minimal` ne sont pas acceptés.
- Outils : « Use the Responses API for tool calling. Chat Completions is
  supported without tool calling. »
- Fenêtre : 1 050 000. Sortie max : 128 000. Coupure de connaissances :
  30 avril 2026.
- Tarif texte, par million de jetons : entrée 2,00 $, entrée en cache 0,10 $,
  écriture de cache 2,50 $, sortie 10,00 $. Au-delà de 272 000 jetons d'entrée,
  2× l'entrée et le cache, 1,5× la sortie, sur toute la requête. Fast : 2× le
  standard. Batch et Flex : 50 % de moins. Ultrafast : 6×. Traitement régional :
  +10 % là où il existe.
- Flux et appels de fonction : pris en charge. La fiche ne dit pas « preview »
  ni « beta ».
- Points de terminaison listés : `v1/responses` et `v1/chat/completions`
  (ce dernier sans outils, d'après la phrase citée plus haut).

Guide raisonnement, lu le 09/10/2026 :
<https://developers.openai.com/api/docs/guides/reasoning>

- GPT-6.1 Sol n'accepte ni `none` ni `minimal`, défaut `medium`.
- « Chat Completions does not support function calling with GPT-6 Astra or
  GPT-6.1 Sol. » Le même guide dit que poser `none` sur GPT-6 Astra renvoie
  HTTP 400.
- L'effort part dans `reasoning.effort` (Responses) ou `reasoning_effort`
  (Chat Completions).
- `reasoning.mode` (`standard` / `pro`) existe. Non branché ici : le lot ne
  le demande pas, et le défaut documenté est `standard` quand on omet le champ.
- Rejouer les items de raisonnement est recommandé pour les outils.
  Le code le fait : les éléments `reasoning`, `function_call` et `message`
  reçus dans le tour repartent tels quels avec le résultat d'outil.

Flux et outils, lus le 09/10/2026 :

- <https://developers.openai.com/api/docs/guides/streaming-responses> :
  `stream: true` sur Responses. Événements `response.output_text.delta`
  (champ `delta`), `response.completed`, `error` (champ `message`).
- <https://developers.openai.com/api/docs/guides/function-calling> : outil
  `{type, name, description, parameters}` (à plat, pas sous `function`).
  Item `function_call` (`call_id`, `name`, `arguments` en chaîne JSON).
  Résultat `{type: "function_call_output", call_id, output}`.
  En flux : `response.output_item.added`,
  `response.function_call_arguments.delta` (`delta`),
  `response.output_item.done` (item complet).
- <https://developers.openai.com/api/reference/resources/responses/streaming-events>
  et l'exemple de
  <https://developers.openai.com/api/reference/resources/responses/methods/retrieve> :
  `response.completed` porte `response.usage.input_tokens` et
  `output_tokens`. `response.failed` porte `response.error`.
  Le statut d'une Response peut valoir `cancelled`. Aucun type d'événement
  nommé `response.cancelled` n'a été lu : non documenté comme événement
  distinct, donc pas de lecteur inventé pour ce nom.

## Décisions

1. `gpt-6-sol` reste la tête OpenAI. `gpt-6.1-sol` entre après `gpt-6-luna`,
   avant `gpt-5.6-sol`. Le Board lit la tête : il ne change pas.
   Promouvoir `gpt-6.1-sol` est une question pour Ludo, pas un choix de ce lot.
2. Le transport Responses s'applique aux modèles qui l'exigent pour les
   outils. Ensemble explicite : `gpt-6.1-sol` et `gpt-6-astra`.
   `gpt-6-sol`, `gpt-6-luna` et la famille 5.x restent sur
   `/v1/chat/completions`, y compris la neutralisation `reasoning_effort=none`
   quand des outils sont présents (contrat du 30/08/2026).
3. GPT-6 Astra est migré. Le guide raisonnement dit que Chat Completions
   refuse le function calling pour Astra et pour GPT-6.1 Sol, et que `none`
   renvoie HTTP 400. Correctif retenu (B-1774), pas une question ouverte.
4. Sans outils, `gpt-6.1-sol` reste sur Chat Completions, chemin documenté.
   L'effort résolu (`low` … `max`, `xhigh` compris) part dans
   `reasoning_effort`. `none` et `minimal` ne partent pas : la fiche du
   catalogue est la table `_EFFORT_GPT6`, et une valeur absente de la table
   vaut `None` (rien n'est envoyé). On n'envoie jamais `none` pour « faire
   passer » les outils.
5. Avec outils, `POST /v1/responses` (ou `{base}/responses` si une base est
   configurée, en retirant un suffixe `/chat/completions` déjà collé).
   Corps : `model`, `input`, `stream: true`, `max_output_tokens` borné au
   maximum publié de 128 000 (une config plus haute est ramenée ; une config
   plus basse part telle quelle). Le même plafond borne `max_completion_tokens`
   sur Chat Completions, quand il n'y a pas d'outils. `tools` aplatis,
   `tool_choice: "auto"`
   (champ présent sur l'objet Response de la référence), `reasoning.effort`
   seulement si le catalogue a résolu une valeur. Pas de repli vers Chat
   Completions, pas de second essai qui retire l'effort.
6. `temperature` : la famille `gpt-6` l'omet déjà (`_refuse_le_sampling`).
   La fiche de `gpt-6.1-sol` ne parle pas de `temperature`. On ne la
   réintroduit pas.
7. Historique : on traduit la liste déjà construite par
   `continue_with_tool_results` (messages, tours précédents, tour courant).
   `system` / `user` / `assistant` texte → `{role, content}`.
   Un assistant avec `tool_calls` → un item `function_call` par appel
   (`call_id` = l'id déjà porté par `ToolCall`, qui est le `call_id`
   Responses). Un message `role: tool` → `function_call_output`.
   Le texte écrit avant l'appel n'est pas remis dans le message d'assistant
   porteur d'outils : c'est le contrat BUG-108 du chemin actuel, conservé.
   `previous_response_id` n'est pas utilisé : THÉRÈSE garde la transcription
   elle-même, et aucun identifiant de réponse n'est persisté.
8. Parité des événements `StreamEvent` :
   - texte : `response.output_text.delta` → `type: text` ;
   - appel : à `response.output_item.done` de type `function_call`,
     `type: tool_call` (`id` = `call_id`, arguments JSON parsés, objet vide
     si le JSON est illisible, comme le chemin Chat) ;
   - résultat : le tour suivant, via la traduction ci-dessus ;
   - usage : `response.completed` → `type: done`, `stop_reason` `tool_calls`
     si un appel a été émis, sinon `stop`, jetons `input_tokens` /
     `output_tokens` (absents → `None`) ;
   - `response.incomplete` : `type: done`, `stop_reason` `incomplete`. Le chat
     l'affiche et le garde : « Réponse coupée… ». Ce n'est pas une fin normale ;
   - coupure du flux sans `response.completed` ni `response.incomplete` :
     un `done` de filet, comme Chat Completions quand `[DONE]` manque ;
   - annulation : fermer le générateur sort du `async with client.stream`
     et ferme la requête. Même mécanisme que le chemin actuel. Pas d'événement
     serveur `response.cancelled` inventé ;
   - erreur HTTP : le `except` déjà dans `stream` (message français, corps
     jamais affiché). Erreur SSE `error`, `response.error` ou
     `response.failed` : un `StreamEvent` `error`, pas de `done` derrière.
     `server_error` → `API error: 500`, `rate_limit_exceeded` → la phrase
     429 déjà écrite, le reste → « Requête refusée par le service d'IA. »
     Le message brut du fournisseur va au journal, pas à l'écran.
9. Tarif : `TOKEN_PRICES["gpt-6.1-sol"] = {input: 2.00, output: 10.00}`,
   le standard de la fiche. Au-delà de 272 000 jetons d'entrée, le palier
   (2× l'entrée, 1,5× la sortie) s'applique à chaque appel fournisseur, puis
   les coûts s'additionnent. Le cache, Fast, Flex, Batch, Ultrafast et le
   régional ne sont pas dans ce compteur. `tarif_connu` est vrai. Un modèle
   sans fiche resterait hors grille, jamais à 0 en silence.
10. Écran : repli OpenAI, nom « GPT-6.1 Sol », sans badge « Recommandé »
    ni « préversion » (la fiche ne dit pas préversion). La mention qui
    annonce « l'effort est désactivé dès qu'une conversation utilise des
    outils » ne s'affiche pas pour ce modèle. Phrase à la place :
    « Avec des outils, l'effort que tu choisis est conservé pour ce modèle. »
11. Atelier (`agents/config.py`) : `gpt-6.1-sol` n'est ajouté qu'avec les
    tests du transport (texte, outil puis continuation, usage et coût,
    annulation, erreur). Il n'est pas marqué recommandé. Le défaut des
    agents reste celui d'`agent.json`.

## Hors de ce lot

Accès réel du compte, `reasoning.mode=pro`, `previous_response_id`,
promotion de `gpt-6.1-sol` en tête de liste. La migration d'Astra et le
rejeu du raisonnement sont dans le code.
