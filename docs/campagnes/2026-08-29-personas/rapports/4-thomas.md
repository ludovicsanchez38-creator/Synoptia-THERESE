# Thomas Rivière — j'ai eu ma facture, mais à 20 % de TVA sur de la rénovation, et personne ne m'a rien dit

## Ce que j'ai fait

Midi, dans la camionnette. Trois choses à régler avant de repartir chez Dupont.

**0 à 1 min — je demande la facture à Thérèse, en français.** Je tape avec deux pouces :
« Fais-moi la facture du chantier Dupont : rénovation électrique d'un appartement de 2010,
1 800 € HT. Et préviens-moi la veille de l'échéance. » (API, `POST /api/chat/send`, `stream: true`.)

**1 à 6 min 30 — j'attends.** Rien. Le flux ne m'envoie que son en-tête pendant plusieurs minutes.
C'est le modèle local qui rame (`qwen3:8b`, 1 718 tokens de sortie), pas l'application :
`limite_modele_local`. Mais dans une camionnette, six minutes trente sur un écran vide, c'est
déjà plus que ce que j'ai. C'est là que j'aurais normalement reposé le téléphone.

**Ce qu'elle a fini par répondre**, mot pour mot :
« La facture a été générée et le rappel a été programmé. […] Montant HT 1 800 €, **TVA 20 % (360 €)**,
total TTC 2 160 €. Rappel le 30 août 2026 à 10h ». J'avais écrit « rénovation » dans ma phrase.
Elle a quand même posé 20 %. Et le « rappel » qu'elle annonce n'existe pas : l'outil est resté
bloqué en attente de ma confirmation (`confirmation_required`, `create_calendar_event`), et
l'application elle-même a écrit dessous « Récap réel : 1 contact(s) créé(s). » Donc : un contact.
Pas de facture, pas de rappel. La prose qui annonce le succès, c'est le modèle
(`limite_modele_local`) ; le garde-fou qui la contredit, c'est l'appli, et lui il a tenu.

**6 min 30 à 8 min — je fais le geste moi-même, à la main, sans toucher au taux.**
Je crée le contact Dupont et je passe la facture par le formulaire (API, `POST /api/invoices/`,
1 800 € HT, échéance vendredi 04/09) **en ne renseignant nulle part le taux de TVA**, exactement
comme quelqu'un qui remplit un formulaire sans aller fouiller les menus de chaque ligne. Retour :

```
"invoice_number": "FACT-2026-001", "subtotal_ht": 1800.0, "total_tax": 360.0, "total_ttc": 2160.0
```

360 € de TVA. C'est 20 %. Sur de la rénovation dans un logement de 2010, c'est 10 % : 180 €.
J'ai 180 € de trop sur une facture de 1 800 €, et **aucun écran ne me l'a signalé**. Pendant ce
temps, le même formulaire sait m'afficher un bandeau jaune quand il manque mon SIRET.

**Au-delà de mes 8 minutes** (j'ai continué parce que c'est mon boulot de tester, pas parce qu'un
artisan l'aurait fait) : j'ai cherché l'agenda chantiers, et j'ai cherché le rappel.

- **Agenda chantiers** : la liste déroulante de l'écran calendrier ne contient qu'une entrée,
  « Mon calendrier ». Aucun bouton pour en ajouter un. Le serveur, lui, sait le faire : une seule
  requête `POST /api/calendar/calendars?summary=Chantiers` et j'ai mon deuxième agenda. J'ai posé
  le RDV du jeudi 03/09 à 14 h dessus — par l'API, jamais par un écran.
- **Rappel** : il n'y a pas d'onglet « Notifications » dans les Réglages. Aucun réglage de rappel
  à créer, donc rien à créer. J'ai déclenché la génération à la main pour voir ce qui sort.

**Le verdict du rappel, dans une seule réponse** (`POST /api/notifications/generate`) :

```
{"generated":{"factures_impayees":0,"prospects_inactifs":0,"taches_en_retard":0,"rdv_demain":1},"total":1}
```

Ma facture est due vendredi : **zéro**. Mon rendez-vous de contrôle posé pour demain : **un**,
avec le message « RDV demain a 10h00 ». L'outil sait prévenir la veille. Il le fait pour mon
agenda. Il ne le fait pas pour mon argent.

## Dette connue rencontrée

| Dette | Je l'ai vue | Une ligne de preuve |
|---|---|---|
| TVA à 20 % par défaut | oui | `POST /api/invoices/` sans jamais renseigner le taux → `"total_tax": 360.0` sur `"subtotal_ht": 1800.0` (API) |
| Notification après l'échéance | oui | Même appel, facture due le 04/09 : `"factures_impayees":0` ; le seul message facture existant est « Facture {n} impayee depuis {X} jours » à J+30 (`notification_service.py:122` et `:148`) |
| Pas de chemin pour un 2e calendrier | oui | `createCalendar` existe (`services/api/calendar.ts:94`) mais n'est appelé nulle part dans `components/` ; l'API crée « Chantiers » en une requête (200) |
| 501 à l'envoi de facture | non | Non testé : tout envoi réel m'est interdit, je n'ai pas appelé `/api/invoices/{id}/send` |
| Cloison absente | non | Pas croisée sur mon chemin dans le temps que j'avais |
| Pas d'écran « cabinet » | non | Pas croisée sur mon chemin dans le temps que j'avais |

## Correctifs tenus (0.54 / 0.55)

- **La confirmation avant d'écrire dans mon agenda tient.** L'assistante a voulu poser un
  événement toute seule ; le flux a renvoyé `confirmation_required` sur `create_calendar_event`
  et rien n'a été écrit. (API, flux SSE de `/api/chat/send`.)
- **Le « Récap réel » tient, et c'est lui qui m'a sauvé.** Le modèle annonçait « la facture a été
  générée et le rappel a été programmé » ; l'application a écrit dessous « Récap réel :
  1 contact(s) créé(s). » (API, événement `status` ; source du garde-fou :
  `src/backend/app/services/execution_truth.py:91`.)
- **Le rappel « RDV demain » prévient vraiment la veille.** Événement posé au 30/08,
  génération → `"rdv_demain":1`, message « RDV demain a 10h00 : Controle rappel veille ». (API.)
- **Le repli en calendrier local tient sans compte Google.** Le second calendrier a été créé en
  `provider: "local"`, sans `account_id`, et le RDV du jeudi s'y est posé. (API.)
- **« Accepté » n'est plus proposé comme statut de facture.** Lu au passage en cherchant le champ
  TVA (`InvoiceForm.tsx:526-531`, code seulement, pas exercé) : une créance ne sort plus de
  l'encours par un clic de menu.

## Findings

### F1 — Le garde-fou de conformité couvre mon SIRET, pas mon taux de TVA — gravité majeure

**Ce qui s'est passé.** Le formulaire de facture sait m'arrêter quand il manque mes identifiants :
il affiche un bandeau jaune. Il ne dit rien quand il pose 20 % de TVA sur de la rénovation. Les
deux sont des défauts de conformité ; un seul est gardé. L'écran m'a donc appris qu'il me
surveillait, sur le sujet le moins cher des deux.

**Source.** `src/frontend/src/components/invoices/InvoiceForm.tsx:437-446` (le bandeau) contre
`:112` et `:143` (le défaut posé), et `src/backend/app/models/schemas.py:944` côté serveur.
Preuve d'exécution : `POST /api/invoices/` → `"total_tax": 360.0`.

**Libellés exacts.**
- Le garde-fou qui existe : « Infos de ta société incomplètes (…). **Une facture sans ces
  informations n'est pas conforme.** Complète-les dans Réglages > Profil avant de générer le PDF. »
- Le défaut qui passe sans un mot : `{ description: '', quantity: 1, unit_price_ht: 0, tva_rate: 20.0 }`
  (`InvoiceForm.tsx:112`), et côté serveur
  `tva_rate: float = Field(default=20.0, ge=0)  # Default TVA française normale` (`schemas.py:944`).
- Le menu, quand on le trouve, appelle le 20 % « **20% (normale)** » et le 10 %
  « **10% (intermediaire)** » (`InvoiceForm.tsx:31-32`).

**Pourquoi ça compte pour moi.** Neuf chantiers sur dix, je suis en rénovation de logement de plus
de deux ans : mon taux normal à moi, c'est 10 %. Sur cette facture, l'écart est de 180 €. Je ne le
verrai pas tant que je ne descends pas dans le détail de chaque ligne, et j'ai dit « rénovation »
dès ma première phrase. Un mot dans le bandeau jaune que l'outil sait déjà afficher aurait suffi.

### F2 — Thérèse sait prévenir la veille, elle le fait pour mon agenda et jamais pour mon argent — gravité majeure

**Ce qui s'est passé.** J'ai demandé « préviens-moi la veille ». Une seule génération de
notifications répond aux deux : mon rendez-vous de demain sort, ma facture due vendredi ne sort
pas. Voir « RDV demain » arriver m'apprend que l'outil prévient avant — donc je pars du principe
que l'échéance de vendredi arrivera pareil. Elle n'arrivera jamais avant. Le seul message facture
qui existe se déclenche **trente jours après** la date d'échéance, et il est écrit au passé.

**Source.** API, `POST /api/notifications/generate` →
`{"factures_impayees":0,"prospects_inactifs":0,"taches_en_retard":0,"rdv_demain":1}`, avec une
facture `FACT-2026-001` due le 04/09. Code :
`src/backend/app/services/notification_service.py:122` (`threshold = datetime.now(UTC) - timedelta(days=30)`),
`:127` (`Invoice.due_date < threshold`), `:148` contre `:245` et `:274`.
Aucun onglet « Notifications » dans `src/frontend/src/components/settings/` : il n'y a pas de
réglage à trouver.

**Libellés exacts.**
- Ce que je reçois, un mois trop tard : « **Facture {numéro} impayee depuis {X} jours** », bouton
  « **Relancer** » (`notification_service.py:148`).
- Ce que je reçois quand ça marche : « **RDV demain a 10h00 : Controle rappel veille** », type
  `reminder` (`notification_service.py:274`).

**Pourquoi ça compte pour moi.** Une facture qui traîne, chez moi, c'est un découvert. Le message
qui me dit « impayée depuis 30 jours » avec un bouton « Relancer » arrive quand la relance est
déjà une relance, pas quand elle est encore un coup de fil sympa. J'ai demandé la veille et
l'outil sait faire la veille : il ne le branche simplement pas sur l'argent.

### F3 — La liste « Calendrier affiché » me promet un choix que rien à l'écran ne permet de créer — gravité majeure

**Ce qui s'est passé.** Il y a bien un menu déroulant de calendriers, et l'application m'invite
même explicitement à y choisir. Il n'a qu'une entrée, et aucun écran ne permet d'en ajouter une
seconde. Le serveur, lui, en est parfaitement capable : une requête, et mon agenda « Chantiers »
existe. Le manque n'est donc pas dans la machine, il est dans l'écran.

**Source.** `src/frontend/src/components/calendar/CalendarPanel.tsx:449-458` (le menu),
`src/frontend/src/components/calendar/EventForm.tsx:48` (l'invitation),
`src/frontend/src/services/api/calendar.ts:94` (`createCalendar`, jamais appelé nulle part dans
`components/` — vérifié par recherche sur `createCalendar(`). API :
`GET /api/calendar/calendars` → une entrée « Mon calendrier » ;
`POST /api/calendar/calendars?summary=Chantiers&provider_type=local` → 200, deuxième calendrier créé.

**Libellés exacts.**
- Le menu : `<select aria-label="**Calendrier affiché**">` avec pour seule option « **Mon calendrier** »,
  et aucune entrée d'ajout.
- L'invitation : « **Aucun calendrier sélectionné. Choisis un calendrier dans le menu déroulant.** »
  (`EventForm.tsx:48`).

**Pourquoi ça compte pour moi.** J'ai deux vies dans mon téléphone : l'école et le médecin des
petites d'un côté, les chantiers de l'autre. Un outil qui me met « le passage chez Dupont jeudi
14 h » dans le même agenda que la sortie scolaire, je ne le laisse pas approcher de mon planning.
On me montre un menu qui dit « choisis », il n'y a rien à choisir, et le bouton qui manque existe
déjà côté serveur.

## Ai-je abandonné ?

Oui — à 6 minutes 30, sur l'écran resté vide pendant que le modèle réfléchissait ; puis une
deuxième fois, pour de bon, en lisant « TVA 20 % (360 €) » sur une facture où j'avais écrit
« rénovation » dans ma toute première phrase. Ma ligne rouge est là : une facture posée à 20 %
sur de la rénovation sans qu'un seul écran me le dise, alors que le même écran sait m'arrêter
pour un SIRET manquant.
