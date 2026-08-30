# Deux personas sur la 0.59.0 - artisan et avocate

> 30 août 2026. Question de Ludo : « THÉRÈSE est une appli publique, ce que je
> viens de faire à partir de MES données ne lèse pas les autres entreprises ? »
> Deux personas joués sur une instance neuve, par l'API, sans complaisance.

## Verdicts

**Karim Belhadj, plombier-chauffagiste à Vénissieux** : *non, il ne rouvre
pas.*

**Maître Inès Ferrand, avocate en droit de la famille à Nantes** : *non, elle
ne rouvre pas.*

## Ce qu'ils ont trouvé et qui a été corrigé le jour même

| Défaut | Qui l'a vu |
|---|---|
| Le délai de suivi « réglable » que **rien ne permettait de régler** (`echeance_de_suivi` n'a jamais reçu son paramètre `jours`). Le défaut de `next_follow_up` corrigé le matin, réintroduit le soir. | l'artisan |
| La **phase posée d'office à « piste »**. « Une fuite sous un lavabo n'est pas une piste. C'est un client qui a de l'eau par terre et qui m'appelle. » | l'artisan |
| Le **blocage d'agenda qui disparaissait à la relecture** : posé sur la route d'écriture, absent de `CalendarEventResponse`. « Si je m'en remets à l'agenda demain matin, je me présente au tribunal pour une audience qui n'existe plus. » | l'avocate |

Les trois sont du même motif : l'application affirmait ce qu'elle ne faisait
pas. Deux étaient des régressions de la nuit même.

## Ce qu'ils ont trouvé et qui n'est PAS corrigé

**Le vocabulaire des phases est commercial.** Les deux ont buté au même
endroit, indépendamment.

- Karim veut : devis envoyé, devis signé, chantier, réception, facturé.
- Maître Ferrand veut : assignation, mise en état, audience, jugement, appel.
  « Un divorce, on ne le *gagne* pas. Les enfants non plus. »

**Le carnet est commun, et le mode cabinet est éteint par défaut.** Les deux
personas ayant tourné sur la même instance, l'avocate a vu les clients du
plombier : « Claire Dupont, Sylvie Morel et le syndic Foncia vivent dans la
même pièce. Pour une profession tenue au secret, c'est éliminatoire. Vous le
savez, puisque le réglage existe. Vous l'avez laissé fermé. » C'est un des
sept écarts de la campagne des dix personas, toujours en attente d'arbitrage.

**Ce qui manque, par métier**

- Artisan : adresse du chantier (le syndic n'habite pas la copropriété),
  urgence, TTC, lien devis ↔ chantier, numéro de sinistre, expert, photos.
- Avocate : numéro RG, juridiction et chambre, partie adverse et son conseil
  comme des personnes, audiences rattachées au dossier, délais de procédure,
  aide juridictionnelle en unités de valeur, convention d'honoraires.

**Le score commercial appliqué à tout le monde.** « Mme Morel n'est pas un
lead. C'est une fuite. » / « Claire Dupont n'est pas un lead. Lui coller un
score commercial dans le dossier, sous le secret, c'est indécent. »

## La seule chose qui leur a plu, et c'est la même

La consigne du contrat de lecture, qui interdit au modèle de trancher entre
deux notes contradictoires.

L'avocate : « Ça, c'est la seule phrase de tout le produit qui parle ma langue.
En famille, deux versions s'affrontent. Un modèle qui *tranche* fabrique un
faux. Je ne veux pas d'un outil qui décide qui a les enfants. »

## Ce que la campagne enseigne sur la méthode

Concevoir une nuit entière à partir d'un seul jeu de données — même réel,
même riche — produit une application qui parle le métier de son propriétaire.
Le matériau réel est un excellent révélateur de manques ; c'est un mauvais
juge de généralité.
