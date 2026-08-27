# « Trop d'interfaces » — le diagnostic, après avoir lu le code

> 27/08/2026. Remplace le design invalidé
> `2026-08-27-une-capacite-une-surface-agenda.md`.
> Origine : Ludo, en regardant l'app — « je trouve qu'il y a trop
> d'interfaces ».

## Ce que je croyais

Six capacités existaient en double, une surface légère dans la conversation
et une surface complète, avec un bouton `onOpenClassic` qui avouait le
doublon. 6 259 lignes pour six fonctions. Remède : fusionner.

**C'était faux.** Le diagnostic reposait sur la présence de ce bouton et sur
des noms de fichiers, pas sur ce que chaque surface fait.

## Ce que dit le code

Comparaison des ACTIONS de chaque paire — ce qu'une surface permet de faire
est ce qui définit sa capacité, davantage que ce qu'elle affiche.

| Paire | Actions de la surface conversationnelle | Actions de la surface complète | Communes |
|---|---|---|---|
| Contacts | ouvrir, sélectionner un contact | supprimer, actions RGPD | **aucune** |
| Email | générer un brouillon, ouvrir, enregistrer | connexion de compte | **aucune** |
| Agenda | créer un événement, créer une note CRM, provisionner un calendrier | (délègue) | **aucune** |
| Factures | créer un contact, créer un devis, créer un brouillon | enregistrer | **aucune** |
| Décision | démarrer, réinitialiser, ouvrir une décision | changer de modèle, rafraîchir Ollama | annuler |
| Atelier | démarrer, muter, ouvrir une tâche | choisir un agent, dialoguer | annuler |

**Aucune paire ne partage son travail.** Ce ne sont pas des doublons.

### Le cas le plus net

| « Contacts » côté conversation | « Contacts » côté vue complète |
|---|---|
| Contacts et contexte | Anonymisation RGPD |
| Contacts et mémoire | Droit à l'oubli (Art. 17) |
| Notes mémorisées | Droit de portabilité (Art. 20) |
| | Renouveler le consentement, Import / Export |

L'une répond à « qui est cette personne ? ». L'autre à « gérer mes
obligations RGPD ». Elles portent le même nom et la même icône.

## Le vrai motif

Les deux familles de surfaces ont des rôles opposés, et cohérents :

- **côté conversation, on AGIT dans un contexte** : créer, démarrer,
  générer, relier au CRM. Ces surfaces croisent les domaines — préparer un
  rendez-vous, c'est de l'agenda *plus* du CRM ; facturer, c'est des
  factures *plus* des contacts.
- **côté vue complète, on ADMINISTRE un domaine** : supprimer, régler,
  exporter, répondre au RGPD, choisir un modèle. Ces surfaces restent dans
  leur silo.

C'est un choix de conception, pas de la duplication. Il n'a simplement
jamais été nommé.

## Donc le problème n'est pas le nombre

Ce qui sature, ce n'est pas la quantité de surfaces : c'est que **des outils
différents portent le même nom, la même icône, et sont reliés par un bouton
qui laisse croire à un agrandissement** (« Ouvrir Agenda », « Ouvrir
Contacts »). On croit revenir au même endroit en plus grand, on arrive
ailleurs.

Le lot C de la 0.48 (« un mot par chose ») a normalisé le vocabulaire, mais
il a vérifié que chaque chose portait UN nom — pas qu'un nom désignait UNE
chose.

## Le remède, et ce qu'il n'est pas

**Ce n'est pas** une fusion. La revue de design l'a démontré sur l'Agenda :
fusionner aurait supprimé le rapprochement CRM et réintroduit BUG-143.

**C'est un travail de nom et de frontière** :

1. **Nommer chaque surface par ce qu'elle fait**, pas par son domaine.
   « Contacts » côté vue devient ce qu'elle est : la gestion des données
   personnelles. « Agenda » côté conversation devient « Préparer un
   rendez-vous ».
2. **Rendre le passage lisible.** Un bouton qui mène à un AUTRE outil ne
   doit pas dire « Ouvrir X » comme s'il agrandissait la même chose.
3. **Vérifier qu'aucun nom ne désigne deux choses**, par un test, comme le
   lexique 0.48 vérifie qu'aucune chose n'a deux noms. C'est l'exact
   symétrique, et il manque.

Coût sans commune mesure avec une refonte, et il touche la cause.

## Ce qui reste à décider

- Les noms eux-mêmes : c'est éditorial, ils appartiennent à Ludo.
- Le cap produit (application conversationnelle ou application à vues)
  n'est toujours pas tranché, et ce chantier ne le tranche pas — il rend
  simplement lisible ce qui existe.
