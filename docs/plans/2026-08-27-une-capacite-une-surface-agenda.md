# Une capacité, une surface — premier cas : l'Agenda

> Design du 27/08/2026, à challenger AVANT toute ligne de code.
> Origine : Ludo, en regardant l'app — « il y a trop d'interfaces ».

## Le diagnostic

L'inventaire donne 12 vues, 7 scénarios, 36 cartes, 9 onglets, 8 panneaux.
Le nombre n'est pas le problème : **six capacités existent en double**.

| Capacité | Surface légère | Surface complète | Lignes |
|---|---|---|---|
| Contacts | ContactsMemoryCard | MemoryPanel | 295 + 823 |
| Email | EmailConversationCard | EmailPanel | 497 + 737 |
| **Agenda** | **MeetingConversationCard** | **CalendarPanel** | **464 + 563** |
| Devis et factures | InvoiceConversationCard | InvoicesPanel | 634 + 480 |
| Décision | BoardConversationCard | BoardPanel | 305 + 754 |
| Atelier | AtelierConversationCard | AtelierPanel | 359 + 348 |

6 259 lignes pour six capacités. Le code assume le doublon : chaque canevas
porte un `onOpenClassic` qui dit « la vraie version est ailleurs ». Sur les
factures, le jumeau léger (634) a même dépassé la version complète (480) :
les deux ont divergé chacune de leur côté.

**Ce n'est pas la quantité de fonctions qui sature, c'est qu'aucune des deux
surfaces n'est jamais « la bonne ».**

## Le principe

**Une capacité, une surface. Le contexte d'ouverture décide du niveau de
détail, pas le composant.**

Pas deux implémentations à tenir synchronisées : une surface unique avec un
réglage de densité.

## Le premier cas : l'Agenda

Choisi parce que les deux surfaces y sont d'égale importance (464 contre
563, aucune n'écrase l'autre), que l'usage est quotidien (donc jugeable en
vrai), et que la question des deux niveaux de détail y est nette.

### Ce que contient chaque surface

**MeetingConversationCard (464 l.)**
- liste « Prochains rendez-vous », triée
- `NewEventForm` : formulaire de création avec récapitulatif en TEXTE LIBRE
- `CalendarProvisioning` : crée un calendrier local au GESTE (BUG-143)
- états chargement / erreur / vide, bouton « Ouvrir Agenda »

**CalendarPanel (563 l.) + CalendarView + EventForm + EventDetail**
- quatre modes : Mois, Semaine, Jour, **Liste**
- navigation temporelle, synchronisation, reconnexion
- `EventForm` : confirmation via `requestExternalAction`, avec champs
  STRUCTURÉS (titre, début, fin, calendrier, fournisseur, compte,
  participants)

### Le doublon exact

1. La liste des prochains rendez-vous **est** le mode « Liste » de la vue.
2. Les deux formulaires de création font le même travail, et celui de la
   vue complète est le meilleur des deux (mécanisme commun de confirmation
   d'action externe contre phrase en texte libre).

### La cible

`CalendarPanel` devient l'unique surface, avec une **densité** :

- **compacte** (ouverture depuis la conversation, scénario `meeting`) :
  démarre en mode Liste, sans barre de navigation temporelle ni sélecteur
  de modes ;
- **complète** (vue embarquée) : les quatre modes et la navigation.

`MeetingConversationCard` et `NewEventForm` disparaissent. Le scénario
`meeting` ouvre `CalendarPanel` en densité compacte.

### Ce qui doit survivre, et c'est le vrai travail

**Le provisionnement au geste (BUG-143).** La coque lit les calendriers en
`createDefault: false` — une lecture ne doit jamais créer de données. Le
calendrier local n'est provisionné qu'au geste explicite de l'utilisateur
(`CalendarProvisioning`). `CalendarPanel` n'a pas cette logique : la perdre
en fusionnant réintroduirait un bug déjà corrigé.

C'est le SEUL élément à reprendre : contrairement à ce que je croyais avant
de lire le code, la confirmation avant création existe déjà côté vue
complète, en mieux.

## Découpage proposé

1. **Densité** : `CalendarPanel` accepte `densite: 'compacte' | 'complete'`,
   défaut `complete`. En compacte : mode Liste forcé, barre de navigation et
   sélecteur de modes masqués. Aucun autre changement de comportement.
2. **Provisionnement** : la logique de `CalendarProvisioning` rejoint
   `CalendarPanel`, déclenchée au geste, jamais à la lecture. Test de
   régression BUG-143 conservé et étendu à la nouvelle surface.
3. **Retrait** : le scénario `meeting` ouvre `CalendarPanel` en compacte ;
   `MeetingConversationCard` et `NewEventForm` supprimés ; le manifeste, la
   parité et le lexique suivent.

Gates verts à chaque étape. Revue Soso sur le design (ce document) PUIS sur
le diff final.

## Ce qui n'est PAS dans ce chantier

- Les cinq autres paires. On en fait UNE, Ludo regarde le résultat dans
  l'app, et on décide si le principe tient avant de continuer.
- Le nombre de vues, de cartes ou d'onglets. Autre sujet.
- Le cap produit (app conversationnelle ou app à vues). Ludo ne l'a pas
  tranché, et ce chantier ne le tranche pas : il supprime un doublon, il ne
  choisit pas un paradigme.

## Risques

| Risque | Traitement |
|---|---|
| Perdre le provisionnement au geste (BUG-143) | étape 2 dédiée, test de régression étendu |
| La densité compacte devient un fourre-tout de conditions | si plus de trois `if densite`, c'est que la fusion est mauvaise : on s'arrête et on rediscute |
| `CalendarPanel` grossit au lieu de maigrir | mesurer avant/après ; le total des deux fichiers doit BAISSER, sinon l'opération a échoué |
| Le mode Liste ne rend pas ce que rendait le canevas | comparer les deux rendus AVANT de supprimer quoi que ce soit |
