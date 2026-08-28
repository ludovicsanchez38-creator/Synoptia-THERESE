# Rapport - Dr Hélène Vasseur, médecin généraliste

## Mon impression générale

J’ai ouvert THÉRÈSE entre deux patients, six minutes devant moi, Weda toujours ouvert à côté. L’écran me dit « Bonjour. » puis « Branche tes mails pour que je te prépare la journée », avec des boutons *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Je ne facture pas mes patients dans un logiciel d’entrepreneur, et je n’ai pas de boîte à brancher pour commencer. Le champ du bas dit « Demande à Thérèse d’organiser, créer ou agir… » : ça, au moins, je comprends. J’ai tapé. Ça a marché une fois, pour les associés. Ensuite j’ai attendu une à deux minutes à chaque phrase, on m’a annoncé une réunion déjà posée alors qu’il fallait encore cliquer *Créer*, et quand j’ai redemandé lequel faisait les visites à domicile, on m’a répondu que ce contact n’existait pas. J’ai glissé un nom de patiente pour voir : la réponse sur le stockage est longue, technique, et elle me dit que la base n’est pas chiffrée. Le titre de la conversation, lui, affiche le nom de Mme Palmade. Entre deux consultations, j’aurais fermé à la première attente.

## Ce que j’ai réussi à faire

- Comprendre en trente secondes que l’accueil n’est pas fait pour un cabinet : brief vide, facturation, mails à brancher. (0 clic, lecture de l’écran)
- Enregistrer Marc Pellissier, Claire Benedetti, Julien Roux et Nadine Ortega en **une seule phrase** dans le champ « Message à Thérèse ». (1 geste, 97 s d’attente) Les rôles sont bien dans les notes.
- Poser la réunion trimestrielle du 19 septembre 2026, 12h30-14h, salle de pause, avec l’ordre du jour, **après** avoir cliqué *Créer* sur la carte « Confirmer la création du rendez-vous ». (2 gestes, 98 s d’attente puis un clic)
- Obtenir un texte de courrier de rappel de vaccination, sans nom de patient. (1 geste, 65 s) Je peux le copier. Ce n’est pas un courrier réutilisable dans l’application.

## Ce que je n’ai pas réussi à faire

- Savoir par quoi commencer : l’accueil me pousse vers les mails, l’agenda à « connecter » et le « profil de facturation ». Rien sur un courrier, un associé, une réunion de cabinet.
- Retrouver plus tard, sans le nom, « celui qui fait les visites à domicile ». Dans une conversation neuve, THÉRÈSE m’a d’abord demandé si elle devait chercher (52 s), puis a répondu « Aucun contact n’a été trouvé avec la mention « visites à domicile » » (71 s de plus). J’avais pourtant noté exactement ça.
- Obtenir une réponse claire, vérifiable et vraie sur où va le nom d’une patiente. Le nom de Mme Palmade et le levothyrox sont restés dans l’historique, et le titre de la conversation les affiche.
- Garder le courrier comme modèle réutilisable : pas de fichier Word, pas de modèle enregistré. La bibliothèque de prompts n’a aucun courrier de vaccination (recherche « vaccination » : 0 résultat). Le bouton *Écrire* ouvre une rédaction d’e-mail, pas un courrier papier.

## Findings

### F1 - L’accueil me parle comme à un commercial
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`ConversationCanvasPrototype.tsx` vers 1568-1571, `lib/etabli.ts` 25-31 et 48, `TodayDashboardCard.tsx` 143-153, `SetupChecklist.tsx` 26-44)
- **Ce que j’ai fait** : ouvrir l’application, regarder l’écran d’accueil. Côté API : `GET /api/dashboard/today` (tout vide), `GET /api/dashboard/setup-status` (`has_calendar: false`, `has_email: false`, `billing_complete: false`), `GET /api/config/profile` (`null`).
- **Ce que j’attendais** : en trente secondes, à quoi ça sert pour un cabinet, et un premier geste du type « note un associé » ou « prépare la réunion ».
- **Ce qui s’est passé** : titre « Bonjour. » (pas de nom, profil vide). Sous-titre : « J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module. » Carte : « Branche tes mails pour que je te prépare la journée » / bouton *Brancher mes mails*. Mise en route : *Connecter ton agenda*, *Compléter le profil de facturation*. Cinq puces : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Placeholder : « Demande à Thérèse d’organiser, créer ou agir… ». *Facturer* et la facturation n’ont rien à faire sur mon premier écran. *Retrouver* veut dire « Retrouver un contact », pas mes mails, mais on ne le lit que si on clique.
- **Pourquoi ça compte pour moi** : j’ai déjà laissé tomber deux logiciels pour trop d’écrans. Si le premier écran me parle de devis, je n’y reviens pas.

### F2 - Mes associés sont enregistrés, puis introuvables sans le nom exact
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Une phrase dans `POST /api/chat/send` : enregistrer les quatre personnes du cabinet avec leur rôle. Quatre `create_contact` ont réussi. `GET /api/memory/contacts` les montre, notes correctes, mais `scope: "conversation"` collé à la première discussion.
  2. Plus tard, **nouvelle** conversation : « C'est lequel déjà de mes associés qui fait les visites à domicile ? » Aucun outil. Réponse : elle me demande si je veux qu’elle cherche.
  3. « Oui, cherche. Visites à domicile. » Outil `read_contact` : « Aucun contact trouvé pour « visites à domicile ». » Réponse à l’écran : ce contact n’est pas dans la base.
  4. `POST /api/memory/search` avec la même phrase : Julien Roux sort **en premier**, note « Associé en gériatrie, réalise les visites à domicile ».
  5. Côté écran *Retrouver* : le champ « Rechercher… » (`ContactsMemoryCard.tsx` 210-211) filtre seulement prénom, nom, entreprise, e-mail (`contactMatchesQuery`, `contactsStore.ts` 39-46). Les notes ne comptent pas. La liste affiche « Cabinet médical de Manosque · contact » (le *contact* est un étage de pipeline, pas le métier).
- **Ce que j’attendais** : retaper l’idée (« visites à domicile ») et retomber sur Julien, comme je le ferais en demandant à Nadine.
- **Ce qui s’est passé** : l’enregistrement par le chat range les fiches dans **cette** conversation. `read_contact` ne cherche pas dans les notes, seulement nom / entreprise / e-mail. Une conversation plus tard, l’outil ne les voit plus. La recherche de l’écran *Retrouver* non plus. La recherche mémoire de l’API, elle, trouve. Trois portes, deux fermées, une que je n’ai pas.
- **Pourquoi ça compte pour moi** : je n’enregistre pas des gens pour les perdre au changement de fenêtre. Si je dois me souvenir du nom pour retrouver la note, je n’avais pas besoin de THÉRÈSE.

### F3 - La réunion est « programmée » avant de l’être
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : dans la même conversation, « Prépare la réunion trimestrielle… Mets ça dans l'agenda ». Réponse SSE : `confirmation_required` sur `create_calendar_event`, puis un texte. J’ai ensuite cliqué comme l’écran le demande : `POST /api/chat/confirm-tool` `approved: true`. L’événement n’existait pas avant ce clic (`GET /api/calendar/events?calendar_id=…` : `[]`), et existait après.
- **Ce que j’attendais** : soit c’est dans l’agenda, soit on me demande clairement de valider. Pas les deux.
- **Ce qui s’est passé** : le message dit « La réunion trimestrielle **a été programmée** dans votre calendrier » **et** « Veuillez confirmer si ces informations sont correctes ». En dessous, une carte « Confirmer la création du rendez-vous » avec *Créer* / *Annuler* (`ToolConfirmationCard.tsx` 73-110). Pendant l’attente : « Execution des outils: create_calendar_event... » (`ChatInput.tsx` 666-668). Après le clic : « Evenement cree : **Réunion trimestrielle du cabinet** le 19/09/2026 12:30 » (sans accents). L’événement est bon (participants, ordre du jour, salle de pause). Si j’avais répondu « oui » dans le champ au lieu de cliquer *Créer*, je serais partie en croyant que c’était posé.
- **Pourquoi ça compte pour moi** : une réunion de cabinet ratée, c’est quatre agendas. Je n’ai pas le temps de démêler un passé et un bouton.

### F4 - Un nom de patiente se retrouve en titre de conversation
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : nouvelle conversation, une phrase : Mme Germaine Palmade, consultation manquée, renouvellement de levothyrox, puis « où sont stockées les informations… est-ce que ça quitte le cabinet ? ». Aucun outil. `GET /api/chat/conversations` : titre « J'ai noté que Mme Germaine Palmade n'est pas venue ». Les messages gardent le nom et le médicament. Aucun contact Palmade créé (heureusement). Aucune tâche, aucune relance. `POST /api/memory/search` « Germaine Palmade levothyrox » ne remonte pas cette conversation, seulement les associés.
- **Ce que j’attendais** : soit un refus net d’enregistrer un nom de patient, soit une phrase simple : c’est sur cet ordinateur, chiffré, moi seule, je peux l’effacer d’ici. Et surtout : ce nom ne s’affiche pas dans une liste visible depuis le couloir.
- **Ce qui s’est passé** : le tiroir *Conversations* (`PrototypeConversationDrawer.tsx` 191 et 261) reprend le début du message comme titre. Nadine ou un associé qui passe derrière l’écran lit le nom et le motif. Dans *Paramètres > Confidentialité*, le tableau dit que les « Conversations IA » sont conservées « Illimitée (locale) » avec la justification « Pas de données personnelles tierces » (`PrivacyTab.tsx` 50). C’est faux dès que je tape un nom de patiente. L’écran *Confidentialité* dit aussi : « Toutes tes données sont stockées localement… sauf les requêtes aux modèles IA si tu utilises un provider cloud » (254-256). Le *Centre de confiance* : « Données métier conservées localement ; secrets protégés par le trousseau système. » Rien n’empêche de coller un dossier médical dans le chat. Rien n’offre d’effacer **cette** phrase en un geste depuis la réponse.
- **Pourquoi ça compte pour moi** : ligne rouge. Aucune donnée de patient ne sort du dossier. Ici elle ne « sort » peut-être pas du Mac, mais elle s’affiche, elle se garde sans fin, et l’écran me dit qu’il n’y a pas de données personnelles. Je ne peux pas laisser ça dans le secrétariat.

### F5 - La réponse « où c’est stocké » est fausse sur le chiffrement
- **Gravité** : majeur
- **Nature** : limite_modele_local
- **Source** : les deux (réponse API du chat ; vérité produit dans l’interface et la doc de l’app)
- **Ce que j’ai fait** : la question ci-dessus, même appel. J’ai lu la réponse, puis l’onglet *Confidentialité* et le *Centre de confiance*.
- **Ce que j’attendais** : une phrase que je peux vérifier dans l’écran *Confidentialité*, sans jargon.
- **Ce qui s’est passé** : le chat (52 s) : « stockées **100 % localement**… `~/.therese/` (base SQLite + index vectoriel Qdrant) ». Puis : « La base SQLite n'est **pas chiffrée au repos** », secrets Fernet, « Seul **vous** et **votre administrateur système** », « **Aucune donnée ne quitte votre machine** (sauf si un modèle cloud est activé) », « Aucun serveur externe… 🛡️ ». L’onglet *Confidentialité* ne dit pas que la base est en clair. Le README / l’écran de bienvenue parlent de données locales, et la documentation sécurité du produit affirme un chiffrement SQLCipher AES-256. Les deux récits ne vont pas ensemble. Pendant ce test le modèle était Ollama local (`GET /api/config/llm` : `ollama` / `qwen3:8b`) : les phrases n’ont pas quitté la machine **cette fois**. Si quelqu’un passe un modèle cloud plus tard, le même onglet le dit, le chat de ce jour-là ne m’a pas expliqué comment le voir. Vocabulaire de tutoiement dans l’app, vouvoiement dans la réponse.
- **Pourquoi ça compte pour moi** : je ne vais pas ouvrir SECURITY.md. Si l’assistante me dit « pas chiffré » et l’écran ne me le confirme pas, je n’ai plus confiance, dans un sens ou dans l’autre.

### F6 - Le courrier type n’est pas un courrier, et *Écrire* n’écrit pas ça
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : « Rédige un courrier type de rappel de vaccination, à réutiliser. Sans aucun nom de patient. » `GET /api/prompts/library/search?q=vaccination` : 0. `GET /api/personalisation/templates` : `[]`. Aucun fichier généré (`skill_file` absent).
- **Ce que j’attendais** : un texte à en-tête, enregistré, que Nadine réouvre et imprime. Idéalement un Word.
- **Ce qui s’est passé** : un message dans le chat (65 s, 1506 caractères). Pas de patient, bien. Mais une rubrique « Prestations incluses » (consultation personnalisée, mise à jour du calendrier, « prise en charge des rappels ou des rappels ») qui sonne comme une plaquette commerciale. Des crochets `[Site web]`. Note finale : « imprimé ou envoyé par email ». Rien n’est enregistré hors de cette conversation. Sur l’accueil, *Écrire* ouvre une rédaction de mail (`ConversationCanvasPrototype.tsx` 237, scénario `email` : « Consulter mes emails »). *Plus d’outils* (bouton d’aide du rail, `ConversationCanvasPrototype.tsx` 1506) cache une bibliothèque de relances clients et de prospection, pas un courrier de cabinet. Le slash `{action: produire docx "…"}` existe dans un menu `/` que je n’ouvrirai pas.
- **Pourquoi ça compte pour moi** : Nadine a besoin d’un papier dans le bac, pas d’un bubble de chat à scroller. Si *Écrire* veut dire e-mail, qu’on l’écrive.

### F7 - Pendant l’attente, l’écran me parle en nom d’outil
- **Gravité** : confort
- **Nature** : friction_ux
- **Source** : interface (`ChatInput.tsx` 666-671, `chat.py` statut « Execution des outils: … »)
- **Ce que j’ai fait** : les envois ci-dessus. Chaque action utile a pris 52 à 98 secondes (modèle local : je ne mets pas ça sur le dos de l’application).
- **Ce que j’attendais** : « J’enregistre tes associés… » / « Je prépare le rendez-vous… »
- **Ce qui s’est passé** : « Execution des outils: create_contact, create_contact, create_contact, create_contact... » puis « Récap réel : 4 contact(s) créé(s). » Pour l’agenda : « Execution des outils: create_calendar_event... ». Les résultats d’outil passent dans l’indicateur avec un pictogramme clé à molette (`🔧 ${chunk.content}`). L’indicateur de frappe dit aussi « Réflexion... » (`TypingIndicator.tsx` 42).
- **Pourquoi ça compte pour moi** : je n’ai pas six minutes, et encore moins six minutes à lire `create_contact`. Si ça doit attendre, que ça attende en français.

## Verdict

Je ne rouvre pas ça demain. Weda reste pour le médical ; pour le reste, un document Word et le calendrier mural iront plus vite que deux minutes d’attente et un bouton *Facturer* sur l’accueil. Ce qui déciderait : que mes associés restent trouvables la fois d’après, qu’un nom de patient ne devienne jamais un titre de conversation, et qu’on me dise en une phrase vérifiable, la même que dans *Confidentialité*, où ça vit. Tant que *Créer* et « c’est déjà programmé » cohabitent, je n’y mets pas l’agenda du cabinet.
