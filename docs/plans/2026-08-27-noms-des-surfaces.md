# Les noms des surfaces — proposition

> 27/08/2026. Suite du diagnostic
> `2026-08-27-diagnostic-surfaces-revise.md`.

## A. Conformité au lexique 0.48 — à corriger, pas à débattre

Le lexique (RULES-DESIGN §13) est déjà voté et verrouillé par
`lexique.test.ts`. Mais ce test porte sur les **registres de textes
exportés** — Centre de capacités, manifeste, actions, raccourcis, commandes,
vues, onboarding. Il ne regarde pas les **titres affichés dans les
panneaux**. Quatre y échappent :

| Surface | Titre affiché | Lexique | Correction |
|---|---|---|---|
| `CalendarPanel` | Calendrier | Agenda | **Agenda** |
| `InvoicesPanel` | Facturation | Devis et factures | **Devis et factures** |
| `BoardConversationCard` | Board de décision | Décision | **Décision** |
| `AtelierConversationCard` | Atelier de code | Améliorer THÉRÈSE | **Améliorer THÉRÈSE** |

C'est cette dérive qui produit le plus clairement la sensation de « trop
d'interfaces » : le même objet s'appelle « Agenda » dans le tiroir et
« Calendrier » une fois ouvert. Deux noms, une chose.

**Le test doit être étendu aux titres de panneaux**, sinon la dérive
reviendra. C'est le symétrique de ce que le lexique vérifie déjà.

## B. Dire ce que la surface fait — décision éditoriale de Ludo

Deux surfaces portent un titre qui décrit leur DOMAINE alors qu'elles font
un TRAVAIL particulier. Les renommer par le travail lève l'ambiguïté avec la
vue complète du même domaine.

| Surface | Titre actuel | Proposition | Pourquoi |
|---|---|---|---|
| `MeetingConversationCard` | Prochains rendez-vous | **Préparer un rendez-vous** | elle ne liste pas : elle rapproche les participants des contacts, montre leur historique, signale ceux qu'on ne connaît pas et enregistre une note CRM. Le titre actuel ne promet qu'une liste |
| `InvoiceConversationCard` | Devis et factures | **Facturer un client** | elle crée un contact, un devis, un brouillon à partir du contexte. Et son titre actuel est exactement celui que le lexique réserve à la VUE : deux surfaces, un nom |

`ContactsMemoryCard` (« Contacts et mémoire ») et `EmailConversationCard`
(« Messages à consulter ») sont laissés tels quels : ils sont déjà distincts
de « Contacts » et « Email », et décrivent honnêtement ce qu'ils montrent.

## C. Le passage d'une surface à l'autre

Les boutons disent « Ouvrir Agenda », « Ouvrir Projets », « Ouvrir
Facturation » — formulation qui promet un agrandissement de la même chose
alors qu'elle mène à un autre outil.

Proposition : nommer la destination par ce qu'on va y faire.

| Actuel | Proposition |
|---|---|
| Ouvrir Agenda | Voir tout mon agenda |
| Ouvrir Facturation | Gérer mes devis et factures |
| Ouvrir Projets | Gérer mes projets |
| Ouvrir Contacts | Gérer mes contacts |

Le verbe dit qu'on change d'outil ; « ouvrir » laissait croire au contraire.

## Ce que ça coûte

Des libellés, un test étendu, et les tests existants qui citent ces titres.
Aucune logique touchée, aucune capacité déplacée. C'est le contraire de la
fusion envisagée hier, qui aurait supprimé du métier.

## Ce que ça ne règle pas

Le cap produit — application conversationnelle ou application à vues — reste
ouvert. Cette proposition rend lisible ce qui existe ; elle ne choisit pas.
