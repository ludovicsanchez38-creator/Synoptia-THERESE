# Rapport - Philippe Marchand, responsable administratif

## Mon impression générale

Ma fille m’a dit d’essayer « les IA ». J’ouvre THÉRÈSE. Ça dit Bonjour, sans mon prénom. Il y a écrit *Interface unifiée* et *Espace de travail*. Je ne sais pas ce que c’est. En dessous, cinq boutons : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. *Écrire*, ça je comprends. Le reste, je n’y touche pas. Une carte me dit *Branche tes mails pour que je te prépare la journée*. Moi je veux juste un courrier pour Durand, comme dans Outlook. Sur le côté, des petits dessins sans nom. Je n’ose pas. Je cherche *Annuler* : il n’y est pas. J’ai peur de casser quelque chose. Quand j’ai tapé dans la grande case, ça a fini par me pondre un texte. Pour les congés, ça m’a posé trois questions que je n’ai pas comprises. Je suis rentré dans le logiciel. Je n’ai pas l’impression d’avoir fait mon travail.

## Ce que j’ai réussi à faire

- Ouvrir l’application et lire l’accueil. Source interface : `ConversationCanvasPrototype.tsx` (titre *THÉRÈSE*, pastille *Interface unifiée*, *Bonjour.*, *J’ai regroupé ce qui mérite ton attention. Tu peux agir ici, sans chercher le bon module.*), `lib/etabli.ts` (*Écrire* / *Retrouver* / *Préparer* / *Facturer* / *Décider*), `TodayDashboardCard.tsx` (*Aucune priorité détectée*, *Branche tes mails pour que je te prépare la journée*, bouton *Brancher mes mails*), `SetupChecklist.tsx` (*Mise en route* : *Connecter ton agenda*, *Connecter ta messagerie*, *Compléter le profil de facturation*). Source API : `GET /api/config/profile` → `null` ; `GET /api/dashboard/setup-status` → pas de mail, pas d’agenda ; `GET /api/dashboard/today` → tout à zéro.
- Obtenir un modèle de courrier pour Durand Fournitures en tapant dans la case *Demande à Thérèse d’organiser, créer ou agir…* puis en envoyant (2 gestes, 78 s d’attente). Source API `POST /api/chat/send`, conversation `8c9202f2-…`. À l’écran, ça ouvre *Nouvelle conversation* (`PrototypeChatSurface.tsx`).
- Enregistrer deux fournisseurs à la main une fois le bouton *Nouveau contact* trouvé : Sophie Martin (Adecco Intérim Vitrolles) et Pierre Lopez (Aciéries du Midi). Source interface : `ContactModal.tsx` (*Prénom*, *Nom*, *Entreprise*, *Email*, *Téléphone*, *Notes*, *Annuler*, *Créer*). Source API `POST /api/memory/contacts`, HTTP 200. Environ 9 gestes par fiche une fois le formulaire sous les yeux (sans le champ *Tags*).
- Poser ma question sur les congés avec mes mots. Réponse en 58 s. Elle n’a rien cassé, elle n’a rien envoyé.

## Ce que je n’ai pas réussi à faire

- Écrire à un fournisseur comme j’écris dans Outlook. Le bouton *Écrire* ne m’a pas mené à un courrier. Il m’a parlé de Gmail et d’IMAP. Je n’ai pas Outlook dans les choix.
- Revenir en arrière avec un bouton *Annuler*. Sur l’accueil et sur le panneau *Écrire*, ce mot n’existe pas.
- Savoir si Durand a bien été mis dans le carnet. J’ai demandé de noter Jean Durand. Au bout de 2 min 07 s, l’assistante m’a redonné un mail « prêt à être envoyé ». Je n’ai pas vu *enregistré*.
- Relancer les congés du personnel. On m’a demandé de choisir entre trois choses que je ne fais pas (réactiver un congé, créer un congé, réserver une activité).
- Comprendre le bandeau *Documents généraux* au-dessus de la conversation, ni *Plus d’outils*, ni *Espaces de travail*.

## Findings

### F1 - L’accueil me parle une langue que je n’ai pas
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`ConversationCanvasPrototype.tsx:1424-1571`, `lib/etabli.ts:26-30`, `TodayDashboardCard.tsx:138-152`, `SetupChecklist.tsx:25-45`)
- **Ce que j’ai fait** : j’ai ouvert l’application, sans cliquer, et j’ai lu ce qui est écrit.
- **Ce que j’attendais** : un écran simple, du genre « Écrire un courrier », « Carnet d’adresses », « Annuler ». Mon nom, ou au moins un « vous êtes ici ».
- **Ce qui s’est passé** : *Bonjour.* (pas de prénom, le profil API est vide). Pastille *Interface unifiée*. Case *Espace de travail*. Phrase *sans chercher le bon module*. Cinq verbes : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Une carte *Branche tes mails* et une *Mise en route* qui me demande l’agenda, la messagerie et le *profil de facturation*. En bas : *Parcours réel · confirmation avant effet* et *Thérèse affiche les sources reçues et confirme les effets externes effectivement raccordés.* Le rail de gauche, ce sont des icônes sans texte (*Accueil*, *Nouvelle conversation*, *Conversations*, *Espaces de travail*, *Paramètres*, *Plus d’outils* : uniquement `aria-label` / `title`). Le champ dit *Demande à Thérèse d’organiser, créer ou agir…*
- **Pourquoi ça compte pour moi** : je n’ai pas vingt ans, je ne devine pas. Si je ne comprends pas le premier écran, je n’ose plus cliquer.

### F2 - *Écrire* ne me laisse pas écrire à Durand
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Clic 1 : *Écrire* (`chooseScenario('email')`, `ConversationCanvasPrototype.tsx:1213-1216`). L’écran dit alors *Je consulte la boîte connectée. Tu peux lire un message et préparer un brouillon sans l’envoyer.*
  2. Carte *Messages à consulter* : *Aucun compte email connecté*, *Configure Gmail ou IMAP dans la vue Email complète.*, bouton *Configurer Email* (`EmailConversationCard.tsx:113-121`).
  3. Le panneau de droite s’intitule *Lecture et brouillon*, sous-titre *Le message reste en lecture seule.* Le formulaire s’appelle *Brouillon de réponse* (`EmailConversationCard.tsx:316-368`). Champs *À*, *Objet*, listes *Formel* / *Amical* / *Neutre* et *Court* / *Moyen* / *Détaillé*. Boutons *Générer une proposition* et *Enregistrer comme brouillon*. En bas, *Gérer ma messagerie*.
  4. API : `GET /api/email/auth/status` → `connected: false`. `POST /api/email/messages/draft` sans compte → 422 *Field required* (`account_id`). Avec `account_id` vide → 404 *Email account not found*.
  5. Si j’accepte *Configurer Email* : vue *Email*, *Aucun compte email configuré.*, *Configurer un compte* (`EmailPanel.tsx:405-411`). Ensuite *Comment veux-tu connecter ton email ?* avec *Gmail OAuth* (badge *Avancé*) et *SMTP / IMAP classique* (badge *Recommandé*) (`ChoiceStep.tsx:27-109`). Pas d’Outlook. La croix dit *Fermer*, pas *Annuler*.
- **Ce que j’attendais** : une feuille, destinataire, objet, envoyer plus tard. Comme Outlook. Ou au moins un mot que je connais.
- **Ce qui s’est passé** : 1 geste, et je suis coincé. On me parle de Gmail, d’IMAP, d’OAuth, d’un *brouillon de réponse* alors que je n’ai rien à quoi répondre. La confirmation d’enregistrement dit *Confirmer l’enregistrement chez le fournisseur email* (`EmailConversationCard.tsx:461`). Pour moi, le fournisseur, c’est Durand. Je clique *Annuler* tout de suite, j’ai trop peur d’envoyer.
- **Pourquoi ça compte pour moi** : relancer un fournisseur, c’est mon travail de tous les jours. Si le bouton *Écrire* ne le fait pas, le logiciel ne me sert pas.

### F3 - *Générer une proposition* ne fait rien quand on écrit un courrier neuf
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : interface (`EmailConversationCard.tsx:233-234` et `486`)
- **Ce que j’ai fait** : lecture du bouton *Générer une proposition* sur la rédaction ouverte par *Écrire* (`nouvelleRedaction`). La fonction `generateDraft` commence par `if (resource?.status !== 'ready') return;` : sans message reçu, elle s’arrête. Le bouton reste actif, aucun message d’erreur.
- **Ce que j’attendais** : un texte, ou au moins « ça n’a pas marché ».
- **Ce qui s’est passé** : un bouton qui a l’air de travailler, et rien. J’attends, je reclique, je n’ai plus confiance.
- **Pourquoi ça compte pour moi** : je ne sais pas si j’ai mal fait, ou si c’est cassé. Dans le doute, je m’arrête.

### F4 - Je cherche *Annuler* et je ne le trouve pas
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface
- **Ce que j’ai fait** : après *Écrire*, j’ai cherché à revenir en arrière sans casser.
- **Ce que j’attendais** : un bouton *Annuler*, ou *Retour*, écrit en toutes lettres, là où je suis.
- **Ce qui s’est passé** :
  - Le panneau de droite se ferme par une icône *Fermer le canevas* (`ConversationCanvasPrototype.tsx:323-325`). Pas le mot *Annuler*.
  - Le chat se ferme par *Fermer la conversation* (`PrototypeChatSurface.tsx:69`). Pareil, une croix.
  - Le rail a une maison *Accueil*, sans libellé visible. Je n’ose pas : je ne savais pas que c’était l’accueil.
  - *Retour* n’apparaît que si on est déjà dans une vue du genre *Email* ou *Contacts* (`PrototypeUnifiedViewCanvas.tsx:52-55`).
  - L’assistant mail, au premier choix Gmail / IMAP, n’a qu’une croix *Fermer*. *Annuler* n’arrive que plus loin, à l’étape *VerifyStep*.
  - En revanche, le formulaire *Nouveau contact* a bien *Annuler* (`ContactModal.tsx:326`). Là, j’ai osé remplir.
- **Pourquoi ça compte pour moi** : avant de faire quoi que ce soit, je cherche la sortie. Si je ne la vois pas, je ne fais rien.

### F5 - *Plus d’outils* et *Espaces de travail* me demandent de choisir dans le vide
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`CapabilityCenter.tsx:386-397`, `ConversationCanvasPrototype.tsx:1485`, `ProjectsPanel.tsx:127-135`)
- **Ce que j’ai fait** : j’ai regardé le bouton d’aide *Plus d’outils* et le dossier *Espaces de travail*, sans m’y engager jusqu’au bout.
- **Ce que j’attendais** : « Carnet », « Courrier », « Congés ». Trois choses. Pas un catalogue.
- **Ce qui s’est passé** : *Plus d’outils* ouvre *Ce que Thérèse sait mobiliser*, pastille *30 capacités*, colonnes *Je veux…* (*Quotidien*, *Activité*, *Création*, *Décision*, *Automatisation*, *Contrôle*). Champ *Chercher une capacité, un résultat ou un outil…*. Le dossier ouvre une vue *Projets*, bouton *Nouveau projet*. Je ne sais pas ce qu’est un projet dans un ordinateur. Ma règle : dès qu’on me demande de choisir entre des options que je ne comprends pas, je m’en vais.
- **Pourquoi ça compte pour moi** : trop de portes, aucune n’a le nom de mon métier.

### F6 - En tapant dans la case, j’ai eu un courrier, mais pas le mien
- **Gravité** : mineur
- **Nature** : limite_modele_local
- **Source** : API `POST /api/chat/send` (78,4 s, conversation `8c9202f2-…`)
- **Ce que j’ai fait** : après *Écrire*, j’ai tapé : « Bonjour, il faut que j’écrive à un fournisseur, Durand Fournitures, pour relancer une commande de roulements qui n’est toujours pas arrivée. Tu peux m’aider à rédiger le mail ? Je ne veux pas l’envoyer, juste le texte. » 2 gestes (saisie + flèche *Poursuivre dans le chat*).
- **Ce que j’attendais** : un texte que je copie dans Outlook, poli, sans inventer.
- **Ce qui s’est passé** : un modèle *Madame, Monsieur* est sorti, avec objet *Relance commande roulements*. Utilisable. Mais il écrit *Malgré plusieurs rappels* : je n’ai pas dit que j’avais déjà relancé. Il me tutoie dans les conseils (*Espérant ton retour*) et vouvoie dans la lettre. Il y a des crochets `[date]`, `[numéro]`, et un cadre technique. Au-dessus, un menu *Documents généraux* / *Tous les projets* (`ConversationProjectPicker.tsx:150-156`) : je n’y touche pas. Pendant l’attente, l’écran peut afficher *En train d'écrire...* (`ChatInput.tsx:653`).
- **Pourquoi ça compte pour moi** : le texte m’a aidé un peu. Je peux le recopier. Je n’enverrai pas un courrier qui raconte des rappels que je n’ai pas faits.

### F7 - J’ai demandé de noter Durand, on m’a redonné un mail
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : dans la même conversation, « Tu peux noter les coordonnées de Durand Fournitures dans mon carnet ? C’est Jean Durand, téléphone 04 91 00 11 22, mail jean.durand@durand-fournitures.fr. […] Je veux juste les enregistrer, rien envoyer. » Attente 127 s.
- **Ce que j’attendais** : « C’est noté : Jean Durand, Durand Fournitures. »
- **Ce qui s’est passé** : l’API a bien créé une fiche (`create_contact` OK, id `7be3dcee-…`). `GET /api/memory/contacts` la montre : prénom *Jean*, **pas de nom**, société *Durand Fournitures*, mail et téléphone justes, notes *Vendeurs de roulements*, `scope: conversation` (rattaché à ce chat, pas au carnet général). À l’écran, le texte visible dit *Voici le texte de votre email, prêt à être envoyé*. Pendant l’outil, l’activité peut afficher un pictogramme et le retour brut (`ChatInput.tsx:669-671`). Les deux autres fournisseurs, je les ai saisis moi-même via *Nouveau contact* une fois *Retrouver* → *Gérer mes contacts* trouvé : là, *Annuler* est écrit, alors j’ai rempli. *Retrouver* m’a d’abord dit *Lecture seule des fiches réellement enregistrées* (`ContactsMemoryCard.tsx:182`) : je ne savais pas qu’on pouvait ajouter. Les pastilles *Tout* / *Global* / *Projet* / *Conv.* (`MemoryPanel.tsx:300-312`) : je n’y touche pas.
- **Pourquoi ça compte pour moi** : si je demande de noter et qu’on me tend encore un courrier « prêt à être envoyé », je crois que ça n’a pas marché. Et Jean sans son nom, dans un tiroir de conversation, ce n’est pas mon classeur.

### F8 - « Relancer les congés » devient un quiz
- **Gravité** : majeur
- **Nature** : limite_modele_local
- **Source** : API `POST /api/chat/send` (58,3 s, conversation `d3a55bf6-…`), texte lu aussi comme ce que l’interface affiche dans le chat
- **Ce que j’ai fait** : depuis l’accueil, mes mots à moi : « je dois relancer les congés, tu peux m’aider ? » Aucun outil appelé.
- **Ce que j’attendais** : un petit mot à coller dans Outlook pour dire aux 24 de poser leurs congés, ou une liste de ceux qui n’ont pas répondu. C’est ça, relancer les congés, chez nous, en août.
- **Ce qui s’est passé** : *Pour relancer vos congés, je vais d'abord vérifier votre calendrier et vos projets existants.* Elle n’a rien vérifié. Puis trois choix : réactiver un congé déjà planifié ; créer un nouveau congé (dates, durée) ; organiser une activité liée aux congés (ex. réservation, planning). Pas de calendrier branché (`has_calendar: false`). Aucune de ces phrases ne décrit mon travail.
- **Pourquoi ça compte pour moi** : on me demande de choisir. Je ne comprends pas les choix. J’abandonne. Demain, je ferai un mail dans Outlook, comme d’habitude.

## Verdict

Je ne rouvre pas demain. *Écrire* ne m’a pas laissé écrire, *Annuler* n’est pas là quand j’en ai besoin, et pour les congés on m’a interrogé au lieu de m’aider. Le seul moment utile, c’est le texte tapé dans la case, au bout d’une minute, que je peux coller dans Outlook. Outlook, lui, je le connais. Ici, j’ai trop peur d’appuyer au mauvais endroit.
