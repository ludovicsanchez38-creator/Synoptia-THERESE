# Revue Soso — la véracité de l'affichage (30/08/2026, passe 5)

> Angle : non plus chercher des pannes, mais des AFFIRMATIONS. Compteurs,
> badges, états, libellés. L'application a le droit de dire « je ne sais pas ».
> Elle n'a pas le droit d'affirmer ce qu'elle n'a pas vérifié.
>
> Trace d'exploration non conservée (2,5 Mo).

# Verdict : NO-GO

L’application présente comme vérifiés des sources, métriques, totaux et disponibilités qui ne le sont pas. Les neuf findings ci-dessous concernent des chemins qui réussissent normalement.

## 1. La recherche approfondie reçoit ses sources, puis les jette

- Fichiers : [chat.py:1071](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/chat.py:1071>), [ChatInput.tsx:849](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/chat/ChatInput.tsx:849>), [CapabilityCenter.tsx:234](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/CapabilityCenter.tsx:234>).
- L’utilisateur croit obtenir une recherche qui « conserve des sources vérifiables » et affiche les sources reçues.
- Il obtient seulement le texte de synthèse. La liste structurée des sources n’est ni affichée ni conservée.
- Chemin exact : le backend construit `sources_data`, envoie un événement SSE `type: "sources"` aux lignes 1073-1091, mais ne sauvegarde que `full_synthesis` en base. La boucle frontend des lignes 849-873 ne traite que `text`, les états de progression et `error` : l’événement `sources` tombe dans aucune branche et disparaît.
- Reproduction : lancer une recherche approfondie, constater que le rapport se termine sans liste de sources, puis recharger la conversation ; seules les données textuelles persistent.
- Pourquoi les passes précédentes ne pouvaient pas le voir : l’appel se termine correctement avec `done`, et seule la traversée de l’événement réussi entre backend, frontend et persistance révèle la perte.

## 2. « Sources web consultées » signifie en réalité « extraits du moteur de recherche lus »

- Fichiers : [board.py:285](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/board.py:285>), [web_search.py:278](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/web_search.py:278>), [BoardConversationCard.tsx:262](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/BoardConversationCard.tsx:262>).
- L’utilisateur croit que le Board a consulté le contenu des pages présentées comme sources.
- Le modèle ne reçoit que le titre, l’URL et le `snippet` renvoyés par le moteur de recherche.
- Chemin exact : `BoardService` appelle `web_search.search()`, copie directement `result.title`, `result.url` et `result.snippet` aux lignes 293-303, puis injecte ces extraits dans le prompt. `web_search.py` parse la page de résultats DuckDuckGo aux lignes 278-316 ; aucun chargement des URL cibles n’a lieu. Le frontend les affiche pourtant sous « Sources web consultées ».
- Reproduction : lancer un Board cloud avec recherche web et observer les requêtes réseau ; le moteur de recherche est interrogé, mais aucune des URL listées dans la décision n’est ouverte par THÉRÈSE.
- Pourquoi les passes précédentes ne pouvaient pas le voir : la recherche réussit et renvoie de vrais résultats, mais un appel isolé ne distingue pas une vignette de moteur de recherche du contenu de la source liée.

## 3. « Tokens générés » compte les morceaux de flux, pas les tokens

- Fichiers : [PerformanceTab.tsx:98](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/settings/PerformanceTab.tsx:98>), [chat.py:2382](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/chat.py:2382>), [performance.py:47](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/performance.py:47>).
- L’utilisateur croit lire le nombre de tokens réellement générés.
- Il lit le nombre d’événements textuels SSE produits par le fournisseur.
- Chemin exact : `chat.py` appelle `stream_metrics.record_token()` exactement une fois par événement `event.type == "text"`, quelle que soit la taille de `event.content`. `record_token()` ajoute simplement 1. Le résultat est exposé comme `total_tokens`, puis affiché sous « Tokens générés ».
- Cela contredit aussi le centre de confiance, qui affirme que seules les consommations réellement mesurées sont présentées comme telles dans [CapabilityCenter.tsx:587](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/CapabilityCenter.tsx:587>).
- Reproduction : comparer l’augmentation de `/api/perf/status.streaming.total_tokens` avec `usage.output_tokens` renvoyé dans l’événement final de la même réponse ; les valeurs divergent dès qu’un morceau de flux contient plusieurs tokens.
- Pourquoi les passes précédentes ne pouvaient pas le voir : le flux termine normalement et seule la comparaison de l’unité métrique avec la granularité des événements révèle le faux comptage.

## 4. « Conversations indexées » affiche le nombre total de conversations SQL

- Fichiers : [PerformanceTab.tsx:195](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/settings/PerformanceTab.tsx:195>), [performance.py:275](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/performance.py:275>), [performance.py:392](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/performance.py:392>).
- L’utilisateur croit voir combien de conversations sont présentes dans l’index de recherche.
- Il voit le nombre de lignes `Conversation` en base.
- Chemin exact : l’API renvoie séparément `search_index.get_stats()`, dont `indexed_conversations`, et `conversations_total`, issu d’un `COUNT(*)`. Le frontend ignore le premier et affiche `conversations_total` avec le libellé « Conversations indexées ».
- Reproduction : conserver des conversations, redémarrer le backend pour vider l’index en mémoire, puis ouvrir Réglages > Performance avant toute réindexation ; l’écran affiche toutes les conversations comme indexées alors que `search_index.indexed_conversations` vaut zéro.
- Pourquoi les passes précédentes ne pouvaient pas le voir : l’endpoint renvoie avec succès les deux nombres, mais le mensonge vient de l’association du mauvais champ au libellé.

## 5. Le SLA est déclaré respecté avant la première mesure

- Fichiers : [performance.py:153](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/performance.py:153>), [PerformanceTab.tsx:103](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/settings/PerformanceTab.tsx:103>).
- L’utilisateur croit que des temps de réponse mesurés respectent le seuil de deux secondes.
- Avec zéro échantillon, la moyenne prend la valeur `0` et `0 < 2000` produit `meets_sla: true`.
- Chemin exact : `get_stats()` fixe `avg_first_token` à zéro quand `_first_token_latencies` est vide, puis calcule systématiquement `meets_sla`. Le frontend transforme ce booléen en badge vert « SLA respecté (< 2s) ».
- Reproduction : redémarrer le backend et ouvrir immédiatement l’onglet Performance sans envoyer de message ; `total_requests` vaut zéro mais le SLA est déclaré respecté.
- Pourquoi les passes précédentes ne pouvaient pas le voir : aucune panne n’intervient, c’est l’absence de mesure qui est interprétée comme une preuve positive.

## 6. Le compteur de messages non lus est plafonné silencieusement aux 30 premiers messages

- Fichiers : [usePrototypeEmailData.ts:58](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/usePrototypeEmailData.ts:58>), [EmailConversationCard.tsx:52](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/EmailConversationCard.tsx:52>), [email.py:796](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/email.py:796>).
- L’utilisateur croit que « N non lus » représente sa boîte de réception.
- Le compteur ne porte que sur une page de 30 messages.
- Chemin exact : le hook appelle `listEmailMessages(..., maxResults: 30)`, ignore toute pagination, puis `EmailConversationCard` compte les non-lus dans ce seul tableau. L’API accepte pourtant un `page_token`.
- Reproduction : avoir plus de 30 messages dans la boîte, marquer les 30 plus récents comme lus et conserver un message plus ancien non lu ; la carte affiche « 0 non lu ».
- Pourquoi les passes précédentes ne pouvaient pas le voir : la première page est chargée et classée correctement, le mensonge n’apparaît qu’en comparant le compteur affiché aux pages volontairement omises.

## 7. Quatre « totaux » d’accueil sont seulement des tailles de pages

- Fichiers :
  - Contacts : [contactsStore.ts:63](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/stores/contactsStore.ts:63>), [ContactsMemoryCard.tsx:74](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/ContactsMemoryCard.tsx:74>), limite serveur dans [memory.py:347](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/memory.py:347>).
  - Devis et factures : [usePrototypeInvoiceData.ts:33](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/usePrototypeInvoiceData.ts:33>), [InvoiceConversationCard.tsx:127](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/InvoiceConversationCard.tsx:127>), limite par défaut dans [invoices.py:201](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/invoices.py:201>).
  - Board : [usePrototypeBoardData.ts:68](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/usePrototypeBoardData.ts:68>), [BoardConversationCard.tsx:85](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/BoardConversationCard.tsx:85>).
  - Agenda : [usePrototypeMeetingData.ts:149](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/usePrototypeMeetingData.ts:149>), [MeetingConversationCard.tsx:102](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/MeetingConversationCard.tsx:102>).
- L’utilisateur croit lire le nombre de contacts, documents, décisions ou événements enregistrés.
- Il lit au maximum 200 contacts, 50 documents, 30 décisions et 50 événements par calendrier sur 90 jours.
- Chemin exact : chaque interface affiche directement `.length` avec un libellé global, sans total serveur ni parcours des pages.
- Reproduction : dépasser l’un des seuils ; par exemple, la 31e décision laisse l’en-tête bloqué à « 30 décisions enregistrées », et le 51e document laisse « 50 documents enregistrés ».
- Pourquoi les passes précédentes ne pouvaient pas le voir : chaque requête réussit et chaque élément reçu est réel, mais seul un regard longitudinal sur le jeu complet révèle que la longueur de page est présentée comme un total.

## 8. « Cloud ou Ollama confirmé » n’est adossé à aucun contrôle de disponibilité

- Fichiers : [ConversationCanvasPrototype.tsx:1767](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:1767>), [usePrototypeBoardData.ts:68](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/usePrototypeBoardData.ts:68>), [board.py:65](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/routers/board.py:65>).
- L’utilisateur croit qu’au moins un moteur capable d’exécuter le Board a été vérifié.
- Le badge est codé en dur dès que le scénario Board est sélectionné.
- Chemin exact : le chargement du scénario ne lit que les 30 dernières décisions et le catalogue statique des conseillers. `/api/board/advisors` renvoie des métadonnées de configuration sans tester une clé cloud, un modèle ou le serveur Ollama. Le badge ne dépend même pas du résultat de ces contrôles inexistants.
- Reproduction : retirer les clés cloud, arrêter Ollama, puis sélectionner le Board sur l’accueil ; « Cloud ou Ollama confirmé » reste affiché.
- Pourquoi les passes précédentes ne pouvaient pas le voir : les lectures locales du catalogue et de l’historique réussissent, alors que la disponibilité externe prétendument confirmée n’est jamais interrogée.

## 9. « Confiance élevée » mesure l’accord entre modèles, pas la fiabilité de la recommandation

- Fichiers : [board.py:872](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/board.py:872>), [board.py:195](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/models/board.py:195>), [BoardConversationCard.tsx:52](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/BoardConversationCard.tsx:52>).
- L’utilisateur croit que « Confiance élevée » qualifie la solidité factuelle de la recommandation.
- Le badge est une auto-évaluation du modèle, explicitement calculée selon le niveau de consensus entre conseillers.
- Chemin exact : le prompt ordonne `confidence = "high"` si le consensus est fort, même sans preuve factuelle. Le schéma vérifie seulement la présence d’une chaîne, puis le frontend transforme `high` en « Confiance élevée » sans préciser « confiance de consensus » ni effectuer de validation contre les sources.
- Reproduction : faire produire aux cinq conseillers le même énoncé non étayé ; une synthèse `confidence: "high"` est acceptée, sauvegardée et affichée comme confiance élevée.
- Pourquoi les passes précédentes ne pouvaient pas le voir : le JSON est valide et toute la génération réussit, seule la comparaison entre la définition donnée dans le prompt et la signification affichée révèle l’affirmation abusive.

Je n’ai pas consulté le dossier d’audits interdit et aucun finding ci-dessus ne reprend la liste fournie.
