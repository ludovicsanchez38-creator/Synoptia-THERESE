# P-159 : contexte réellement transmis

`messages_relus` compte les messages passés retenus par `send_message` (`chat.py` 1377-1385) : rôles `user` et `assistant`, hors `action-deterministe`, `commande-deterministe` et `extra_data` déterministe, dans `limit(plafond_historique)` (l.1365-1370, de 1 à 200, 50 sinon). Le tour courant n'y entre pas.

Ce tour est ajouté après (`chat.py` 1825 hors flux, 2486-2487 en flux). `prepare_context` (`llm.py` 890-909) copie la liste et appelle `trim_to_fit` (`context.py` 41-46). Le budget vaut `context_window - max_tokens` (`llm.py` 903). L'estimation vaut `len(texte) // 4`, plus 4 par message, prompt système compris (`context.py` 26-37). Tant que le total dépasse le budget et qu'il reste plus d'un message, le plus ancien est retiré.

`messages_transmis` vaut les messages passés encore là après cette coupe : `max(0, len(context.messages) - 1)`, sans dépasser `messages_relus`. Le dernier message gardé est le tour courant. La coupe du texte de ce seul message (`context.py` 54-68) ne change pas les deux comptes.

Hors flux, les deux entiers voyagent dans `ChatResponse.contexte`, champ optionnel. En flux, ils voyagent sur l'événement `done`, à côté de `usage`, et dans `extra_data.contexte` pour le rechargement. Une réponse sans modèle (action locale, message bloqué) n'en porte pas.

Sous la réponse, près de la puce Local ou Cloud : « Contexte : 12 messages relus » si les comptes sont égaux, « Contexte raccourci : 30 messages sur 50 » sinon. Zéro et un s'écrivent « aucun message relu » et « 1 message relu ». Le texte est visible, focusable au clavier, lu par le lecteur d'écran. Aucun réglage nouveau.
