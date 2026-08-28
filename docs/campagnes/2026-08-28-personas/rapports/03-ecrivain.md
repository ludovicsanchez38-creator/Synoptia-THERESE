# Rapport - Camille Ferrand, écrivaine

## Mon impression générale

J’ouvre THÉRÈSE pour ranger un roman, pas pour vendre une formation. L’écran me dit « Bonjour. » puis, tout de suite, « Branche tes mails pour que je te prépare la journée », avec un bouton *Brancher mes mails*. En bas, cinq puces : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. *Facturer* est le quatrième geste qu’on me propose. Le champ dit « Demande à Thérèse d’organiser, créer ou agir… ». J’ai créé un espace *Les Cales*, collé mes notes, enregistré Claire, Marc et Inès, posé les dates du contrat. Ça tient. Puis j’ai demandé de la recherche, pas de la prose : elle a cherché sur le web sans me demander, m’a rendu Wikipédia et des chiffres trop ronds, et m’a collé une confiance à 100. Quand j’ai voulu les mots exacts de Claire, le flux s’est coupé. Ensuite plus rien n’a voulu de moi (401). Je n’ai pas demandé d’écrire le livre. Heureusement. Je n’y reviendrai pas pour ça.

## Ce que j’ai réussi à faire

- Lire l’accueil et comprendre, sans clic, que l’outil se voit comme une assistante de *business* (mails, facturation, pipeline).
- Créer le projet *Les Cales* (roman en cours), y mettre des notes de recherche, y joindre un fichier `notes-recherche-marine-1930.md`. Le fichier a été indexé (`chunk_count: 1`).
- Enregistrer Claire Morel (éditrice), Marc Delaunay (agent), Inès Benali (attachée de presse), avec leurs mots dans le champ *Notes*. La fiche *Retrouver* les affiche sous « Notes mémorisées ».
- Poser quatre tâches et quatre jours dans l’agenda local (*Remise manuscrit Les Cales* le 31/01/2027, corrections le 15/03, épreuves le 30/04, point Marc le 15/12/2026).
- Poser une question de recherche documentaire (marine marchande 1930) dans le composeur, rattachée au projet. Réponse en 209 s. Elle n’a pas écrit de roman. Elle a relu mes notes (cambusier, cargo de 4 000 tonneaux, dockers de 1928).
- Ouvrir *Contrôle des données* / *Confidentialité* et lire ce que l’application promet sur le local.

## Ce que je n’ai pas réussi à faire

- Me sentir à ma place dès l’accueil : rien sur un manuscrit, une éditrice, une date de remise. Tout sur les mails, la facture, les prospects.
- Voir mes échéances de contrat sur l’écran d’arrivée. Elles existent dans *Tâches* et *Agenda*, le brief du jour fait comme si je n’avais rien.
- Retrouver le mot *cambusier* par la recherche mémoire, alors qu’il est dans le fichier que je viens de ranger.
- Avoir un historique « qui a dit quoi » comme une correspondance : les notes marchent, la frise d’activités vit dans *Pipeline*, et *Pipeline* ne montre pas les gens que j’ai créés comme contacts.
- Obtenir des sources que je pourrais ouvrir (pas de lien, « FranceArchives », « Wikipédia »).
- Relire les mots de Claire dans la conversation : le deuxième message a cassé le flux, puis le jeton n’a plus passé.
- Être sûre que ma question de recherche n’est allée nulle part : elle est partie en *web_search* sans confirmation.

## Findings

### F1 - Le premier écran me prend pour une commerçante
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : ouvrir l’application. Côté API : `GET /api/dashboard/today` (tout à zéro), `GET /api/dashboard/setup-status` (`has_email: false`, `billing_complete: false`, puis `has_calendar: true` une fois l’agenda local créé), `GET /api/config/profile` (`null`). Côté écran, lu dans `ConversationCanvasPrototype.tsx` (vers 1568-1571, 1768-1785), `lib/etabli.ts` (25-31, 48), `TodayDashboardCard.tsx` (143-173), `SetupChecklist.tsx` (26-44), `CapabilityCenter.tsx` (92-99, 177-193), `onboarding/WelcomeStep.tsx` (56-57).
- **Ce que j’attendais** : en dix secondes, savoir si cet outil peut tenir un roman, des notes, une éditrice. Un verbe du type « ranger » ou « rechercher ». Pas une caisse.
- **Ce qui s’est passé** : titre « Bonjour. ». Phrase : « J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module. » Carte vide : « Branche tes mails pour que je te prépare la journée » / bouton *Brancher mes mails*. Mise en route : *Compléter le profil de facturation* (l’agenda une fois branché disparaît). Cinq puces : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Placeholder : « Demande à Thérèse d’organiser, créer ou agir… ». *Plus d’outils* ouvre un catalogue dont le groupe s’appelle « Développer mon activité » : *Pipeline* (« Suivre prospects, activités et étapes commerciales »), *Devis et factures*. L’accueil d’installation dit : « Ton assistante IA souveraine. Ta mémoire, tes données, ton business. » *Écrire* n’écrit pas un chapitre : ça ouvre un brouillon de mail.
- **Pourquoi ça compte pour moi** : je fuis les logiciels qui me parlent de pipeline. Si le premier geste qu’on me tend s’appelle *Facturer*, je range ça avec les trucs pour auto-entrepreneurs, et je retourne à Scrivener.

### F2 - Mes dates de contrat existent, l’accueil n’en veut pas
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : `POST /api/tasks/` (quatre tâches, projet *Les Cales*, dont *Remise du manuscrit — Les Cales* au 31/01/2027, priorité haute) et `POST /api/calendar/events` sur le calendrier local « Mon calendrier » (même dates, journées entières). Puis `GET /api/dashboard/today` et `GET /api/calendar/events?calendar_id=93d10b66-13d9-4981-9b51-32f1937bfd19&time_min=2026-08-01T00:00:00Z&time_max=2027-12-31T00:00:00Z`.
- **Ce que j’attendais** : voir, quelque part près de « ce qui mérite ton attention », que j’ai un manuscrit à rendre. Pas forcément aujourd’hui : dans cinq mois, c’est déjà une corde au cou.
- **Ce qui s’est passé** : les quatre événements sont bien là (API, 200). Les quatre tâches aussi. Le brief du jour : `events: []`, `urgent_tasks: []`, `summary.tasks_count: 0`. L’écran (`TodayDashboardCard.tsx` 139-160, `dashboard.py` 278-293) ne remonte que le jour même et le retard. À la place : « Branche tes mails… » et *Compléter le profil de facturation*. Titre de carte si tout est vide : « Aucune priorité détectée ». Sous-texte : « Aucune relance, échéance ou rencontre à enjeu n’est remontée. » C’est faux : j’ai quatre échéances. Elles sont juste trop loin pour le logiciel.
- **Pourquoi ça compte pour moi** : un contrat d’édition, ce n’est pas une relance client à J+2. Si l’accueil ne voit que le courrier et les factures impayées, il ne me sert pas à tenir le calendrier du livre.

### F3 - Claire n’est pas un prospect « chaud »
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : `POST /api/memory/contacts` pour Claire Morel (Éditions du Large), Marc Delaunay (Agence Delaunay), Inès Benali. Lu la fiche *Retrouver* (`ContactsMemoryCard.tsx` 78, 243-267) et le panneau *Pipeline* (`CRMPanel.tsx` 38-40, 145-147 ; `PipelineView.tsx` 32-39 et 270-278). `GET /api/crm/pipeline/stats` : `active` moyenne 137,5, `contact` 80.
- **Ce que j’attendais** : trois personnes, un métier à côté du nom, la phrase qu’elles m’ont dite. Comme un carnet.
- **Ce qui s’est passé** : la création *Nouveau contact* demande *Entreprise* (placeholder « Synoptïa ») et *Notes*. Ça va. Ensuite Claire a un `score: 145`, Marc 130, Inès 80. L’infobulle du pipeline dit : « Score de potentiel commercial de 0 à 100 […] Plus il est haut, plus le prospect est chaud. » 145 n’est pas dans 0-100, et Claire n’est pas un prospect. La fiche *Retrouver* affiche « Éditions du Large · active » : *active* est un étage de pipeline, pas un état de contrat. *Pipeline* lui-même ne liste que les contacts avec une `source` (`CRMPanel.tsx` 40) : les miens ont `source: null`, donc 0 personne dans la vue, alors que les stats API en comptent 3. La frise *Nouvelle activité* (libellés *Email* / *Appel* / *Réunion* / *Note*, placeholder « Ex: Appel de suivi, Envoi devis... ») vit là, pas dans *Contacts*. J’ai quand même pu coller les citations dans *Notes*, et `POST /api/memory/search` « manuscrit complet fin janvier Claire » sort bien Claire en premier, avec ses mots.
- **Pourquoi ça compte pour moi** : on ne « score » pas son éditrice. Si je dois passer par un pipeline commercial pour garder qui a dit quoi, je prends un cahier.

### F4 - Mes notes de recherche sont indexées et introuvables
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : API
- **Ce que j’ai fait** :
  1. `POST /api/files/upload` du fichier `notes-recherche-marine-1930.md` sur le projet *Les Cales*. Réponse : `chunk_count: 1`, `scope: "project"`.
  2. `GET /api/files/{id}/content` : le mot *cambusier* est dans le fichier.
  3. `POST /api/memory/search` `{"query":"cambusier cargo mixte 1930","entity_types":["file","project"]}` : deux projets *Les Cales*, **aucun fichier**. Le `content` renvoyé pour le projet est la description (« Deuxième roman, sous contrat… »), pas les notes où *cambusier* est écrit.
- **Ce que j’attendais** : retaper un mot de mes notes et retomber sur la fiche, comme dans un dossier.
- **Ce qui s’est passé** : l’upload a bien copié le fichier dans le dossier du projet et l’a indexé. La recherche mémoire ne le sort pas. Le chat, plus tard, a pourtant recyclé ces notes (il cite le cargo de 4 000 tonneaux et le cambusier). Deux portes, une seule ouverte, et ce n’est pas celle qui s’appelle recherche.
- **Pourquoi ça compte pour moi** : je prends mes notes à la main pour ne pas les perdre. Si je les confie à un logiciel qui les indexe et ne les retrouve pas, je les ai perdues deux fois.

### F5 - La recherche documentaire part sur le web sans me demander, et me rend des sources que je ne peux pas ouvrir
- **Gravité** : bloquant (pour mon usage : je ne fais pas écrire le livre, je documente)
- **Nature** : les deux (`defaut_app` pour le départ non confirmé et l’absence de liens ; `limite_modele_local` pour les chiffres trop sûrs)
- **Source** : les deux
- **Ce que j’ai fait** : conversation `ad1c9968-5655-4237-9671-ea202c6ebecb` rattachée au projet (`PATCH .../project`). `POST /api/chat/send` : « Je n'ai pas besoin que tu écrives à ma place. […] Distingue clairement ce qui est établi de ce qui est incertain, et cite tes sources. […] Ne rédige aucun passage de roman. » SSE, 209 s, HTTP 200. Statut écran : « Execution des outils: web_search... ». `tool_result` : recherche « organisation equipage cargo 1930 France, grades bosco cambusier, sa... ». Aucun événement `confirmation`. `done.uncertainty` : `is_uncertain: false`, `confidence_score: 100`, `should_verify: false`, `provider: ollama`, modèle `qwen3:8b`. Le *Centre de confiance* (`CapabilityCenter.tsx` 586) : « Les parcours raccordés indiquent leur destination et demandent une confirmation avant l’effet externe. » Pied de composeur : « Thérèse affiche les sources reçues et confirme les effets externes effectivement raccordés. » (`ConversationCanvasPrototype.tsx` 1873).
- **Ce que j’attendais** : soit elle cherche dans ce que j’ai déjà, soit elle me dit « je sors sur le web, tu confirmes ? ». Ensuite des sources avec un titre et une adresse, et un « je ne sais pas » dès que ça flotte.
- **Ce qui s’est passé** : elle n’a pas écrit de roman, c’est déjà ça. Elle a repris mes notes. Elle a aussi envoyé ma question (et le mot *cambusier*) à un moteur, sans carte *Créer* / *Annuler*. La réponse range sous « Ce qui est établi » un équipage de « 20 à 25 hommes », une solde de « 100 à 150 francs par mois » « source : *Wikipédia* », un radio obligatoire « à partir de 1920-1925 » « source : *FranceArchives* ». Pas un URL. Le détecteur de doute dit 100. Deux lignes plus bas, le texte lui-même a une rubrique « Ce qui reste incertain ». *Paramètres > Services* : « Recherche Web — Permet aux LLMs de chercher sur le web » (`ServicesTab.tsx` 304-307), interrupteur, pas de consentement dans l’onglet *Confidentialité* (les finalités listées sont messages, documents, dictée, images).
- **Pourquoi ça compte pour moi** : un chiffre faux dans un roman historique, c’est un lecteur qui m’écrit, et un historien qui me recale. Je veux une cote, pas une assurance. Et je ne veux pas que le sujet du livre parte sur un moteur parce que j’ai posé une question.

### F6 - On me dit « tout reste local », ma question de recherche non
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : lire *Contrôle des données* et *Confidentialité*, puis comparer à l’appel de recherche ci-dessus. `GET /api/config/llm` : `provider: ollama`, `model: qwen3:8b`. `GET /api/config/web-search` : `enabled: true`, `has_brave_key: false` (donc DuckDuckGo). Badge accueil : « Données locales » (`HomeHeader.tsx` 57, si on passe par l’ancien accueil) ; bouton *Contrôle des données* (`ConversationCanvasPrototype.tsx` 1451). *Confidentialité* (`PrivacyTab.tsx` 254-256, 418-419) : « Toutes tes données sont stockées localement sur ta machine. Aucune donnée n'est envoyée à un serveur externe (sauf les requêtes aux modèles IA si tu utilises un provider cloud…) » et « Aucun consentement cloud accordé : tout reste local tant que tu n’autorises rien. »
- **Ce que j’attendais** : une phrase vraie au moment où ça sort. Si Ollama est local, le texte reste. Si une recherche web part, on me le dit avant, avec les mots de la requête.
- **Ce qui s’est passé** : le modèle est bien local (le `done` le confirme, `cost_eur: 0`). La recherche web est un autre canal, allumé, hors liste de consentements, hors confirmation. L’onboarding le mentionne quelque part (*Recherche Web* : « Tes requêtes peuvent être tracées », `textes.ts` 47-48). L’écran du jour, lui, me dit que rien ne part. Mes notes, elles, sont bien sur la machine (chemin d’upload dans le dossier du projet).
- **Pourquoi ça compte pour moi** : le manuscrit n’est pas public. Même une question de documentation, c’est déjà le sujet du livre. Si l’écran *Confidentialité* et le geste réel ne disent pas la même chose, je n’y mets pas une ligne.

### F7 - Deux projets *Les Cales*, aucun avertissement
- **Gravité** : mineur
- **Nature** : friction_ux
- **Source** : API
- **Ce que j’ai fait** : un premier `POST /api/memory/projects` (notes avec retours à la ligne), puis un second une fois le formulaire repris. `GET /api/memory/projects` : deux lignes, même nom, mêmes tags, ids `634a4f99-…` et `3fc64040-…`. L’écran *Projets* (`ProjectsPanel.tsx` 127-136) s’intitule *Projets*, bouton *Nouveau projet*, placeholder du nom « Refonte site web » (`ProjectModal.tsx` 313), champ *Budget (€)*.
- **Ce que j’attendais** : un seul espace pour le roman. Si le nom existe déjà, qu’on me le dise.
- **Ce qui s’est passé** : deux cartes. Le formulaire sent le site vitrine (budget, « Refonte site web »). Un projet n’accepte qu’un *Contact associé* : Claire, pas Marc, pas Inès.
- **Pourquoi ça compte pour moi** : un roman, c’est un dossier, pas un chantier à 5 000 €. Je n’ai pas besoin de deux *Les Cales* dans un kanban.

### F8 - Le deuxième échange s’est coupé, puis on m’a fermé la porte
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : API
- **Ce que j’ai fait** : dans la même conversation, `POST /api/chat/send` : « Sans rien inventer : qu'est-ce que Claire Morel, mon éditrice, a dit exactement sur la date de remise du manuscrit ? » Après 26 s : `curl: (18) transfer closed with outstanding read data remaining`. Le SSE ne contient qu’un `generation_id`. `GET /health` répond encore `healthy`. Tous les appels authentifiés suivants (`GET /api/memory/contacts`, `GET /api/chat/conversations/.../messages`, `GET /api/config/llm`) : HTTP 401, `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}`. Je me suis arrêtée. Je n’ai rien relancé.
- **Ce que j’attendais** : les mots de Claire, déjà dans sa fiche. Ou un message d’erreur lisible. Pas un silence puis une porte.
- **Ce qui s’est passé** : plus d’accès à mes contacts, mes dates, la conversation de recherche. L’application est « healthy » pour la machine, morte pour moi.
- **Pourquoi ça compte pour moi** : je n’ai pas un informaticien sous la main. Si ça lâche au milieu d’une phrase sur mon éditrice, je referme, et je n’ouvre plus.

## Verdict

Je ne rouvre pas demain pour écrire. L’outil n’a pas tenté de rédiger *Les Cales*, et c’est la seule chose que je lui reconnais. Il sait ranger un projet, des gens, des dates, à condition d’accepter le vocabulaire d’un commercial et de ne pas compter sur l’accueil. La recherche m’a envoyée sur le web sans me le dire, avec des sources que je ne peux pas vérifier. Quand j’ai voulu les mots de Claire, on m’a débranchée. Scrivener et un cahier me suffisent.
