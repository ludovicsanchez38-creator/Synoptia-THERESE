# Plan - Le variateur du brief du jour

> Design challenge du 29/08/2026. Point de départ : l'intuition de Ludo sur les
> cycles, puis le témoignage de Perrine. Résumé de l'échange :
> `2026-08-29-de-l-intuition-cycles-a-la-capacite-du-jour.md` (bureau de Syn).
>
> **Ce document remplace la fonctionnalité décrite dans ce résumé.** Grok et Soso
> ont été saisis séparément sur sept questions écrites pour tuer la proposition,
> pas pour la confirmer. Les deux l'ont refusée telle qu'elle était décrite.

## En une phrase

Il reste un variateur : trois mots, dans l'en-tête du brief, qui règlent combien
de lignes le brief développe le matin. Rien ne se cache, rien ne se stocke, rien
ne parle au modèle. Le journal de capacité, le champ libre et la promesse de
rattraper une baisse d'énergie sortent tous les trois.

## 1. Ce que les deux verdicts refusent

| Ce que j'avais décrit à Ludo | Verdict |
|---|---|
| Trois pastilles muettes (haute / moyenne / basse) | **Refusé par les deux.** « Des petits dessins sans nom, je n'ose pas » est exactement la plainte de la campagne du 28/08. Soso ajoute le point le plus dur : si seule « basse » a un effet, moyenne et haute sont **deux commandes placebo**, donc la rechute du motif que la 0.56 vient de fermer (un contrôle qui affirme sans geste correspondant). |
| Un champ de texte libre optionnel | **Refusé par les deux.** Zéro effet produit, et la donnée la plus intime de l'application. Les gens y écriraient la cause. Selon son contenu, c'est une donnée de santé ; la CNIL recommande de ne pas collecter une donnée sensible dont on peut se passer. SQLCipher protège le disque, pas les exports, les journaux, les sauvegardes ni un partage d'écran. |
| Réduire le brief à 2 éléments | **Refusé sous cette forme.** Couper sans le reste, c'est cacher une facture en retard. |
| Le mot « capacité » | **Refusé par les deux.** Le mot interprète déjà un état du corps. Grok : nommer l'action sur le brief, pas un état. |
| « S'adapte à ta journée » | **Refusé par les deux.** Le clic exige la conscience que le témoignage dit absente. Une fonction ne rattrape pas une baisse qu'elle ne détecte pas ; elle enregistre un geste déjà fait. |

## 2. Ce que le code dit (vérifié, pas supposé)

Trois de mes affirmations étaient fausses. Elles sont corrigées ici.

1. **Le brief n'affiche pas 9 éléments, il en affiche 6.** `TodayDashboardCard.tsx:83`
   fait `items.slice(0, 6)`, puis `:211` propose « Voir les N autres éléments ».
   Mon « 2 au lieu de 9 » était un chiffre inventé. **Le mécanisme de repli
   existe donc déjà** : le variateur ne fait que déplacer le seuil.
2. **Le sous-titre compte `items.length`, pas les éléments visibles**
   (`:100`). Il dit donc déjà la vérité quand la liste est repliée. Si on
   coupait `items` au lieu de `visibleItems`, ce sous-titre mentirait.
3. **`buildTodayAttentionItems` n'ordonne pas par urgence** mais empile des
   catégories dans un ordre fixe (`prototypeReadModels.ts:149-170`). Les retards
   (tâches, relances, factures) sont bien en tête, mais entre eux l'ordre est
   celui des catégories, pas celui de la gravité.
4. **`GET /api/data` exporte toutes les `Preference` verbatim.** La sérialisation
   (`data.py:229-238`) ne caviarde que les clés contenant `api_key`. Toute valeur
   posée dans `Preference` part dans l'export RGPD, en clair.
5. **`HomeView` et `TodayPanels` sont orphelins** (aucun import hors commentaires
   et tests). Un second brief non branché est une terre à régression pour
   exactement ce chantier.

## 3. Le geste, nommé honnêtement

Dans l'en-tête de la carte « Ton attention aujourd'hui », un `radiogroup` visible,
avec les trois mots écrits :

> **Aujourd'hui, montre-moi :  tout  /  l'essentiel  /  le minimum**

| Valeur | Effet | Défaut |
|---|---|---|
| tout | développe toute la liste | |
| l'essentiel | développe 6 lignes, le reste replié | **oui, comportement actuel inchangé** |
| le minimum | développe 2 lignes, le reste replié | |

**Pourquoi trois valeurs et pas deux.** Soso n'a pas refusé trois niveaux : il a
posé une condition, « seulement si chacun produit un effet distinct, observable et
sûr ». Trois seuils (tous / 6 / 2) la remplissent. Ce n'est pas un compromis entre
les deux verdicts : c'est la condition de Soso appliquée à la proposition de Grok.
Et « l'essentiel » étant le comportement d'aujourd'hui, **personne ne voit de
changement sans avoir fait un geste**.

**Pourquoi ces mots-là.** Ils décrivent l'action sur le brief, pas un état de la
personne. Conséquence directe : la commande peut vivre dans l'en-tête de l'accueil
sans rien révéler pendant un partage d'écran avec un client. C'était l'objection
de Grok contre « privé + en-tête », et le changement de vocabulaire la supprime.

## 4. L'arbitrage que Grok et Soso n'ont pas tranché

Les retards, en mode « le minimum ».

- **Soso** : « Aucun élément en retard ne disparaît silencieusement. S'il y en a
  cinq, le mode concentré peut dépasser deux. »
- **Grok** : « 2 visibles + N autres » suffit.

**Je tranche pour le seuil mécanique, avec l'annonce que Soso réclame** : le
bouton de repli devient, quand X > 0 :

> « Voir les 7 autres éléments, **dont 2 en retard** »

Le seuil reste mécanique (donc prévisible, donc testable), et rien ne disparaît
en silence. Un seuil qui s'étire tout seul selon le contenu est un second
algorithme d'urgence dans une carte qui n'en a déjà pas un bon.

**Règle bouton / réglage** : « Voir les N autres » reste une expansion ponctuelle,
valable pour la session. Elle **ne modifie pas** le réglage.

## 5. Périmètre, dans l'ordre

**Lot 0 - retirer les orphelins (une heure).** `git rm` sur `HomeView.tsx`,
`TodayPanels.tsx` et `TodayPanels.test.tsx`. Aucun import hors commentaires. On ne
touche pas au brief avec un second brief mort dans le dépôt.

**Lot 1 - le variateur (une journée).** Le `radiogroup`, les trois seuils, le
libellé « dont X en retard », l'état en `localStorage` avec la date civile pour
clé, `try/catch` autour de chaque lecture et écriture.

- La clé de jour vient de `data.date` (le payload de `/dashboard/today`), **jamais**
  d'un `new Date()` côté React. C'est la leçon BUG-125, et c'est ce qui garantit
  que l'accueil et le backend parlent du même jour.
- Valeur du jour précédent : ignorée, le réglage repart sur « l'essentiel ».
- Aucune migration, aucune colonne, aucun endpoint.

**Lot 2 - les garanties (une demi-journée).** Voir section 6.

Trois jours au total, lot 2 compris. Cette marge n'ouvre pas un quatrième lot.

## 6. Les garanties, et ce qu'elles valent vraiment

Ma proposition initiale disait « un test vérifie que la valeur n'entre dans aucun
prompt ». Soso : **« Chercher une chaîne dans un prompt est un détecteur de fumée,
pas une garantie. »** Elle rate une reformulation, une valeur dérivée, un second
tour d'outil, et la fuite par le nombre d'éléments. La propriété à tester est la
**non-interférence** :

> À message, historique et données métier identiques, ce qui part vers le modèle
> doit être identique quelle que soit la valeur du variateur.

Ce que ça donne ici, où la valeur ne quitte jamais React :

1. **Test d'architecture** : le module du variateur n'est importé ni par `chat`,
   ni par `llm`, ni par `memory`, ni par `tools`, ni par `board`, ni par
   l'extracteur d'entités.
2. **Test de sortie** : aucun corps de requête émis par l'application ne porte la
   valeur (le brief reste servi complet par le backend, la réduction est une
   projection d'affichage).
3. **Test de défaut** : sans geste, le rendu est identique à celui d'aujourd'hui.
4. **Test de non-disparition** : en mode « le minimum » avec des retards, le
   bouton annonce le nombre de retards repliés.

**Le point le plus important, et c'est Grok qui le nomme** : le brief n'est pas
une fuite aujourd'hui parce que le modèle ne le lit pas (`/dashboard/today` ne
passe par aucun LLM ; le chat reconstruit son contexte par ses outils). Le jour où
quelqu'un « alignera » le chat sur le brief réduit, il y aura soit une fuite, soit
un assistant qui ratifie sept échéances invisibles. **Ce jour-là est interdit, et
le test d'architecture est là pour le rendre bruyant.** « Résume ma journée » doit
toujours lire les données complètes.

## 7. Ce qui sort, et c'est définitif pour cette tranche

- **Le champ de texte libre.** Pas « plus tard » : il ne revient que si une
  finalité et une restitution explicites le justifient, ce qui n'est pas le cas.
- **Tout historique.** Une valeur, une date, écrasée le lendemain. Pas de ligne par
  jour, pas de courbe, pas de « tu étais basse 12 fois ». Sans restitution, une
  accumulation est un cimetière de données, et c'est déjà un historique de
  bien-être même sans écran pour le lire. Le jour où quelqu'un demandera la
  courbe, la réponse est non.
- **Toute persistance en base.** Vérifié : `Preference` part verbatim dans
  l'export RGPD. Rien tant que le lot 1 n'a pas servi deux cycles de testeurs.
- **Le mot « capacité »**, et toute formule qui promet une adaptation.
- **Le refus de « Décider » pour la journée** (l'idée qui colle le mieux au
  témoignage de Perrine). Grok est net : c'est une nouvelle discussion, pas la
  suite naturelle de celle-ci.
- **Le second calendrier**, déjà mis de côté par Ludo, et qui ressuscitait par
  ce chemin.

## 8. La phrase vraie

Grok la formule mieux que moi, et c'est le test de la fonctionnalité :

> « Tu choisis combien le brief te montre aujourd'hui. Le reste de l'app, non. »

Ce qu'elle ne dit pas, et qu'il faut assumer : elle ne détecte rien, elle ne
s'adapte à rien, elle ne rattrape aucune baisse. Elle sert un homme fatigué, une
nuit blanche, une femme qui a mal, quelqu'un qui sort d'un Board pourri. C'est
légitime. Un module qui interpréterait un corps ne l'est pas.
