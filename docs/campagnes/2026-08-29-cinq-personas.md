# Campagne cinq personas — THÉRÈSE 0.55 (29/08/2026)

## En un coup d'œil

| Persona | Métier | A abandonné ? | Sur quoi |
|---|---|---|---|
| Karim Haddad | consultant franco-suisse, facture en CHF et EUR | **non** | — |
| Inès Khelifi | psychologue clinicienne, secret professionnel | **oui** | 854 s de génération contre 12 min de patience |
| Aude Perrin | consultante en organisation | **oui** | le temps, pas la ligne rouge |
| Thomas Rivière | électricien, TVA 10 % rénovation | **oui** | 6 min 30 de flux muet |
| Léa Martin | assistante freelance, livrable Office | **oui** | aucun moyen de récupérer son fichier |

Quatre abandons sur cinq. **Trois sur le temps du modèle local**, un seul sur un
défaut de l'application (Léa). Karim, seul à disposer de 25 minutes, est allé au
bout.

Quatorze findings au total, contre 76 pour les dix personas du 28/08. Le cadrage
— quota de quatre, mandat exclusif, dettes mesurées une seule fois — a tenu.

## Ce que la 0.54 et la 0.55 ont fermé, confirmé en usage

Ces correctifs ont été **parcourus** par au moins un persona et ont tenu :

- **L'arrondi.** Karim : `119,99 + 0,10` à 20 % donne `143,99 + 0,12 = 144,11`,
  et la somme des lignes égale le total du document.
- **La devise.** Le CHF voyage de bout en bout, jusqu'à la conversion
  devis→facture. `invoice_totals` rend `encours_ttc: null` avec
  `{CHF: 119.97, EUR: 144.11}` : aucun total fondu.
- **Le nommage.** Le bouton dit « Ouvrir Devis et factures », et Aude a vérifié
  que le libellé dérive de la table qui titre la destination.
- **L'établi.** « Facturer » revient dès que `has_invoices` passe à `true`.
- **La confirmation avant écriture.** Thomas et Léa l'ont vue bloquer une
  écriture d'agenda que le modèle voulait faire seul.
- **Le refus honnête.** Aude : l'export répond `400 Document vide : rien à
  exporter` au lieu de livrer une coquille. Karim : le refus de PDF nomme les
  trois champs manquants.
- **La promesse web.** Aude ne fiche rien : l'écran annonce franchement qu'il
  n'y a **pas** de confirmation avant sortie web.
- **La recherche approfondie** ne plante plus à l'import.
- **Le cloisonnement des fiches.** Inès : le contact portant le secret
  (anxiolytique, prénom du conjoint) n'a jamais reparu dans l'autre dossier.

## Le motif dominant : la couche d'exécution affirme un succès sans le geste

Le lot A avait fermé « l'écran promet ce que l'application ne fait pas ». Les
cinq personas le confirment : **aucun ne fiche une phrase d'écran mensongère.**

Ce qui reste est une couche plus bas, et quatre personas l'ont rencontré
indépendamment, sur quatre chemins différents :

| Persona | La couche qui affirme | La preuve |
|---|---|---|
| Karim | `create_contact` rend `success: true` en jetant `notes`, `address`, `phone` sur un contact existant | `memory_tools.py:436-445`, la branche de déduplication sort avant la lecture des champs |
| Inès | la note de séance annoncée enregistrée, jamais écrite | zéro `tool_result`, recherche « alprazolam » à 0, Qdrant à 2 points |
| Aude | l'indexation se déclare `etat: "fait"`, `erreur: null`, horodatée | `chunk_count: 0` sur trois fichiers, Qdrant à `points_count: 1` |
| Léa | le fichier XLSX est produit — rien ne s'affiche pour le récupérer | `[generate_document] OK` mais **aucun chunk `skill_file`**, `extra_data: null` |

**Le garde-fou existe, et il est à moitié armé.** Thomas l'a vu fonctionner :
« Récap réel : 1 contact(s) créé(s) » a contredit à l'écran une prose annonçant
« facture générée et rappel programmé ». Inès a trouvé son angle mort :
`summarize_executions` **se tait quand `total == 0`** (`execution_truth.py:44-91`).

Il couvre donc la sous-déclaration — annoncer moins qu'on a fait — et jamais
l'invention. Il est aveugle exactement là où le mensonge coûte le plus.

## Le second motif : des chemins qui existent en backend et n'ont pas de porte

Trois fois, la fonction marche quand on l'appelle soi-même, et aucun écran ni
aucun outil ne l'atteint :

- **Écrire une facture depuis le chat.** `WORKSPACE_TOOLS` n'a côté facturation
  que `search_invoices` et `invoice_totals`, tous deux en lecture seule
  (`workspace_tools.py:335-345`). « Il accepte le devis » laisse la pièce en
  `draft`, alors que `PATCH /{id}/devis-status` fonctionne. *(Karim)*
- **Créer un second calendrier.** `createCalendar` existe
  (`services/api/calendar.ts:94`) et n'est appelé par aucun composant ; le
  serveur crée un agenda « Chantiers » en une requête. *(Thomas)*
- **Produire un fichier par une compétence en le demandant en français.** Le
  chemin `skill_id` marche de bout en bout — carte affichée, `extra_data`
  peuplé. Mais la détection par mots-clés a été retirée
  (`intent_detector.py:148-154`), et `skill_id` n'est posé que par les prompts
  suggérés. *(Léa)*

Et un cas voisin : **aucun outil de mise à jour de contact** n'existe, alors que
`create_contact` refuse d'écrire sur un contact existant.

## Le cloisonnement : un demi-mur

C'est le constat d'Inès, le plus grave de la campagne. **Gravité bloquante.**

| Domaine | A fuité ? | Preuve |
|---|---|---|
| Agenda | **oui, franc** | Depuis le dossier Ruiz : `[list_calendar_events] OK` → « **01/09 10:00-11:00 — Séance Martin** » |
| Notes / mémoire | **oui, partiel** | Le nom du dossier de l'autre patient remonte par `include_global` |
| Fichiers | non éprouvé | corpus vide |
| Factures | non éprouvé | aucune facture |
| Mails | non éprouvé | aucun compte connecté |

Sa cause est plus grave que le symptôme : `_list_calendar_events(args, session)`
n'a **ni `scope`, ni `scope_id`, ni `conversation_id`** (`workspace_tools.py:1154`).
La cloison n'y est pas contournée — **elle n'y est pas exprimable**. Signature
identique pour `_search_invoices` (`:643`), `_send_email` (`:1050`),
`_search_emails` (`:1117`).

Inès insiste, et elle a raison : « domaine **non éprouvé**, pas domaine sûr ».
Elle note aussi que le contenu de la note n'a pas fui *parce qu'il n'a jamais
été enregistré*, pas parce que la cloison l'a retenu.

## Les trois dettes connues, mesurées une seule fois

Par Thomas, dont c'est le métier. Sa phrase :

> **« L'écran a un garde-fou jaune pour un SIRET manquant, et rien pour 180 €
> de TVA en trop. »**

- **TVA à 20 % par défaut** : prouvée par deux chemins. « Rénovation d'un
  appartement de 2010 » dans la phrase → « TVA 20 % (360 €) ». Et par l'API,
  sans renseigner de taux → `total_tax: 360.0` sur 1 800 € HT.
- **Notification après l'échéance** : `{"factures_impayees":0, "rdv_demain":1}`.
  L'outil sait prévenir la veille — il le fait pour l'agenda, pas pour l'argent.
  Et le filtre `status.in_(["sent","overdue"])` (`notification_service.py:126`)
  fait qu'une facture remise en main propre ne notifie **jamais**.
- **Second calendrier** : voir ci-dessus.

Grok classait la TVA « surestimée » parce que les cinq taux français sont dans
le formulaire. Il a raison sur le formulaire. Thomas montre le vrai trou : c'est
le **défaut** qui est faux pour un métier entier, et rien n'alerte.

## Ce que le harnais a trouvé, et qui n'est pas dans les rapports

- **H1** — `POST /api/chat/send` en `stream: false` affirme « le contact a été
  enregistré » et ne crée rien. Vérifié avant de conclure : Ollama rend un
  `tool_calls` parfaitement formé en direct, et le même message en streaming
  crée bien le contact. Observation d'API, pas expérience utilisateur.
- **H2** — Le contrôle d'intégrité a trouvé `FACT-2026-001.pdf` **dans
  l'installation réelle**. `resolve_invoice_output_dir()` retombait sur
  `~/.therese/invoices` en dur. C'est le défaut O1 de la campagne précédente
  sur un troisième chemin : le lot 4 avait balayé les journaux et `THERESE.md`,
  pas les PDF. **Corrigé le jour même, avec sabotage.**

## Ce que la campagne n'a pas vu

- Les fichiers, factures et mails **n'ont pas été éprouvés** pour le
  cloisonnement, faute de corpus. Ne pas les lire comme sûrs.
- Le mode cabinet n'a été activé par personne : son absence d'écran est notée,
  son comportement n'est pas mesuré.
- Le 501 d'envoi de facture n'a été atteint par aucun persona.
- La lenteur du modèle local (90 à 400 s par échange) a coûté trois abandons.
  Elle est classée `limite_modele_local` partout, mais elle a **empêché de
  mesurer** ce que ces trois personas auraient trouvé ensuite.
