# Préparation v0.49.0-alpha — « ce qui est annoncé se produit »

> Branche `feat/ux-p4-noms`, 14 commits, 128 fichiers.
> Point de départ : Ludo, en regardant l'app — « je trouve qu'il y a trop
> d'interfaces ».

## Le diagnostic, et les deux hypothèses écartées

**Écartée par le code n°1 : « six capacités existent en double, fusionnons ».**
La comparaison des ACTIONS de chaque paire montre qu'aucune ne partage son
travail. Côté conversation on AGIT dans un contexte, en croisant les domaines
(préparer un rendez-vous rapproche les participants des contacts et enregistre
une note CRM) ; côté vue complète on ADMINISTRE un domaine (supprimer, régler,
RGPD). Fusionner aurait supprimé du métier — et réintroduit BUG-143, puisque
`CalendarPanel` lit les calendriers sans `createDefault: false`.

**Écartée n°2 : « il y a trop d'écrans ».** Le nombre n'est pas la cause. Une
capacité centrale mérite d'être joignable de partout.

**La cause réelle : rien ne se comportait comme annoncé.**

| Ce qui était annoncé | Ce qui se passait |
|---|---|
| « Retour » | traversait deux écrans non demandés, trois gestes pour en fermer un |
| Une autorité unique pour Échap | `resolveEscape` n'avait **aucun appelant** ; 14 composants lui déléguaient par commentaire |
| La commande « Conversations » | basculait un drapeau que la coque n'observe pas |
| Une carte du tiroir | posait une phrase et n'ouvrait rien avant validation |
| « Aucune priorité détectée » | pouvait signifier une panne de lecture, présentée comme un écran vide |
| Les noms | « Agenda » dans le tiroir, « Calendrier » une fois ouvert |

## Ce que la version corrige

**Navigation.** Le store démarrait sur la vue `home` — l'ancien tableau de
bord — que plus rien n'affiche au lancement ; la pile mentait dès l'ouverture.
`activeView` accepte désormais `null` : « aucune vue embarquée » est un état
réel, il lui manquait un nom. Le retour prend un geste.

**Échap.** `resolveEscape` retiré après comparaison de ses onze branches à la
cascade réelle : toutes couvertes, et sept ne pouvaient PAS l'être ailleurs
(états locaux invisibles aux stores). La coque se déclare autorité, les
quatorze commentaires disent la vérité, et deux tests Python qui protégeaient
un contrat *sur du code mort* portent enfin sur le lieu réel.

**Perte de données.** Un fichier joint à un projet partait au premier clic.
Confirmation en ligne fail-closed — le mécanisme commun `requestExternalAction`
a été écarté sciemment : il est fail-OPEN par conception.

**Pannes.** `setup-status` renvoyait `False` quand une lecture échouait :
l'écran demandait de brancher un agenda déjà branché. Il nomme désormais ce
qu'il n'a pas pu vérifier, et l'écran le dit.

**Cartes.** Les 20 destinations de navigation s'ouvrent au clic. Les 3 cartes
de type `prompt` gardent leur relecture avant envoi — vérifié par un sabotage
dédié.

**Cohérence.** 133 indicateurs de chargement en 38 formes → un composant, trois
tailles nommées par leur usage. 229 couleurs figées → tokens du thème.

**Lisibilité.** Recette visuelle dans l'app : les cinq verbes de l'établi
étaient en 12 px, la taille de « Connecté » et des mentions de bas de page. La
hiérarchie passe de deux niveaux utiles à cinq. Sept boutons de passage encore
en « Ouvrir X » ont été trouvés à l'écran, qu'aucun grep n'avait montrés.

## Revue

Le plan a été challengé AVANT écriture : **NO-GO, six objections**, dont trois
contre-vérifiées à la main — et la revue avait raison sur les trois. Ce que le
plan V1 affirmait à tort : un comptage de fermetures mal classé, un « cliquer
ne produit rien » faux (il y a bien un retour visuel), et une correction de
sécurité qui s'appuyait sur un mécanisme fail-open.

## Dette assumée

- **257 champs de formulaire** stylés à la main face à quatre primitives
  (`Input`, `Textarea`, `Select`, `FormField`) importées par **zéro** fichier.
  Migration non mécanique : chaque champ a ses props et ses handlers.
- 62 autres états vides, dont la plupart sont légitimes ; ceux des écrans de
  configuration mériteraient le même traitement que les tâches.
- Rôle ARIA des six panneaux (`dialog` au lieu de `region`) : demande une
  vérification en navigateur, jsdom n'implémente pas `inert`.
- Les couleurs de CATÉGORIE (email bleu, appel vert, rendez-vous violet) ne
  sont pas touchées : les mapper sur des tokens d'état dénaturerait leur sens.
