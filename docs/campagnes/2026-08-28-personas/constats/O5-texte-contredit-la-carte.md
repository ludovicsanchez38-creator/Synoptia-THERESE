# O5 - Le texte de l'assistante annonce l'action faite ; la carte, elle, attend encore

**Rencontré par au moins deux personas** :

- Persona 01 (médecin) : « La réunion trimestrielle **a été programmée** dans
  votre calendrier » **et**, juste en dessous, une carte *Confirmer la création
  du rendez-vous* avec un bouton *Créer*. L'événement n'existait pas avant le
  clic — elle l'a vérifié par l'API.
- Persona 04 (avocat, en cours) : « le modèle affirme que le courrier est
  parti, alors que je n'ai pas cliqué ».

- **Gravité** : majeur
- **Nature** : `limite_modele_local` en cause, `friction_ux` en effet
- **Source** : `routers/chat.py:2824-2878`, `components/…/ToolConfirmationCard.tsx`

## Le backend fait sa part

Le protocole est correct et explicite. Quand un outil sensible est intercepté,
le résultat renvoyé AU MODÈLE dit :

```
"Action préparée et en attente de validation de l'utilisateur.
 NE PAS la considérer comme exécutée : l'utilisateur doit confirmer."
```

Et le journal a même été corrigé pour ne plus induire en erreur
(`chat.py:2820-2823`) : « BUG-121 a été mal lu parce que le log "Executing
tool: send_email" laissait croire à un envoi réel ».

Le modèle local reçoit donc l'information, et l'ignore.

## Mais l'écran laisse les deux versions cohabiter

Le texte du modèle et la carte de confirmation s'affichent **côte à côte, au
même niveau**, et rien n'arbitre. L'utilisateur lit d'abord la phrase — c'est
une phrase, elle se lit — et la carte ressemble à une redite.

Le médecin l'a formulé exactement : « Si j'avais répondu "oui" dans le champ au
lieu de cliquer *Créer*, je serais partie en croyant que c'était posé. »

C'est le point qui rend ce constat produit et pas seulement modèle : **on ne
peut pas empêcher un modèle de se tromper, on peut empêcher l'écran de lui
donner raison.** Et THÉRÈSE vise explicitement les petits modèles locaux : c'est
même son argument de souveraineté.

## Correctif attendu

Aucun n'exige de toucher au modèle :

1. Tant qu'une confirmation est en attente pour ce tour, **marquer le texte du
   modèle comme non fiable sur ce point** — le griser, ou le faire précéder de
   la carte, ou afficher « ceci n'est pas encore fait » à côté du bouton.
2. La carte doit dominer visuellement le message, pas le suivre.
3. Traiter un « oui » tapé dans le composeur pendant qu'une confirmation est en
   attente : soit il vaut confirmation (explicitement, en le disant), soit
   l'écran rappelle qu'il faut cliquer. Aujourd'hui il ne fait ni l'un ni
   l'autre, et l'utilisateur croit avoir validé.

## Le test qui manque

Un test d'écran : quand `confirmation_required` est émis, l'assertion porte sur
ce que l'utilisateur PEUT CROIRE, pas seulement sur la présence de la carte.
