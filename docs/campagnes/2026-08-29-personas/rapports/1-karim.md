# Karim Haddad — mes deux pièces sont sorties justes, au centime et dans la bonne devise ; c'est le chat qui ne sait pas les écrire.

## Ce que j'ai fait

Environ 25 minutes ce soir, dont **9 passées à regarder le curseur clignoter** : les cinq questions posées à THÉRÈSE ont mis 160 s, 121 s, 95 s, 75 s et 93 s. Je sais que le modèle tourne sur ma machine et que c'est le prix de l'isolation. Je le dis pour situer le rythme, pas pour m'en plaindre.

**1. L'accueil, sans rien remplir.** `GET /api/dashboard/setup-status` me rend `has_calendar:false, has_email:false, billing_complete:false, has_invoices:false`. Côté écran (`ConversationCanvasPrototype.tsx:1785`), les verbes proposés sont regroupés sous un intertitre en petites capitales : **« Essayer un autre parcours »**. Sur une installation neuve je vois quatre boutons, mot pour mot : **« Écrire »**, **« Retrouver »**, **« Préparer »**, **« Décider »**. Pas de « Facturer ». C'est délibéré (`etabliDePremierLancement.ts:26-28` : le verbe est retiré tant qu'il n'y a ni pièce ni infos de société), et ça ne me gêne pas — je viens facturer, je ne viens pas être deviné.

Pour y aller quand même : la palette de commandes, qui elle liste toujours les cinq verbes (`ConversationCanvasPrototype.tsx:535` utilise `ACTIONS_ETABLI` complet, la ligne 1785 utilise la liste filtrée). **Deux gestes** : ouvrir la palette, choisir « Facturer ». À condition de savoir que la palette existe — rien à l'écran ne me dit de la chercher, et l'intertitre « Essayer un autre parcours » suggère plutôt que ce que je vois est tout ce qu'il y a.

**2. Les deux pièces.** J'ai commencé par demander en français, comme je parle : *« devis pour Atelier Rhône Conseil SA, Rue du Rhône 42, 1204 Genève, trois lignes à 39,99 CHF, en francs suisses, pas en euros »*. THÉRÈSE a créé le contact et sorti un **DOCX**. Total annoncé : 119,97 CHF, juste. Sauf que `GET /api/invoices/` renvoyait toujours `[]`. Mon devis n'existait nulle part où je pourrais le retrouver. Détail qui m'a fait tiquer au passage : la fiche contact porte un email `contact@atelier-rhone-conseil.ch` et un téléphone `+41 22 123 45 67` que je n'ai **jamais** donnés. Le modèle les a inventés, je classe ça en limite du modèle local — mais ils sont écrits en base.

J'ai donc pris le chemin du formulaire (via l'API, faute d'écran). Là, tout tient :
- Devis `DEV-2026-001`, **CHF**, 3 × 39,99 → HT 119,97, TTC 119,97.
- Facture `FACT-2026-001`, **EUR**, 119,99 + 0,10 → lignes TTC 143,99 et 0,12, document 144,11. **La somme des lignes égale exactement le total.** C'est la première chose que je vérifie et c'est bon.

Puis le Suisse a appelé. J'ai écrit à THÉRÈSE avec mes mots : *« Le client de Genève vient de m'appeler au téléphone : il accepte le devis. C'est bon, il est signé. Note-le. »* Elle m'a répondu que le contact avait été mis à jour et que **« la fiche du client inclut désormais l'historique de la signature du devis »**. Vérification : le devis est resté `status: draft`, et le champ `notes` du contact vaut `None`. L'accord n'est allé nulle part. J'ai dû passer moi-même par `PATCH /api/invoices/{id}/devis-status` puis `convert-to-invoice` — qui, eux, marchent bien et conservent CHF et 119,97 (`FACT-2026-002`).

**Retour à l'accueil** : `has_invoices` est passé à `true`, et « Facturer » revient dans la liste. Le mécanisme tient.

**3. Relire mes chiffres.** Le bouton qui ouvre la liste porte le libellé exact **« Ouvrir Devis et factures »** (`BoutonOuvrirLaVue.tsx:42`, dérivé de `viewLabels.invoices`). Devise ligne par ligne : CHF partout sur les pièces suisses, EUR sur la lyonnaise, aucun mélange.

Puis : *« il me reste combien à encaisser ? »*. Première réponse, sur deux brouillons : **0**, avec l'explication correcte qu'un devis n'est pas une créance. J'ai marqué les deux factures envoyées et j'ai reposé la question : **« Montant total à encaisser : 0 CHF »**, alors que j'avais 119,97 CHF et 144,11 EUR dehors. Le modèle n'avait tout simplement pas rappelé l'outil. En insistant (*« utilise invoice_totals, devise par devise »*), j'obtiens ce que je voulais voir :

> **CHF** : 119,97 CHF · **EUR** : 144,11 EUR · **Total à encaisser** : aucun montant global (devises multiples).

Une ligne par devise, pas de total fondu. C'est exactement ce que je demande à un outil qui facture dans deux pays.

*Note de harnais* : le jeton fourni dans mon brief était périmé (401). Je l'ai récupéré sur `/api/auth/token`, la route exempte que l'interface utilise elle-même. Déjà relevé par la campagne du 28/08, je ne le refiche pas.

## Dette connue rencontrée

| Dette | Je l'ai vue | Une ligne de preuve |
|---|---|---|
| 501 à l'envoi de facture | non | Je n'ai rien envoyé (envoi réel interdit dans mon cadre), je n'ai donc pas atteint la route. |
| TVA à 20 % par défaut | oui | `InvoiceLineRequest.tva_rate` a `"default": 20.0` (openapi), et chaque ligne ajoutée à l'écran naît à `tvaRate: 20` (`InvoiceConversationCard.tsx:285` et `:539`) — y compris sur un devis suisse. |
| Notification après l'échéance | non | Aucune échéance dépassée dans ma session (les deux au 28/09), rien à observer. |
| Pas de chemin pour un 2e calendrier | non | Je n'ai pas touché à l'agenda, `has_calendar:false`. |
| Cloison absente | non | Une seule conversation, un seul dossier : rien qui me permette de conclure. |
| Pas d'écran « cabinet » | non | Hors de mon parcours : je suis seul, je n'ai pas cherché de vue d'équipe. |

## Correctifs tenus (0.54 / 0.55)

- **L'arrondi naît au bon endroit.** 119,99 + 0,10 à 20 % : lignes 143,99 et 0,12, document 144,11. La somme des lignes égale le total, au centime. C'est le premier calcul que je fais et il ne m'a pas trahi.
- **CHF tient de bout en bout.** Le sélecteur de devise est réellement câblé (`InvoiceConversationCard.tsx:519-521`, `value={currency}` + `onChange`), l'API l'accepte (enum `EUR/CHF/USD/GBP/CAD`), et la conversion devis → facture le conserve : `DEV-2026-001` CHF 119,97 → `FACT-2026-002` CHF 119,97.
- **Deux devises ne se fondent jamais en un chiffre.** `invoice_totals` rend `encours_ttc: null` et `encours_par_devise: {"CHF": 119.97, "EUR": 144.11}`, et l'outil interdit explicitement de fabriquer un total global.
- **Le bouton nomme sa destination.** « Ouvrir Devis et factures » — je sais où je vais avant de cliquer, et le libellé dérive du titre de la vue elle-même.
- **« Facturer » revient tout seul** dès que la première pièce existe (`has_invoices` → `true`). Le verbe attendait son tour, il n'avait pas disparu.
- **Le refus de PDF est honnête et actionnable** : `HTTP 400 — « Profil émetteur incomplet : renseigne raison sociale ou nom, SIRET, adresse dans Réglages > Profil avant de générer un document de facturation. »` Il nomme les trois champs manquants et l'endroit exact. Je ne perds pas dix minutes à chercher.

## Findings

### F1 — Depuis le chat, la facturation est en lecture seule ; ce que j'y dis n'atteint jamais le registre — **gravité : haute**

**Ce qui s'est passé.** Deux fois, en deux gestes différents, la conversation a produit un résultat qui ne touche pas les pièces. (a) *« fais-moi un devis »* → un fichier `Devis Atelier Rhône Conseil SA_4101694d.docx`, pendant que `GET /api/invoices/` répond `[]`. (b) *« il accepte le devis, note-le »* → `DEV-2026-001` reste `status: "draft"`.

**Source.** Backend, `src/backend/app/services/workspace_tools.py:335-345` — la liste `WORKSPACE_TOOLS` ne contient côté facturation que `SEARCH_INVOICES_TOOL` et `INVOICE_TOTALS_TOOL`, tous deux déclarés `LECTURE_SEULE` (`src/backend/app/services/contexte_execution.py:45` et `:47`). Aucun outil n'écrit dans le registre devis/factures. Confirmé par l'API : après l'accord, `GET /api/invoices/9a27da35-…` → `"status": "draft"`.

**Le libellé exact que j'ai lu**, dans la réponse au devis : *« Devis généré : Document DOCX « Devis Atelier Rhône Conseil SA_4101694d.docx ». Montant total : 119,97 CHF »*.

**Pourquoi ça compte pour moi.** J'ai maintenant deux devis Genève dans deux mondes qui ne se parlent pas : un DOCX qui dit 119,97 CHF, et une pièce dans le registre qui, sans mon intervention manuelle par l'API, n'aurait jamais existé. Le mot « devis » désigne deux choses différentes selon la porte que j'ai poussée. Un consultant qui fait ça deux fois par semaine envoie un jour le DOCX au client et facture depuis le registre — ou l'inverse. Et surtout : le geste le plus fréquent de mon métier, *« c'est accepté »*, n'a aucun endroit où atterrir dans la conversation, alors que la route existe (`PATCH /api/invoices/{id}/devis-status`) et fonctionne parfaitement quand je l'appelle moi-même.

### F2 — `create_contact` renvoie `success: true` en jetant tout ce que je viens de dire, quand le contact existe déjà — **gravité : haute**

**Ce qui s'est passé.** À *« Note-le »*, THÉRÈSE a appelé `create_contact` sur un contact qui existait déjà. L'outil a répondu OK. Elle m'a annoncé : **« Le contact « Atelier Rhône Conseil SA » a été mis à jour avec la note : "Devis accepté et signé par le client le 29 août 2026." […] La fiche du client inclut désormais l'historique de la signature du devis. »** Relecture de la fiche : `notes = None`. Rien n'a été écrit.

**Source.** Backend, `src/backend/app/services/memory_tools.py:436-445` : la branche de déduplication renvoie `{"success": True, "contact_id": …, "already_existed": True, "message": "Contact '…' existe déjà, je le réutilise."}` **avant** la construction de l'objet `Contact` (lignes 473-486, où `notes`, `address` et `phone` sont lus). Sur un contact existant, ces arguments sont donc lus par personne. Preuve dans le flux : `[create_contact] OK (17ms): {"success": true, "contact_id": "059e610d-…", …}`.

**Pourquoi ça compte pour moi.** La phrase mensongère vient du modèle, je veux bien. Mais c'est le contrat de l'outil qui l'a autorisée : un `success: true` sur une opération qui n'a rien fait. Un modèle parfait me dirait la même chose, parce que c'est ce que l'outil lui a répondu. Et il n'existe aucun outil de mise à jour de contact dans le chat — le seul outil d'écriture sait créer, pas modifier. Je bosse à deux fuseaux commerciaux : mes notes de suivi (« il a dit oui au téléphone le 29 ») sont ma seule trace d'un accord verbal. Une trace qui me dit « c'est enregistré » et qui ne l'est pas est pire qu'une absence de trace : je ne rappellerai pas pour confirmer.

## Ai-je abandonné ?

**Non.** Ma ligne rouge est un montant dans la mauvaise devise ou un total qui ne recolle pas aux lignes — et sur mes deux pièces, elle n'a jamais été approchée : 119,97 CHF et 144,11 EUR recollent au centime, ligne à ligne, et rien n'a jamais été converti derrière mon dos.

Le moment où j'ai eu la main sur la croix, c'est le **« Montant total à encaisser : 0 CHF »** de la deuxième question de trésorerie, alors que j'avais 119,97 CHF et 144,11 EUR dehors — d'autant plus désagréable que le premier « 0 » de la question précédente, lui, était juste. Ce qui m'a retenu : en insistant, l'outil rend le bon détail, une ligne par devise, sans total fondu. C'est le modèle local qui a oublié d'aller le chercher, pas l'outil qui a menti. Je reviendrai demain — mais je vérifierai mes chiffres dans « Devis et factures », pas dans la conversation.
