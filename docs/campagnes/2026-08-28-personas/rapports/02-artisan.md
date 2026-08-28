# Rapport - Sébastien Roux, plombier-chauffagiste

## Mon impression générale

J’ai ouvert ça à la table de la cuisine, après 20 h, pour un devis chaudière. Premier écran : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Moi je veux un devis, pas une décision. J’ai cliqué *Facturer*. Ça marche, on peut pondre un brouillon, mais il a fallu d’abord créer le client, et je n’ai nulle part où coller son adresse ni son 06. Ensuite on m’a bloqué le PDF tant que je n’avais pas rempli un « profil émetteur » dans les Réglages, avec un bouton *Voir THERESE.md* et un champ « organisme de formation ». Le PDF sort, mais il est marqué DRAFT en anglais et les accents sont à la ramasse. Quand le client a rappelé, le chat a mis une minute et demie à me retrouver le devis, puis il m’a dit que 4 200 € ça ne collait pas (c’est le HT, le TTC c’est 4 620). Pour les impayés et « il me reste combien à encaisser », il a cherché à côté. Excel, je le connais. Là j’ai cliqué trop de fois, et trop de mots que je ne lis pas.

## Ce que j’ai réussi à faire

- Faire un devis chaudière Moreau à 4 200 € HT / 4 620 € TTC, n° DEV-2026-001, quatre lignes, TVA 10 %. (parcours *Facturer* puis *Nouveau devis* / *Préparer un devis*, environ 15 gestes une fois le client créé, plus le détour Réglages pour le PDF)
- Enregistrer le client Alain Moreau (nom, mail, téléphone). L’adresse, je l’ai tapée : elle n’est pas restée.
- Retrouver le devis en recliquant *Facturer* : il est là, *Brouillon*. Le chat l’a aussi trouvé (92 s).
- Voir les deux factures en retard dans le filtre *En retard* et sur le brief du jour, une fois que je les ai rentrées moi-même (Garcia 198 € TTC, SCI des Tilleuls 1 020 € TTC).
- Noter le chantier Martin : une tâche « Commander le matériel… » dans *Tâches*, et un jour *Chantier Martin - démarrage* le lundi 31 dans l’agenda local.
- Obtenir un PDF du devis après avoir collé SIRET + adresse entreprise dans *Réglages > Profil*.

## Ce que je n’ai pas réussi à faire

- Mettre l’adresse du client (14 chemin des Oliviers, Mane) dans la fiche. Pas de champ Adresse à l’écran. J’ai quand même envoyé l’adresse : elle est revenue vide.
- Mettre le 06 du client au moment du premier devis : le formulaire du devis n’a que Prénom / Nom / Entreprise / Email.
- Sortir un devis que je peux envoyer au client. Le PDF dit *DRAFT*, *EMETTEUR*, *Date d' emission*, *Validite*. Je ne donne pas ça à Moreau.
- Savoir tout seul quelles factures traînent, depuis combien de jours, et avoir un message de relance pour Garcia et la SCI. Le chat a parlé de Moreau et m’a collé un « Cher Alain » avec des crochets à remplir.
- Poser la question de comptoir « il me reste combien à encaisser ce mois-ci ? » et avoir le chiffre (1 218 € TTC des deux impayés). Réponse : allez filtrer dans Facturation, statut « en attente ».
- Faire noter le chantier Martin en une phrase. Le chat a créé un « projet » *Chantier Martin* qui dit que ça démarre « lundi 30 août » (le 30 c’est un dimanche, lundi c’est le 31) et une date limite au 25 août, déjà passée.

## Findings

### F1 - Le bouton dit *Facturer* alors que je veux un devis
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (`src/frontend/src/lib/etabli.ts` 25-30, `ConversationCanvasPrototype.tsx` 117-122, `InvoiceConversationCard.tsx` 127 et 134-140)
- **Ce que j’ai fait** : ouvrir l’accueil, chercher « devis ».
- **Ce que j’attendais** : un bouton *Devis*, comme sur mes papiers.
- **Ce qui s’est passé** : cinq puces *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Le titre du parcours, une fois cliqué, dit *Créer un devis*. La carte s’appelle *Facturer un client*, avec *Nouveau devis* et *Facturation complète*. Dans *Plus d’outils*, ça s’appelle *Devis et factures*. Trois noms pour la même chose. *Retrouver*, je croyais que ça cherchait dans mes trucs (devis, mails). Ça ouvre *Retrouver un contact*.
- **Pourquoi ça compte pour moi** : le soir je clique. Si le mot n’est pas le mien, je me trompe de case. *Décider*, je ne sais pas ce que ça veut dire, je n’y touche pas.

### F2 - Je ne peux pas coller l’adresse du client (ni le 06 sur le premier devis)
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Parcours devis sans client : l’écran *Crée le client de ce premier devis* (`InvoiceConversationCard.tsx` 425-456) n’a que Prénom, Nom, Entreprise, Email. Pas de téléphone, pas d’adresse. Texte : « Le contact sera enregistré dans le CRM puis sélectionné automatiquement. Tu restes dans ce canevas. »
  2. Fiche *Nouveau contact* (`ContactModal.tsx`) : Prénom, Nom, Entreprise, Email, Téléphone, Notes, *Tags (séparés par des virgules)*. Toujours pas d’adresse.
  3. API : `POST /api/memory/contacts` avec `"address": "14 chemin des Oliviers, 04300 Mane"` → la réponse a `"address": null`. `PATCH` avec la même adresse, là ça reste. Le PDF a pu l’afficher seulement après ce PATCH.
- **Ce que j’attendais** : nom, 06, adresse du chantier. C’est ce que je mets en haut d’un devis.
- **Ce qui s’est passé** : l’adresse est avalée à la création. Le 06 n’existe pas sur le formulaire du premier devis. Un devis sans adresse, je ne l’envoie pas.
- **Pourquoi ça compte pour moi** : Moreau n’a pas que un mail. Mes clients, c’est le téléphone et la maison. Si je dois retaper l’adresse à la main sur le PDF, autant rester sur Excel.

### F3 - Quinze clics plus un « profil émetteur » avant d’avoir un PDF, et le PDF n’est pas montrable
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Devis enregistré en brouillon : bandeau *Profil émetteur incomplet : raison sociale ou nom, SIRET, adresse. Tu peux enregistrer le brouillon, mais pas générer un PDF conforme.* (`InvoiceConversationCard.tsx` 476-479)
  2. `GET /api/invoices/5aa07657-…/pdf` avant profil → 400 : « Profil émetteur incomplet : renseigne raison sociale ou nom, SIRET, adresse dans Réglages > Profil »
  3. J’ai rempli *Réglages > Profil* (`ProfileTab.tsx`) : *SIRET (requis pour facturer)*, adresse, entreprise. J’ai aussi vu *Voir THERESE.md*, *N° de déclaration d'activité (organisme de formation)*, *Contexte additionnel* « injectées dans le contexte de l'IA ».
  4. Nouveau `GET …/pdf` → 200, fichier `DEV-2026-001.pdf`.
- **Ce que j’attendais** : un PDF propre, en français, que je mets sur WhatsApp à Moreau.
- **Ce qui s’est passé** : le PDF a les bons montants (4 200 HT, 4 620 TTC) et le SIRET. Statut écrit *DRAFT*. Titres sans accents : *EMETTEUR*, *DESTINATAIRE*, *Date d' emission*, *Date d' echeance*, *Validite*, *DETAIL DES PRESTATIONS*, *Document genere par THERESE*. Page 2 : « Paiement a reception de facture » sur un devis.
- **Pourquoi ça compte pour moi** : ma comptable veut des documents propres. Moreau aussi. Un devis marqué DRAFT, je ne l’envoie pas. Et « organisme de formation », c’est pas mon métier, je suis plombier.

### F4 - « Combien à encaisser » et « quelles factures impayées » : l’outil ne sait pas additionner, il cherche un nom
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Deux factures en *En retard* : FACT-2026-001 Garcia, 198 € TTC, échéance 15/07 ; FACT-2026-002 SCI des Tilleuls, 1 020 € TTC, échéance 20/06. `GET /api/invoices/?status=overdue` les rend. `GET /api/dashboard/today` aussi (`overdue_invoices`, 2).
  2. Chat, 140 s : « mes factures pas payées c'est lesquelles, depuis combien de temps, et prépare-moi un message de relance. tu l'envoies pas. » Statut à l’écran : *Execution des outils: search_invoices...* Résultat outil : « Aucune facture ni devis local ne correspond à « Alain Moreau ». » Texte : aucune facture pour Moreau, plus un modèle « Cher Alain » avec `[REFERENCE]`, `[MONTANT]`, `[DATE_limite]`.
  3. Chat neuf, 118 s : « il me reste combien à encaisser ce mois-ci ? » L’outil cherche « encaissement août 2026 », rien. On me dit d’aller dans *Facturation*, filtrer par mois et statut « en attente » / « partiellement payé ». Ces statuts n’existent pas : l’écran a *Brouillon*, *Envoyée*, *Payée*, *En retard* (`InvoicesPanel.tsx` 30-41 et 226-228).
- **Ce que j’attendais** : Garcia, 44 jours ; la SCI, 69 jours ; 1 218 € à rentrer ; deux textos que je copie.
- **Ce qui s’est passé** : `search_invoices` ne cherche que la référence ou le nom du client (`workspace_tools.py` 259-274 et 359-388). Une question sans nom, ou « impayé », tombe dans le vide. Le brief du jour écrit *Facture FACT-2026-001* / *198,00 € · échéance 15/07* / badge *À relancer* (`prototypeReadModels.ts` 75-86) : pas le nom du client, pas « depuis combien de jours ».
- **Pourquoi ça compte pour moi** : c’est la seule question que je pose tous les mois, avant la comptable. Si je dois recompter à la main, je n’ai pas besoin de l’appli.

### F5 - La liste *Devis et factures* n’affiche pas le nom du client
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : interface (`InvoicesPanel.tsx` 268-322)
- **Ce que j’ai fait** : après création, ouvrir *Gérer mes devis et factures* / *Devis et factures*. Côté API, chaque ligne a un `contact_id`, pas le nom.
- **Ce que j’attendais** : « Moreau, devis chaudière, 4 620 € ».
- **Ce qui s’est passé** : on voit *DEV-2026-001*, badge *Devis*, *Brouillon*, dates, montant TTC. Pas le client. La petite carte *Facturer un client* montre bien « Alain Moreau · devis » (`InvoiceConversationCard.tsx` 189). L’écran « complet », non. Vide : *Aucune facture* et bouton *Créer une facture*, même si je suis sur le filtre *Devis*.
- **Pourquoi ça compte pour moi** : je ne retiens pas les numéros DEV-2026-001. Je retiens Moreau. Si le client rappelle, je cherche Moreau, pas un numéro.

### F6 - « Note que le chantier Martin démarre lundi » crée un projet à la mauvaise date
- **Gravité** : majeur
- **Nature** : limite_modele_local
- **Source** : API (chat)
- **Ce que j’ai fait** : `POST /api/chat/send` « le chantier Martin démarre lundi, faut que je commande le matériel avant, note-le quelque part que je n'oublie pas » (92 s). Statut : *Execution des outils: create_project...* puis *Récap réel : 1 projet(s) créé(s).*
- **Ce que j’attendais** : une case à cocher « commander le matos avant lundi », éventuellement un jour dans l’agenda.
- **Ce qui s’est passé** : un projet *Chantier Martin*, description « Démarrage du chantier lundi 30 août 2026 » (le 30 août 2026 est un dimanche). Le texte parle d’une date limite *jeudi 25 août 2026*, déjà passée (on est le 28). Il me demande si je veux un rappel calendrier. Aucune tâche créée par ce message. (`GET /api/memory/projects`, `GET /api/tasks/` : la tâche Martin, c’est moi qui l’ai faite à la main dans *Tâches*.)
- **Pourquoi ça compte pour moi** : lundi je suis sur le chantier, pas dans un « projet ». Si la date est fausse, je m’en sers plus.

### F7 - Trop de mots que je ne comprends pas (je ne demanderai pas, je partirai)
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : interface (fichiers et lignes ci-dessous)
- **Ce que j’ai fait** : lire ce qui s’affiche, sans ouvrir l’aide. Compte des mots où je décroche, et ce que je croyais.
- **Ce que j’attendais** : les mots de mon métier : devis, facture, client, relance, lundi, matériel.
- **Ce qui s’est passé** (libellés exacts) :

| Mot à l’écran | Fichier | Ce que je croyais |
| --- | --- | --- |
| *canevas* (« Tu restes dans ce canevas ») | `InvoiceConversationCard.tsx` 435 | Un truc de peintre. Je ne vois pas le rapport avec un devis. |
| *CRM* | même ligne | Un logiciel de commerciaux. Pas moi. |
| *Profil émetteur* | `InvoiceConversationCard.tsx` 479, `InvoiceForm.tsx` 442 | L’émetteur de la chaudière ? Non : ma boîte, mais ce n’est pas dit comme ça. |
| *Facturation locale* / *Référentiel contacts* | `ConversationCanvasPrototype.tsx` 1746-1747 | Jargon. Je veux « mes devis » et « mes clients ». |
| *THERESE.md* | `ProfileTab.tsx` 115-117 | Un fichier d’informaticien. Je n’ouvre pas. |
| *N° de déclaration d'activité (organisme de formation)* | `ProfileTab.tsx` 372 | Rien à voir avec la plomberie. |
| *Contexte additionnel* « injectées dans le contexte de l'IA » | `ProfileTab.tsx` 384-388 | Je ne sais pas ce que je dois écrire. |
| *Multi-LLM* / *provider IA* / *Ollama* | `WelcomeStep.tsx` 18-30 | Accueil. Je clique Suivant sans lire. |
| *Capacités* / *Parcours* | `ConversationCanvasPrototype.tsx` 532, 568, 1803 | Des mots d’appli. |
| *Plus d’outils* | `ConversationCanvasPrototype.tsx` 1506 | Encore un tiroir. *Pipeline*, *Scopes*, *Extraction d’entités*, *Indexation* sont dedans (`CapabilityCenter.tsx`). Je n’y vais pas. |
| *Global* / *Conv.* | `MemoryPanel.tsx` 300-310 | Filtres sur les contacts. Aucune idée. |
| *RGPD* | `MemoryPanel.tsx` 317-323 | J’ai déjà entendu, je ne sais pas quoi faire. |
| *Tags* | `ContactModal.tsx` 263 | Des étiquettes. Pourquoi sur un client ? |
| *search_invoices* / *create_project* (bandeau *Execution des outils: …*) | événements SSE du chat | De l’anglais. Je n’ai pas demandé un outil, j’ai posé une question. |
| *DRAFT* | PDF DEV-2026-001 | Brouillon, mais en anglais sur un papier client. |
| *Avoirs* | `InvoicesPanel.tsx` 207 | Un avoir, d’accord, mais collé à *Tout / Devis / Factures* dès le premier écran vide. |
| *Espaces de travail* | `ConversationCanvasPrototype.tsx` 1485 | Je croyais un dossier chantier. Ça ouvre les projets. |
| *Parcours réel · confirmation avant effet* | `ConversationCanvasPrototype.tsx` 1851 | Une phrase pour informaticien sous la zone de saisie. |

- **Pourquoi ça compte pour moi** : un mot que je ne comprends pas, je ne le demande pas, je ferme. *Canevas* et *profil émetteur* sont pile sur le devis, donc pile où je décroche.

### F8 - La TVA part à 20 % alors que le remplacement de chaudière chez le particulier, c’est 10 %
- **Gravité** : mineur
- **Nature** : friction_ux
- **Source** : interface (`InvoiceConversationCard.tsx` 286-287 et 538-540, `InvoiceForm.tsx` 30-36 : défaut `tva_rate: 20.0`, libellé *20% (normale)*)
- **Ce que j’ai fait** : ouvrir *Nouveau devis*. Une ligne vide, TVA déjà à 20 %.
- **Ce que j’attendais** : au moins que ça se voie gros, ou 10 % pour de la rénovation.
- **Ce qui s’est passé** : si je ne change pas la liste, le devis Moreau passe à 5 040 € TTC au lieu de 4 620. J’ai corrigé parce que je connais mes taux. Un apprenti ne corrigera pas.
- **Pourquoi ça compte pour moi** : un devis trop cher, le client ne signe pas. Un devis trop juste, je perds la TVA.

## Verdict

Demain je n’ouvre pas. J’ai un devis dans l’appli, mais je ne peux pas l’envoyer comme ça, et pour les impayés je n’ai pas le chiffre. Excel plus WhatsApp, je sais où cliquer. Si un jour le premier bouton dit *Devis*, que je peux coller l’adresse et le 06, et que « il me reste combien à encaisser » me sort 1 218 € avec les noms, je reviendrai. Pas avant.
