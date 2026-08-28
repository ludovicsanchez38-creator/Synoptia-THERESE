# Rapport - Julien Ferry, boulanger

## Mon impression générale

J’ai trois minutes le mardi, c’est tout. J’ouvre, et ça me dit *Commencer la configuration*. Six étapes. On me parle de *Multi-LLM*, d’importer un fichier *THÉRÈSE.md*, de *service d’IA*, de clés. Moi je veux noter « Dupont, bûche 8 personnes, 24 à 10 h » pendant que le client est au téléphone. Après, cinq boutons : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Aucun ne dit commande, aucun ne dit farine. Il y a un micro, ça c’est bien, je tape avec deux doigts. Sauf que le micro demande le cloud, et après il dit qu’il manque une clé. Pour une commande, j’ai attendu plus de deux minutes, et le lendemain au comptoir elle n’existait plus. Mon cahier, lui, il est déjà ouvert.

## Ce que j’ai réussi à faire

- Lire l’arrivée. Source interface : `WelcomeStep.tsx` (*Bienvenue sur THÉRÈSE*, *Ton assistante IA souveraine. Ta mémoire, tes données, ton business.*, *Mémoire persistante*, *Données locales*, *Multi-LLM*, bouton *Commencer la configuration*). Six pastilles : *Bienvenue*, *Profil*, *Service d’IA*, *Sécurité*, *Dossier*, *Terminé* (`OnboardingWizard.tsx`). Source API : `GET /api/config/onboarding-complete` → `completed: false`. Profil vide. Je n’ai pas fini ça. En trois minutes, je suis encore dans le formulaire.
- Une fois l’accueil lu (si on passe tout) : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider* (`lib/etabli.ts`). Case *Demande à Thérèse d’organiser, créer ou agir…*. *Mise en route* : *Connecter ton agenda*, *Connecter ta messagerie*, *Compléter le profil de facturation*. Micro intitulé *Message vocal*.
- Poser ma question en une phrase (1 geste, 52 s d’attente). Source API `POST /api/chat/send`. Elle m’a parlé de *projet*, de *budget*, d’*échéances*. Rien de noté.
- Faire noter une commande au chat : « note ca maintenant: madame Dupont, buche chocolat 8 personnes, retrait 24 decembre a 10h » (1 geste, 131 s). Un contact a été créé. Une carte *Confirmer la création du rendez-vous* est apparue, boutons *Créer* et *Annuler*. J’ai cliqué *Créer*. L’événement est bien dans le calendrier local.
- Entrer une deuxième commande à la main, une fois le bouton *Nouveau contact* trouvé : Martin Roux, kouglof, 23 décembre 16 h. Source interface `ContactModal.tsx` (7 champs : *Prénom*, *Nom*, *Entreprise*, *Email*, *Téléphone*, *Notes*, *Tags*). Bouton *Créer*. Environ 9 gestes. Instantané. Source API `POST /api/memory/contacts` HTTP 200.
- Mettre deux fournisseurs dans le même formulaire : *Moulins de Provence* (340 €) et *Minoterie Blanc* (180 €). Même 9 gestes par fiche.
- Chercher « Dupont » et « buche chocolat » dans la mémoire. Source API `POST /api/memory/search` : ça tombe sur la fiche, sous le titre *Dupont Madame*.
- Demander « combien je dois a mes fournisseurs de farine ». Réponse en 51 s : 340 + 180 = 520 €. Ça tombe juste. J’avais déjà les chiffres dans le cahier.

## Ce que je n’ai pas réussi à faire

- Décider en trois minutes si ça me sert. L’écran d’arrivée est une configuration, pas un carnet.
- Noter une commande pendant un appel. Deux minutes d’attente, ce n’est pas un coup de fil, c’est une attente au four.
- Retrouver la commande de Madame Dupont quand elle se présente. Nouvelle phrase, 60 s, réponse : *Aucun contact nommé « Madame Dupont » n'a été trouvé dans la base.* Elle est devant moi.
- Parler à la place de taper. Le micro existe. La voix locale n’est pas là. Le cloud demande Groq. Pas de clé Groq. Message : *Clé API Groq non configurée. Ajoute-la dans les paramètres.*
- Suivre ce que je dois aux minoteries comme des dettes, pas comme des fiches *contact* mélangées aux clients. *Facturer* ouvre *Créer un devis*. Ce n’est pas une facture que je reçois, c’est une facture que j’envoie.
- Gagner du temps. Le cahier me prend 8 secondes. Ici, chaque geste utile m’en a pris 50 à 130.

## Findings

### F1 - En trois minutes je suis encore en train de configurer
- **Gravité** : bloquant
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : j’ai ouvert l’application pour voir si elle me sert. Source API `GET /api/config/onboarding-complete` → pas terminé. Lecture de l’écran d’accueil ensuite.
- **Ce que j’attendais** : une page, un micro, « dis ta commande ».
- **Ce qui s’est passé** : bouton *Commencer la configuration*. Six étapes. *Ton profil* (nom obligatoire, *Surnom*, *Entreprise*, *Rôle*, *Email*, *Localisation*, *Contexte additionnel*, bouton *Importer THÉRÈSE.md*, texte *Ces informations sont injectées dans le contexte de l'IA*). *Choisis ton service d’IA*. Avertissement *Sans clé API, THÉRÈSE ne pourra pas fonctionner. Configure une clé ou utilise Ollama.* Bouton *Configurer plus tard*. Puis *J'ai compris, continuer* sur une liste de risques (*Services d’IA cloud*, *Connecteurs*, *Transcription vocale* : *L’audio est envoyé à Groq*). *Passer* sur le dossier. Si j’arrive au bout : *Bonjour.* (pas de prénom, profil API `null`), pastille *Interface unifiée*, *Espace de travail*, cinq verbes, *Mise en route* agenda / messagerie / *profil de facturation*. En bas : *Parcours réel · confirmation avant effet*.
- **Pourquoi ça compte pour moi** : je n’ai pas d’ordinateur à la maison. Si le premier écran me parle de clés et de LLM, je referme et je retourne au four.

### F2 - Aucun bouton ne dit « commande » ou « fournisseur »
- **Gravité** : bloquant
- **Nature** : friction_ux
- **Source** : interface (`lib/etabli.ts:26-31`, `ConversationCanvasPrototype.tsx:117-125`, `SetupChecklist.tsx:15-45`)
- **Ce que j’ai fait** : j’ai lu les cinq boutons et les titres derrière.
- **Ce que j’attendais** : *Commandes de fêtes*, *Fournisseurs*, ou au moins *Carnet*.
- **Ce qui s’est passé** : *Écrire* = *Consulter mes emails*. *Retrouver* = *Retrouver un contact*. *Préparer* = *Préparer un rendez-vous*. *Facturer* = *Créer un devis*. *Décider* = *Éclairer une décision*. *Plus d’outils* est une icône d’aide (`HelpCircle`) dans le rail. *Voix et transcription* est rangé là-dedans, pas sur l’accueil. Le placeholder dit *organiser, créer ou agir*. Rien sur le pain, rien sur Noël.
- **Pourquoi ça compte pour moi** : je n’ai pas le temps de deviner. Si le mot de mon métier n’est pas écrit, ce n’est pas pour moi.

### F3 - Noter une commande au téléphone prend plus de deux minutes
- **Gravité** : bloquant
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : `POST /api/chat/send` dans la conversation `4f425906-…`, message exact *note ca maintenant: madame Dupont, buche chocolat 8 personnes, retrait 24 decembre a 10h*.
- **Ce que j’attendais** : c’est noté, tout de suite, comme dans le cahier.
- **Ce qui s’est passé** : premier mot à 108 s. Outils `create_contact` puis `create_calendar_event`. Carte à l’écran *Confirmer la création du rendez-vous* (`ToolConfirmationCard.tsx:73`), détails *Événement*, *Début*, *Fin*, *Fuseau*, *Calendrier*, *Fournisseur*, *Lieu*. Boutons *Créer* / *Annuler*. Le texte du chat dit que l’événement *a été créé*, puis *est en attente de validation*. Lieu proposé : *Boulangerie Dupont* (Dupont, c’est la cliente, pas ma boutique). Sans le clic *Créer*, `GET /api/calendar/events?calendar_id=…` reste vide. Total 131 s, plus un clic. Le premier message, lui, n’avait rien enregistré (52 s de conseils).
- **Pourquoi ça compte pour moi** : le client raccroche. Ou je le fais attendre. Mon cahier, c’est une ligne pendant qu’il parle.

### F4 - La commande notée dans le chat disparaît au comptoir
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux (API `POST /api/chat/send` + `execute_read_contact` / `_cloison_contacts` dans `memory_tools.py:297-341`)
- **Ce que j’ai fait** : le lendemain (nouvelle conversation, Madame Dupont est là). `POST /api/chat/send` *madame dupont elle est la, elle vient chercher sa commande, c etait quoi*. Conversation `89f260c3-…`.
- **Ce que j’attendais** : *bûche chocolat 8 personnes, 24 décembre 10 h*.
- **Ce qui s’est passé** : 60 s. Outil `read_contact`. Résultat *found: false*, *suggestions: []*, *Aucun contact trouvé pour « madame dupont »*. Le chat répète *Aucun contact nommé « Madame Dupont » n'a été trouvé dans la base.* Or `GET /api/memory/contacts` a bien la fiche : prénom *Dupont*, nom *Madame*, notes *Bûche chocolat pour 8 personnes, retrait le 24 décembre à 10h*, `scope: conversation` collé à l’ancien chat. Un contact créé par le chat n’est visible que dans ce chat-là. Au comptoir, autre conversation, la commande n’existe plus pour l’assistante. La recherche mémoire hors chat (`POST /api/memory/search` *Dupont*) la trouve, sous le titre *Dupont Madame*. Sur *Retrouver*, la carte s’appelle *Contacts et mémoire*, sous-titre *Fiche locale*, il faut cliquer pour lire les notes (`ContactsMemoryCard.tsx`). Les fournisseurs sont dans la même liste.
- **Pourquoi ça compte pour moi** : si je note le lundi et que je ne retrouve pas le samedi, je sers la mauvaise pièce. Ça, c’est la honte en boutique.

### F5 - Madame Dupont s’appelle *Dupont Madame*
- **Gravité** : majeur
- **Nature** : limite_modele_local
- **Source** : API (`POST /api/chat/send` → `create_contact`, puis `GET /api/memory/contacts/f31a2e87-…`)
- **Ce que j’ai dit** : *madame Dupont*.
- **Ce que j’attendais** : Dupont, ou Madame Dupont.
- **Ce qui s’est passé** : `first_name: "Dupont"`, `last_name: "Madame"`. À l’écran : *Dupont Madame*. `read_contact` cherche la phrase entière dans un seul champ : *madame dupont* n’est dans ni *Dupont*, ni *Madame*, ni *Dupont Madame*. Même sans la cloison, la recherche du chat raterait le nom à l’envers.
- **Pourquoi ça compte pour moi** : au comptoir je dis « Dupont ». Si la machine a écrit à l’envers, je perds du temps devant la cliente.

### F6 - Le micro est là, je ne peux pas parler
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : j’ai cherché à dicter. Bouton micro du composeur, `aria-label` *Message vocal* (`VoiceDictationButton.tsx:69-75`). Statut voix : `GET /api/voice/local/status` → `stt_available: false`, `ready: false`, `enabled: false`. `GET /api/config/` → `has_groq_key: false`. `POST /api/voice/transcribe` avec un petit fichier wav → 400 *Clé API Groq non configurée. Ajoute-la dans les paramètres.*
- **Ce que j’attendais** : j’appuie, je parle, c’est écrit.
- **Ce qui s’est passé** : au clic, si ce n’est pas local, une boîte *Autoriser la dictée cloud ?* (*La transcription envoie ton audio à Groq. Tu peux aussi activer la voix 100 % locale dans Paramètres > Confidentialité.*, *Pas maintenant*, *Autoriser et dicter*). Dans *Paramètres* → *Confidentialité*, titre *Voix locale souveraine* : *La voix locale n'est pas embarquée dans cette version de THÉRÈSE. Mets l'application à jour pour en profiter.* (`VoiceLocalSection.tsx:106-109`). Derrière *Plus d’outils*, *Voix et transcription* : *Importer un enregistrement, le transcrire, puis poursuivre dans le chat.* C’est un fichier, pas un micro de boutique. Et ça transcrirait aussi vers Groq après confirmation.
- **Pourquoi ça compte pour moi** : je tape avec deux doigts, mal, lentement. Sans dictée qui marche, l’écran me coûte plus cher que le cahier.

### F7 - *Facturer* ce n’est pas ce que je dois, c’est ce que je vends
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : j’ai cherché où coller *Moulins de Provence, 340 €* et *Minoterie Blanc, 180 €*. Lecture de *Facturer* / *Créer un devis* (`etabli.ts`, `scenarioLabels`). API `GET /api/invoices/` → `[]`. `GET /api/invoices/billing/profile-status` → incomplet (*raison sociale ou nom*, *SIRET*, *adresse*).
- **Ce que j’attendais** : une liste « je dois ».
- **Ce qui s’est passé** : *Facturer* c’est mes devis à moi. Pour les minoteries, le seul trou c’est *Nouveau contact*, champ *Notes*. Chat *combien je dois a mes fournisseurs de farine* : 51 s, total 520 € juste, puis *Vérifie si ces montants sont à jour via la fonction `search_invoices`*. Les clients Noël et les fournisseurs sont le même tas, filtres *Tout* / *Global* / *Projet* / *Conv.* (`MemoryPanel.tsx:310`).
- **Pourquoi ça compte pour moi** : le comptable me demande ce que je dois. Je n’ai pas besoin d’un devis, j’ai besoin d’une ligne. Et je ne veux pas lire `search_invoices`.

### F8 - Le calendrier de retrait parle de rendez-vous, pas de commande
- **Gravité** : mineur
- **Nature** : friction_ux
- **Source** : interface (`ToolConfirmationCard.tsx:73-110`, `MeetingConversationCard.tsx:138`)
- **Ce que j’ai fait** : après la commande Dupont, la carte à valider, et le parcours *Préparer*.
- **Ce que j’attendais** : *retrait bûche, 24 décembre 10 h*.
- **Ce qui s’est passé** : titre *Confirmer la création du rendez-vous*. *Préparer* ouvre un agenda de *rendez-vous*. État vide : *Aucun rendez-vous à venir*. Le lieu de l’événement créé : *Boulangerie Dupont*.
- **Pourquoi ça compte pour moi** : un retrait de fête, ce n’est pas un rendez-vous. Si ça dit rendez-vous, je clique *Annuler* parce que je n’ai pas demandé ça.

## Verdict

Je ne rouvre pas demain. Trois minutes, et on me configure encore. Deux minutes pour une bûche, une heure plus tard la cliente n’existe plus pour le chat, et je ne peux pas parler. Mon cahier tient le coup. Ce qui déciderait : un micro qui marche tout de suite, une ligne « nom, produit, heure », retrouvée en une seconde au comptoir. Pas cinq verbes, pas de clés, pas d’attente.
