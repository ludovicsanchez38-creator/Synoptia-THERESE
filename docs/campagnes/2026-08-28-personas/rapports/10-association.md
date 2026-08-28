# Rapport - Sylvie Ranc, directrice d'association

## Mon impression générale

J’ouvre et on me dit *Bienvenue sur THÉRÈSE*, *Ta mémoire, tes données, ton business.* Je dirige Table Ouverte, une association loi 1901 d’aide alimentaire. Trente bénévoles, deux contrats aidés, 180 000 euros dont 70 % de subventions. Pas un client, pas une facture à envoyer, pas un centime pour un logiciel. Le premier formulaire me demande mon *Entreprise*. Les cinq boutons du milieu disent *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. *Facturer*, chez nous, ça n’existe pas. Quand je lui parle, elle comprend que je ne vends rien. Quand je clique, tout est écrit pour une petite entreprise : *Pipeline*, *prospect chaud*, *Proposition commerciale*, *SIRET (requis pour facturer)*. Je peux m’en servir en traduisant dans ma tête, comme je le fais déjà sur les portails de la Région. Ça me fatigue. Et nulle part on ne me dit que c’est gratuit.

## Ce que j’ai réussi à faire

- Lire l’arrivée. Source interface : *Bienvenue sur THÉRÈSE*, *Ton assistante IA souveraine. Ta mémoire, tes données, ton business.* (*WelcomeStep.tsx:53-57*). Six étapes d’installation. *Ton profil* : *Nom complet*, *Surnom*, *Entreprise* (placeholder *Ton entreprise*), *Rôle*, *Email*, *Localisation*, *Contexte additionnel* dont l’exemple parle d’une offre à 490 € HT (*ProfileStep.tsx:171-232*). L’avertissement de sécurité dit *Ne partage jamais de données sensibles (mots de passe, secrets, données clients)* (*onboarding/textes.ts:27*). Source API : `GET /api/config/onboarding-complete` → `completed: false`.
- Remplir le profil (1 formulaire). Source API `POST /api/config/profile`. J’ai mis *Association Table Ouverte* dans *Entreprise*, *Directrice* dans *Rôle*. Enregistrement OK. Dans *Paramètres*, le même champ s’appelle encore *Entreprise*, placeholder *Synoptïa*, rôle *Entrepreneur IA*, plus *Adresse (facturation)*, *TVA intracommunautaire*, *SIRET (requis pour facturer)*, *N° de déclaration d'activité (organisme de formation)* (*ProfileTab.tsx:259-372*).
- Lui dire qui je suis. Source API `POST /api/chat/send`, conversation `10f2ae6e-…`. Premier mot à 58 s, 77 s au total. Elle a répondu *Vous pilotez une association loi 1901*, *Aucun client, aucun chiffre d’affaires*, *180 000 €, dont 70 % de subventions*. Ça, c’est juste. Ça vient du texte que j’ai collé dans le profil, pas des boutons.
- Préparer le dossier mairie. 8 fiches contacts à la main (prénom, nom, *Entreprise*, notes, *Tags*). 1 projet *Subvention fonctionnement mairie 2026*, budget 25 000 €, contact Marie Blanc. 1 tâche *Deposer dossier subvention mairie*, échéance 15 octobre. Source API `POST /api/memory/contacts`, `/api/memory/projects`, `/api/tasks/`. Puis le chat (170 s) : plan de pièces et d’échéances. Puis *Documents* → *Nouveau document* → *Générer la trame* (*OutlineTree.tsx:212*). 14 sections : *Présentation de l'association*, *Budget prévisionnel*, *Rapport d'activité*, *Statuts*, *Liste du conseil d'administration*, *RIB*. Ça ressemble à un vrai dossier.
- Tenir une liste de bénévoles. Quatre fiches (Monique, Karim, Hélène, Jean-Pierre) avec les créneaux dans les notes et le tag `benevole`. La recherche mémoire *benevole mercredi distribution* (*POST /api/memory/search*) sort Monique et Hélène en tête. Le chat, 73 s, me dit *Monique Fabre : Disponible mercredi de 9h à 12h* et qu’Hélène est *en arrêt en août*. Deux créneaux posés dans *Mon calendrier* (local) : *Distribution alimentaire* le 2 septembre 9 h-12 h, *Tournees camionnette* le 1er septembre.
- Rédiger un compte rendu de CA. *Nouveau document*, titre *Compte rendu du conseil d administration du 20 aout 2026*, bouton *Générer la trame* (90 s), puis *Rédiger* sur *Décisions prises* (56 s). Le paragraphe vote le dépôt mairie, me charge des relances, valide le planning de septembre, fixe l’AG au 12 novembre. Ton de procès-verbal. Utilisable.
- Faire rédiger trois courriers de relance, sans les envoyer. Chat, 151 s. Trois brouillons (département, Région, DDCS). Aucune carte *Confirmer l’envoi de l’email* (*ToolConfirmationCard.tsx:73*). Je n’ai rien expédié.

## Ce que je n’ai pas réussi à faire

- Me reconnaître dans les mots de l’écran. Il faut traduire *client* / *Entreprise* / *Pipeline* / *Facturer* à chaque clic.
- Inscrire un bénévole comme participant d’un créneau. *Participants*, placeholder *email1@example.com, email2@example.com* (*EventForm.tsx:383-393*). Source API : `Adresse participant invalide : Monique Fabre`. Mes bénévoles n’ont pas tous un mail, et je n’ai pas à leur en inventer un.
- Poser une relance de financeur comme une relance. *Relances et alertes* existe, mais `POST /api/follow-ups` exige un *email_message_id*. Sans boîte : `Email message not found`. Brouillon mail : `Email account not found`. Le brief du jour, vide, me dit *Branche tes mails pour que je te prépare la journée* (*TodayDashboardCard.tsx:143-154*).
- Brancher la messagerie. *Connecter ta messagerie* (*SetupChecklist.tsx:36*). L’écran : *Gmail OAuth* tampon *Avancé* (OAuth PKCE, projet Google Cloud) ou *SMTP / IMAP classique* tampon *Recommandé* (*ChoiceStep.tsx:63-112*). Je n’ai ni informaticien ni mot de passe d’application. Je ferme.
- Faire disparaître *Compléter le profil de facturation*. Source API `GET /api/invoices/billing/profile-status` → `missing: ["SIRET","adresse"]`. Je n’émets pas de devis.
- Savoir si c’est gratuit. Aucun libellé *gratuit* sur l’accueil, ni dans *À propos*. Le mot *payant* apparaît pour Groq (*ServicesTab.tsx:292*). Pour une asso à 180 k€, le prix est éliminatoire : si je dois demander un devis, je n’ouvre plus.
- Me fier aux dates du plan mairie sans tout relire : elle a inventé *Avant le 15 août 2026* alors que je n’ai donné que le 15 octobre. Dans un courrier, l’adresse de Claire Aubert est devenue *sylv.roy@tableouverte.asso.fr*.

## Findings

### F1 - L’écran me parle comme à une entreprise
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`WelcomeStep.tsx:57`, `lib/etabli.ts:26-31`, `ConversationCanvasPrototype.tsx:117-125`, `CapabilityCenter.tsx:99-198`, `ContactModal.tsx:215-268`, `guided/actionData.ts:91-92`, `DocumentCreateModal.tsx:160`, `onboarding/textes.ts:27`)
- **Ce que j’ai fait** : j’ai lu l’accueil, le profil, les cinq boutons, le centre de capacités, le formulaire *Nouveau contact*, *Nouveau document*.
- **Ce que j’attendais** : adhérents, bénévoles, financeurs, dossier de subvention, compte rendu d’AG. Des mots de loi 1901.
- **Ce qui s’est passé** : *ton business.* Cinq verbes : *Écrire* (titre derrière : *Consulter mes emails*), *Retrouver* (*Retrouver un contact*), *Préparer* (*Préparer un rendez-vous*), *Facturer* (*Créer un devis*), *Décider*. Groupe *Développer mon activité* : *le cycle commercial de bout en bout*. Carte *Pipeline* : *Suivre prospects, activités et étapes commerciales*. Carte *Livrables et suivi client*. Champ *Entreprise*, tags *client, prospect, partenaire*. Placeholder du document : *Proposition commerciale - Client X*. Modèle tout prêt : *Proposition commerciale* pour *[client/projet]*. J’ai quand même réussi à travailler, en traduisant.
- **Pourquoi ça compte pour moi** : chaque euro de subvention est justifié. Si l’outil m’appelle *Entreprise* et mes financeurs *clients*, je ne peux pas le montrer au CA. On croirait que je commercialise l’aide alimentaire.

### F2 - Au premier geste, elle m’a fermé la porte sans le dire
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux. API `401 {"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` sur le jeton du brief. Interface : `core.ts:93-110` charge le jeton une fois (`initializeAuth`), `core.ts:144` le pose, aucune reprise sur 401. Le bandeau *Le moteur local redémarre* (*SidecarStatusBanner.tsx:41*) ne recharge pas le jeton.
- **Ce que j’ai fait** : `GET /api/config/profile` avec le jeton qu’on m’avait donné. Puis, comme je relancerais le logiciel, `GET /api/auth/token` (c’est ce que fait l’écran au démarrage) et le nouveau jeton a marché.
- **Ce que j’attendais** : ouvrir, remplir, travailler.
- **Ce qui s’est passé** : d’abord *Token de session invalide ou manquant*. Rien à l’écran qui m’explique de fermer et de rouvrir. Le journal du moteur dit qu’il a été relancé à 14:05:41 et qu’un nouveau jeton a été écrit. Si je n’avais pas « redémarré », j’aurais cru que le logiciel ne voulait plus de moi.
- **Pourquoi ça compte pour moi** : je n’ai pas un informaticien sous la main. Un message rouge illisible, je range et je reviens à LibreOffice.

### F3 - Mes bénévoles ont un « score de potentiel commercial »
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux. Interface `PipelineView.tsx:32-39` et `:274` (*Score de potentiel commercial de 0 à 100 […] Plus il est haut, plus le prospect est chaud.*). Colonnes *Contact*, *Découverte*, *Proposition*, *Signature*, *Livraison*, *Actif*, *Archive*. API `GET /api/crm/pipeline/stats` → 8 contacts, tous en `contact`, `avg_score` 71,875. Marie Blanc (mairie) score 95. Paul, Claire, Nadia (financeurs publics) 80. Monique, Karim, Hélène, Jean-Pierre (bénévoles) 60.
- **Ce que j’ai fait** : j’ai créé les fiches, puis j’ai ouvert *Pipeline* (*PrototypeUnifiedViewCanvas.tsx:19*, titre d’écran *Pipeline*).
- **Ce que j’attendais** : une liste de personnes, avec un rôle (bénévole, financeur, membre du CA).
- **Ce qui s’est passé** : tout le monde est un *contact* du même tuyau commercial. La mairie est le « prospect » le plus chaud. Les bénévoles du mercredi sont à 60. Le brief du jour a un tiroir *stale_prospects* et un libellé *Relancer {nom}* (*prototypeReadModels.ts:137*).
- **Pourquoi ça compte pour moi** : un bénévole n’est pas un prospect. Un instructeur DDCS n’est pas une signature de devis. Si un élu voit ça sur mon écran un jour de permanence, je m’explique.

### F4 - Je ne peux pas mettre un bénévole sur un créneau sans son e-mail
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux. Interface *Participants*, *Séparez les emails par des virgules* (*EventForm.tsx:383-393*). API `POST /api/calendar/events` avec `attendees: ["Monique Fabre"]` → `VALIDATION_ERROR`, *Adresse participant invalide : Monique Fabre*. Le même appel sans participants passe (événement `4181f23d-…`, *Distribution alimentaire* le 2 septembre).
- **Ce que j’ai fait** : fiche Monique (pas d’e-mail, c’est voulu), puis créneau mercredi 9 h-12 h.
- **Ce que j’attendais** : cocher Monique et Hélène sur la distribution, comme sur la feuille volante du local.
- **Ce qui s’est passé** : refus. Les noms tiennent seulement dans *Description*. Le planning existe, la présence non.
- **Pourquoi ça compte pour moi** : le mercredi matin, j’ai besoin de savoir qui est là, pas qui a une adresse Gmail.

### F5 - Relancer un financeur exige une boîte mail déjà branchée
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux. Carte *Relances et alertes* : *Création depuis un email* (*CapabilityCenter.tsx:164-167*). API `POST /api/follow-ups` `{email_message_id, due_date}` → *Email message not found*. `POST /api/email/messages/draft` → *Email account not found*. `GET /api/email/auth/status` → `connected: false`. Brief vide : *Branche tes mails pour que je te prépare la journée*, bouton *Brancher mes mails* (*TodayDashboardCard.tsx:143-154*). *Mise en route* : *Connecter ta messagerie* (*SetupChecklist.tsx:36*).
- **Ce que j’ai fait** : trois financeurs muets (12 juin, 3 juillet, 20 mai). J’ai voulu une relance, pas un Gmail.
- **Ce que j’attendais** : une date, un nom, un brouillon, comme un pense-bête.
- **Ce qui s’est passé** : sans IMAP/OAuth, pas de relance dans l’outil. Le chat m’a bien écrit les trois lettres (voir F8). Je ne peux pas les garder dans *Écrire*, ni les retrouver dans *Relances*.
- **Pourquoi ça compte pour moi** : les portails de subvention, je les déteste déjà. Ajouter *Gmail OAuth*, *OAuth PKCE* et *projet Google Cloud* (*ChoiceStep.tsx:63-74*), c’est un autre métier. *SMTP / IMAP* *Recommandé* demande un mot de passe d’application. Je n’ai personne pour ça.

### F6 - On me pousse à facturer
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux. *Mise en route* : *Compléter le profil de facturation* (*SetupChecklist.tsx:40-44*). API `GET /api/invoices/billing/profile-status` → `is_complete: false`, `missing: ["SIRET","adresse"]`. Bouton d’accueil *Facturer* → *Créer un devis* / *Facturer un client* (*InvoiceConversationCard.tsx:127*, *ConversationCanvasPrototype.tsx:123*). Vue *Devis et factures* (*InvoicesPanel.tsx:168*). Formulaire *Client \**.
- **Ce que j’ai fait** : j’ai ouvert l’accueil après le profil. La checklist restait là, à côté de *Connecter ta messagerie*.
- **Ce que j’attendais** : qu’on me lâche avec les subventions.
- **Ce qui s’est passé** : tant que le SIRET et l’adresse de facturation manquent, l’écran me doit encore un devoir. Une association a un SIRET, oui. Elle n’a pas à ouvrir *Nouveau devis* pour exister.
- **Pourquoi ça compte pour moi** : 70 % de notre budget est de l’argent public. Facturer un « client », ce n’est pas notre objet social.

### F7 - La trame du CA a doublé les chapitres
- **Gravité** : mineur
- **Nature** : limite_modele_local
- **Source** : API `POST /api/documents/07855ab5-…/outline` (90 s). Interface bouton *Générer la trame* (*OutlineTree.tsx:212*), badge *Sans trame* puis *Rédaction* (*DocumentsList.tsx:84*).
- **Ce que j’ai fait** : *Nouveau document*, brief de CA du 20 août, *Générer la trame*.
- **Ce que j’attendais** : les points de l’ordre du jour, une fois.
- **Ce qui s’est passé** : 15 sections. Les bons titres sont là (*Ordre du jour*, *Budget 2026 et trésorerie*, *Dossiers de subventions*, *Planning des bénévoles*, *Recrutement des contrats d'aide*, *Date de l'assemblée générale*, *Décisions prises*). Puis les six derniers sont recopiés. *Rédiger* sur *Décisions prises* a donné un vrai paragraphe de PV (56 s). Les *PISTES:* sont parties à part (2 pistes), le texte du PV est resté propre.
- **Pourquoi ça compte pour moi** : un compte rendu d’AG, le préfet peut le demander. Doubler les chapitres, c’est de la relecture en plus. Le fond, lui, était le bon.

### F8 - Les courriers de relance, je dois tout relire au mot près
- **Gravité** : majeur
- **Nature** : limite_modele_local
- **Source** : API `POST /api/chat/send` dans `10f2ae6e-…` (151 s, 0 confirmation d’envoi).
- **Ce que j’ai fait** : « Relance les trois financeurs […] IMPORTANT : ne les envoie PAS. »
- **Ce que j’attendais** : trois lettres, les vrais noms, ma vraie adresse, sans pièce jointe fantôme.
- **Ce qui s’est passé** : les trois brouillons sont là, ton administratif. Aucun envoi. Mais : *Madame, Monsieur* alors que j’ai donné Paul, Claire, Nadia. Pour Claire Aubert, l’e-mail de signature devient *sylv.roy@tableouverte.asso.fr* (le mien est *sylvie.ranc@…*). Les trois lettres annoncent *le dossier complet est joint* : je n’ai rien joint. Plus tôt, pour le dossier mairie (170 s), elle avait inventé *Avant le 15 août 2026* alors que l’échéance que j’avais dite est le 15 octobre, et suggéré une *attestation de TVA*.
- **Pourquoi ça compte pour moi** : un courrier à la DDCS avec le mauvais mail, ou une date de dépôt fausse, c’est une subvention qui glisse. Je relis déjà les portails. Si je dois relire l’outil autant que je rédige, je gagne zéro minute.

### F9 - Nulle part on ne me dit que c’est gratuit
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface. Accueil *ton business* (*WelcomeStep.tsx:57*). *À propos* : version, GitHub, Discord (*AboutTab.tsx*), pas un mot sur le prix. *Mise en route* : clé IA, agenda, messagerie, facturation. *Services* : Groq *gratuit jusqu'à un certain volume, puis payant*.
- **Ce que j’ai fait** : chercher le tarif avant d’investir une matinée.
- **Ce que j’attendais** : *gratuit*, *sans abonnement*, ou un prix associatif.
- **Ce qui s’est passé** : silence. *Facturer* est un bouton d’accueil. *cycle commercial* est un titre. Pour moi, ça sent le logiciel de commercial.
- **Pourquoi ça compte pour moi** : le bureau a voté zéro ligne « licences ». Si ce n’est pas écrit *gratuit* dès la première page, je n’ai pas le droit d’y passer du temps.

## Verdict

Je la rouvre demain seulement si on m’écrit que c’est gratuit, et si on arrête de me dire *client* et *Facturer*. Le chat, une fois que je me suis présentée, a parlé association. Les écrans, jamais. Les dossiers et le PV, ça m’a aidée, à condition de tout relire. Les relances et le planning des bénévoles, non : trop de Gmail, trop d’e-mails obligatoires, trop de pipeline. LibreOffice, lui, connaît déjà le mot *association*.
