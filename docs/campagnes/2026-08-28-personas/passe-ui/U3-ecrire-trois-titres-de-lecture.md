# U3 - Cliquer « Écrire » affiche TROIS libellés qui parlent de lecture

Le constat O2 (établi à la lecture du code) ne relevait qu'un titre accessible.
**La capture d'écran en montre trois, tous visibles.**

- **Gravité** : majeur (requalifié à la hausse — l'analyse de code seule
  sous-estimait)
- **Nature** : defaut_app (dérive de nommage)
- **Source** : constaté à l'écran, v0.53.0, navigateur réel

## Ce que l'utilisateur voit après avoir cliqué « Écrire »

| Emplacement | Texte affiché |
|---|---|
| Sous-titre de l'accueil | « Je **consulte** la boîte connectée. Tu peux **lire** un message et préparer un brouillon sans l'envoyer. » |
| Carte du parcours, colonne gauche | « **Messages à consulter** » / « **Lecture** de la boîte connectée » |
| Titre du canevas, colonne droite | « **Lecture** et brouillon » / « Le message reste en **lecture seule**. » |

Le verbe cliqué est **Écrire**. Les trois titres qui répondent parlent de
consultation. Sur un écran vide (aucun compte connecté), la carte affiche même
« Aucun compte email connecté / Configurer Email » — alors que l'entrée 10 avait
précisément pour but d'ouvrir une rédaction sans compte.

## Pourquoi c'est plus grave que ce que le code laissait voir

En lisant le source, j'avais relevé un seul écart (`scenarioLabels.email`,
le titre accessible du canevas) et classé le tout en **mineur** après la
contre-expertise, qui avait raison de corriger ma prémisse fausse sur le prompt.

À l'écran, l'écart est partout où l'œil se pose. C'est une illustration nette
de ce qu'une campagne sans navigateur ne peut pas peser : **la densité d'un
défaut de nommage ne se lit pas dans un fichier, elle se voit sur l'écran.**

## Trois personas l'avaient rencontré sans pouvoir le nommer

- Le médecin : « Sur l'accueil, *Écrire* ouvre une rédaction de mail. Si
  *Écrire* veut dire e-mail, qu'on l'écrive. »
- Le responsable administratif : « Le bouton *Écrire* ne m'a pas mené à un
  courrier. Il m'a parlé de Gmail et d'IMAP. »
- Le formateur, dont c'était le sujet : « repérer tous les endroits où deux mots
  différents désignent la même chose ».

## Correctif

Les trois libellés doivent nommer une rédaction, et le gate de lexique
(`lexiqueTitres.test.ts`) doit couvrir `scenarioLabels`, `scenarioPrompts` et
les sous-titres de carte — aujourd'hui il ne voit aucun des trois.
