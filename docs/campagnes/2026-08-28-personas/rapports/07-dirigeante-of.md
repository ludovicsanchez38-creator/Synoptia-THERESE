# Rapport - Nadia Belkacem, dirigeante d'organisme de formation

## Mon impression générale

J’ouvre l’application un vendredi matin, comme je le fais avec mon CRM : je veux voir ce qui est en retard, ce qui se joue aujourd’hui, ce qui rentre. L’écran me dit « Bonjour ! », « Données locales », et surtout « Branche tes mails pour que je te prépare la journée ». Mes mails, je les ai. Ce que je n’ai pas ici, c’est mon activité. Les cinq boutons s’appellent *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. Aucun ne dit pipeline, chiffre d’affaires, équipe. Pour voir mes trois prospects, il faut aller chercher *Pipeline* derrière *Plus d’outils*, dans un catalogue qui s’intitule « Ce que Thérèse sait mobiliser ». Une fois les fiches saisies à la main, le brief du jour me propose de « Relancer » Marie Lopez, que je viens d’entrer, et cache mon CODIR de 9 h. Le devis Horizon est là, 50 400 € TTC, mais le PDF refuse de sortir tant que je n’ai pas retapé SIRET et adresse, déjà dans l’ERP. Je n’ai pas une seconde CRM à nourrir. J’en ai déjà une, trop lourde, et je suis venue voir si celle-ci m’en débarrassait.

## Ce que j’ai réussi à faire

- Lire l’accueil au premier regard. Source interface : `ConversationCanvasPrototype.tsx`, `TodayDashboardCard.tsx`, `SetupChecklist.tsx`, `lib/etabli.ts`. Source API : `GET /api/dashboard/setup-status`, `GET /api/dashboard/today`.
- Poser trois prospects dans le *Pipeline* (*Découverte*, *Proposition*, *Signature*) via `POST /api/crm/contacts`, le même formulaire *Ajouter un contact* (Prénom, Nom, Entreprise, Email, Téléphone, Source, Stage). 7 champs + *Créer le contact*, trois fois. Environ 24 gestes. Les cartes affichent un « Score: » 105 / 115 / 125.
- Créer le devis `DEV-2026-001` pour Horizon Hôtellerie, 42 000 € HT / 50 400 € TTC, statut *Brouillon*. Source API `POST /api/invoices/` ; à l’écran le parcours s’appelle *Facturer*, le titre de carte « Facturer un client », le bouton « Nouveau devis ».
- Ouvrir un document « Proposition commerciale Horizon Hôtellerie » : trame de 11 sections, étiquette *Rédaction*, « 0/11 sections validées ». Toutes les sections sont vides.
- Noter trois tâches d’équipe (Céline, Julien, Samira) en mettant leur prénom dans les *tags*, faute de champ responsable. Filtre écran : « Filtrer par étiquette », option « Tous les tags ».
- Poser quatre rendez-vous sur « Mon calendrier » (local) : CODIR 9 h, point Céline 14 h, comité Karim le 01/09, signature Région le 02/09. L’agenda a une vue *Semaine*.
- Poser la question du composeur « Demande à Thérèse d’organiser, créer ou agir… » : « Qu'est-ce qui demande mon attention aujourd'hui ? » Réponse en 60 s (API `POST /api/chat/send`). Elle cite le point Céline, le comité Karim et la signature Région, pas le CODIR, pas la tâche Qualiopi en retard, pas le devis.
- Obtenir un brouillon de lettre commerciale en 80 s, et une réponse « qui fait quoi » en 105 s.

## Ce que je n’ai pas réussi à faire

- Voir l’état de l’activité en un regard, à l’ouverture, sans rien saisir. L’accueil vide m’envoie brancher mes mails. Après saisie, le brief ne montre ni le CODIR, ni le 42 k€, ni Sophie en signature.
- Importer mon CRM. À l’écran *Pipeline*, le seul bouton d’import est « Import .vcf ». La synchro s’appelle « Importer les contacts et projets depuis Google Sheets », rangée dans Paramètres > *Mode Contributeur* > *Avancé*. Mon outil n’est pas une feuille Google. Un CSV d’essai passe par l’API, le contact n’apparaît pas dans le kanban (pas de source).
- Mettre un montant d’affaire sur un prospect. Le formulaire n’a pas de champ budget. Les stats du pipeline comptent des têtes et un score, pas des euros.
- Déléguer : le formulaire *Nouvelle tâche* a Titre, Description, Statut, Priorité, date, projet, tags. Pas de responsable. Le chat, à qui j’ai demandé le travail de Samira, répond « Aucune tâche spécifique notée cette semaine » alors que son dossier signature est *urgent* et en retard depuis le 25/08.
- Sortir un PDF de proposition. Message API : « Profil émetteur incomplet : renseigne raison sociale ou nom, SIRET, adresse dans Réglages > Profil avant de générer un document de facturation. » À l’écran : « Profil émetteur incomplet (raison sociale ou nom, SIRET, adresse) ». Ces infos sont dans l’ERP.
- Obtenir une proposition grand compte utilisable : le chat écrit une lettre qui mélange le point interne avec Céline et « la signature du marché » (qui est le dossier Région, pas Horizon). Le document a 11 titres vides.
- Voir « ce qui rentre » : le devis 42 k€ n’est pas dans le brief du jour (uniquement les factures *Envoyée* / *En retard* de plus de 30 jours).

## Findings

### F1 - L’accueil ne me montre pas mon activité
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Ouverture : `GET /api/dashboard/setup-status` → `has_email: false`, `has_calendar: false`, `billing_complete: false`. `GET /api/dashboard/today` → tout à zéro.
  2. Lecture de l’écran d’accueil (`TodayDashboardCard.tsx` 138-153, `SetupChecklist.tsx` 25-45) : bandeau *Mise en route* avec « Connecter ton agenda », « Connecter ta messagerie », « Compléter le profil de facturation ». Carte du jour : « Branche tes mails pour que je te prépare la journée », bouton *Brancher mes mails*. Sous-texte : « Sans boîte connectée, le brief ne voit ni messages à traiter ni relances. »
  3. Après saisie de l’agenda, des tâches et du pipeline : l’API `/today` renvoie bien CODIR 9 h, point Céline 14 h, deux tâches urgentes, Marie Lopez à relancer. Le brief visible (`prototypeReadModels.ts` 150-167) écarte les rendez-vous sans participant ni contact CRM. Mes deux réunions du jour n’ont ni l’un ni l’autre. Il reste : tâche Samira en retard, relance Marie, plus Amine (un import test) et encore Marie. Titre : « Ton attention aujourd’hui ». Bouton *Vue complète*. Le devis 50 400 € TTC n’y figure pas.
- **Ce que j’attendais** : en un écran, le retard, le jour, ce qui rentre. Comme un tableau de bord de direction, pas une checklist d’installation.
- **Ce qui s’est passé** : au premier regard, on me demande de brancher une boîte mail. Une fois les données là, mon CODIR disparaît, le 42 k€ n’existe pas, et une fiche créée il y a deux minutes s’appelle déjà « Relancer Marie Lopez » (`prospectToAttention`, ligne 137). Un prospect sans `last_interaction` est traité comme un silence de 15 jours (`dashboard.py` 383-390), y compris le jour de sa création.
- **Pourquoi ça compte pour moi** : je ne saisis pas des données pour le plaisir. Si l’ouverture ne me dit pas où en est la boutique, je reste sur l’outil que j’ai déjà.

### F2 - Le pipeline, c’est une deuxième saisie, et l’import ne me concerne pas
- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Chercher le pipeline depuis l’accueil. L’établi (`lib/etabli.ts` 25-31) : *Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*. *Pipeline* est une carte du tiroir *Plus d’outils* (`CapabilityCenter.tsx` 177-180), titre du tiroir « Ce que Thérèse sait mobiliser ».
  2. Écran *Pipeline* (`CRMPanel.tsx` 145-165) : titre « Pipeline », boutons « Import .vcf » et « Ajouter un contact ». Formulaire : Prénom *, Nom, Entreprise, Email, Téléphone, Source, Stage (Contact / Découverte / Proposition / Signature / Livraison / Actif). Pas de montant.
  3. Trois `POST /api/crm/contacts` : Marie Lopez Métropole AMP (*Découverte*, 28 k€ dans les notes), Karim Benali Horizon (*Proposition*, 42 k€), Sophie Martin Région SUD (*Signature*, 38 k€). `GET /api/crm/pipeline/stats` : 3 têtes, des scores, zéro euro.
  4. Synchro : `GET /api/crm/sync/config` → `configured: false`. À l’écran, « Synchronisation CRM » vit dans Paramètres, onglet *Avancé*, lui-même derrière le bascule « Mode Contributeur » / « Fonctions avancées » (`SettingsModal.tsx` 46 et 776, `AdvancedTab.tsx` 123-126). Texte : « Importer les contacts et projets depuis Google Sheets » ; « Google Sheets reste la source de vérité » (`CRMSyncPanel.tsx` 292 et 626-627).
  5. Tentative CSV (ce que j’exporterais de mon CRM) : `POST /api/crm/import/contacts` réussit, « 1 crees ». Amine Boukhelifa, CCI du Var, `source: null`, `stage: contact`. Le kanban ne montre que les fiches **avec** une source (`CRMPanel.tsx` 37-40). Amine n’y est pas. Il apparaît quand même dans le brief du jour, à relancer.
- **Ce que j’attendais** : coller mon CRM, ou au moins un export Excel / CSV qui arrive dans les colonnes, avec les montants.
- **Ce qui s’est passé** : je retape. L’import visible est le carnet d’adresses du téléphone. L’autre import est une feuille Google, cachée dans un mode « contributeur ». Le CSV existe quelque part côté technique, et il ne nourrit même pas le tableau.
- **Pourquoi ça compte pour moi** : c’est ma ligne rouge. Huit salariés, 900 k€, un CRM déjà trop lourd. Je ne paie pas quelqu’un pour saisir deux fois Marie Lopez.

### F3 - Je ne peux pas déléguer, je peux coller un mot-clé
- **Gravité** : majeur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Lecture de *Nouvelle tâche* (`TaskForm.tsx`) : Titre *, Description, Statut (*À faire*), Priorité, date, projet, tags. Aucun champ responsable, assigné, équipier.
  2. Contournement : tags `Céline`, `Julien`, `Samira` sur trois tâches. L’écran propose « Filtrer par étiquette » / « Tous les tags » (`TasksPanel.tsx` 227-232).
  3. Fiches Céline Morel, Julien Khelifi, Samira Haddad en contacts mémoire, sans source, pour ne pas les mettre dans le pipeline commercial. Elles tombent quand même dans `pipeline/stats` colonne *contact* (4 fiches, dont l’équipe).
  4. Question au chat, 105 s, « Ne crée rien, montre-moi seulement ce qui est déjà noté. » Réponse : Céline relancerait Karim à 14 h 30 (c’est *mon* point avec elle) ; Julien a de l’ingénierie en notes ; **Samira : « Aucune tâche spécifique notée cette semaine. »** Or `GET /api/tasks/` contient « Dossier signature marché Région SUD », priorité *urgent*, échéance 25/08, tags `Samira`.
- **Ce que j’attendais** : « Céline : relance AMP. Julien : programme Horizon pour mardi. Samira : dossier signature, en retard. »
- **Ce qui s’est passé** : l’application n’a pas d’équipe. Le chat n’a pas lu les tâches. Samira porte le dossier le plus chaud de la semaine et l’outil me dit qu’elle n’a rien.
- **Pourquoi ça compte pour moi** : je ne forme plus, je pilote. Si je ne vois pas qui fait quoi, l’outil ne sert pas à une structure de huit personnes.

### F4 - Le brief du jour n’est pas la semaine, et le chat n’est pas d’accord avec l’écran
- **Gravité** : majeur
- **Nature** : friction_ux
- **Source** : les deux
- **Ce que j’ai fait** : quatre événements (28/08 9 h et 14 h, 01/09, 02/09). API `/today` : seulement les deux du 28. L’agenda a les boutons *Semaine* / mois / jour / liste (`CalendarPanel.tsx` 371-382). Le brief d’accueil, lui, filtre encore (F1). Question du parcours *Mes priorités du jour* (`ConversationCanvasPrototype.tsx` 118 et 128) : « Qu'est-ce qui demande mon attention aujourd'hui ? » 60 s, modèle local. Réponse : point Céline 14 h, comité Karim 01/09, signature Sophie 02/09, plus l’avertissement « Aucun compte email connecté ». Pas le CODIR de 9 h, pas la tâche Qualiopi en retard, pas Marie, pas le devis.
- **Ce que j’attendais** : la même vérité partout. Aujourd’hui d’un côté, la semaine de l’autre, clairement nommés.
- **Ce qui s’est passé** : trois listes différentes pour la même journée. L’écran cache les réunions internes. Le chat invente une « semaine » quand je demande aujourd’hui, et oublie le retard admin. Je n’arbitrerai pas là-dessus.
- **Pourquoi ça compte pour moi** : vendredi, j’arbitrer entre le CODIR, Céline, et le dossier Région. Si chaque surface raconte sa version, je reprends mon agenda papier.

### F5 - Une proposition grand compte, j’ai une lettre et des titres vides
- **Gravité** : majeur
- **Nature** : limite_modele_local
- **Source** : les deux
- **Ce que j’ai fait** :
  1. Devis réel `DEV-2026-001`, trois lignes, totaux justes. PDF : HTTP 400, message cité plus haut. Bandeau écran *Nouveau devis* : « Profil émetteur incomplet (raison sociale ou nom, SIRET, adresse). Une facture sans ces informations n'est pas conforme. Complète-le dans Réglages > Profil avant de générer le PDF. » (`InvoiceForm.tsx` 441-444.) `GET /api/config/profile` : `null`. Je n’ai pas retapé le SIRET.
  2. Document « Proposition commerciale Horizon Hôtellerie », 11 sections (Introduction, Contexte, Proposition de service, Méthodologie, Équipe, Tarification, Conclusion, Contact, trois annexes). Contenu : `""`. Badge *Rédaction*, « 0/11 sections validées » (`DocumentsList.tsx` 84 et 50).
  3. Chat 80 s : « Prépare une proposition… Ne l'envoie pas. » Sortie : lettre « Cher Karim », montants justes, puis « Relance le 28/08 à 14:30 (RDV avec Céline Morel) » et « Signature du marché » dès validation. Céline est interne. La signature, c’est Sophie / Région, pas Horizon. L’organisme n’a pas de nom : « [Votre nom complet], Directrice d’OF (Qualiopi) ». Aucun outil appelé, le devis déjà créé n’est pas cité.
- **Ce que j’attendais** : un document que je relis, que je mets en PDF, que j’envoie lundi. Le chiffrage, je l’ai. Le texte, je veux qu’il tienne devant un DRH de groupe.
- **Ce qui s’est passé** : un brouillon de mail qui mélange deux dossiers, un PDF bloqué par une fiche émetteur, une trame de onze cases vides. Un modèle plus fin écrirait mieux ; le mélange des dossiers, sur un grand compte, je ne le laisse pas partir.
- **Pourquoi ça compte pour moi** : Horizon c’est 42 k€. Je ne sors pas une lettre qui promet la signature du marché de la Région.

### F6 - Le score « de 0 à 100 » monte à 125
- **Gravité** : mineur
- **Nature** : defaut_app
- **Source** : les deux
- **Ce que j’ai fait** : créer Sophie Martin en *Signature*, avec email, téléphone, entreprise. Score renvoyé : 125. Infobulle de la carte (`PipelineView.tsx` 272-277) : « Score de potentiel commercial de 0 à 100, calculé depuis le profil et l'activité du contact. » Le calcul (`scoring.py` 43-88) additionne 50 de base + 20 e-mail + 15 téléphone + 10 entreprise + 30 stage signature, et ne plafonne qu’en bas (`max(0, score)`).
- **Ce que j’attendais** : un chiffre que je peux comparer, dans l’échelle annoncée. Ou pas de score du tout, j’en ai déjà un.
- **Ce qui s’est passé** : 105, 115, 125. Plus c’est « chaud », plus ça dépasse le cadre. Je ne sais pas si 125 est excellent ou cassé.
- **Pourquoi ça compte pour moi** : un commercial qui me sort un indicateur hors échelle, je range le tableau. Pareil ici.

### F7 - Ce que je devrais ressaisir, franchement
- **Gravité** : bloquant
- **Nature** : friction_ux
- **Source** : les deux (inventaire d’usage, pas un crash)
- **Ce que j’ai fait** : parcourir *Pipeline*, *Contacts et mémoire*, *Nouvelle tâche*, *Nouveau devis*, *Profil*, *Agenda*, *Documents*, *Synchronisation CRM*, et la liste des capacités.
- **Ce que j’attendais** : une liste courte de ce que THÉRÈSE prend à la place de mon CRM / ERP, et ce qu’elle me demande en plus.
- **Ce qui s’est passé**, à recenser :

| Déjà chez moi | Ici, à retaper ou rebrancher |
|---|---|
| Fiches prospects, étapes, montants | Formulaire *Ajouter un contact*, 7 champs, **sans montant** |
| Pipeline métier | 7 colonnes génériques (*Contact* … *Archive*) |
| Export CRM (Excel / CSV) | Bouton *Import .vcf* seulement ; Sheets caché en mode contributeur |
| Équipe (Céline, Julien, Samira) | Contacts comme les prospects, ou tags sur les tâches |
| Agenda (réunions, jurys, CODIR) | « Mon calendrier » local, ou « Connecter ton agenda » |
| SIRET, adresse, NDA, assurance | *Réglages > Profil*, sinon pas de PDF |
| Devis / factures / BPF | *Nouveau devis* / *Nouvelle facture*, à la main |
| Boîte mail | *Brancher mes mails*, sinon le brief insiste |

Ce que THÉRÈSE fait et que je n’ai pas ailleurs : un chat qui brouillonne, un atelier documentaire à sections, un brief du jour. Rien de tout ça ne tient si la base n’est pas la mienne.
- **Pourquoi ça compte pour moi** : un outil de plus qui me recopie le fichier client, je le ferme. J’ai déjà donné.

## Verdict

Je ne rouvre pas demain. Pas parce que « ça ne marche pas » : le devis se calcule, le kanban se remplit, l’agenda local accepte mes quatre rendez-vous. Je ne rouvre pas parce que, pour voir quelque chose, il faut d’abord tout saisir, et que l’accueil me parle de mails au lieu de mon 42 k€. Un copilote de rédaction à 40 € par mois, branché sur le CRM que j’ai déjà, je l’écouterais. Une deuxième base prospects, avec score à 125 et PDF bloqué au SIRET, à n’importe quel prix : non.
