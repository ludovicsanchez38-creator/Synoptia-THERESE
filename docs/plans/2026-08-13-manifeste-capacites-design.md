# Manifeste de capacités — design (13/08/2026)

> Chantier 0.44, fondation A. À faire challenger AVANT la première ligne de code.
> Matière : inventaire multi-agents du 13/08 (178 capacités, 70 divergences relevées
> sur cinq surfaces, plus une passe de complétude).

## Le problème, tel que l'inventaire l'établit

Un testeur dit ne pas savoir configurer un serveur MCP ni créer une commande. Les
deux existent. Le défaut n'est pas l'absence de fonctions, c'est qu'elles sont
introuvables — et que rien, dans le code, ne fait autorité sur ce qui existe.

Trois constats structurels, tous ancrés :

**Cinq registres concurrents** déclarent « ce que l'app sait faire », tous tenus à
la main, aucun dérivé d'un autre : le registre d'actions frontend (qui se présente
lui-même comme « la source de vérité UNIQUE »), les 21 commandes codées en dur du
menu `/`, le registre de commandes backend, la fiche des raccourcis, et le centre
des Capacités. La liste des vues, elle, est redéclarée à **sept endroits**.

**Ils divergent déjà.** `files` manque à la table du backend : la vue qui porte
l'indexation et le RAG est absente de `{action: ouvrir …}` **et** de la réponse de
`/aide`. Quatre raccourcis sont annoncés sans exister ; deux raccourcis réels ne
sont annoncés nulle part.

**La porte d'entrée du catalogue existant est invisible.** Le bouton « Capacités »
vit dans le composeur de l'accueil : il disparaît dès qu'une conversation ou une
vue est ouverte. Le rail permanent, lui, ne compte qu'une seule vue métier, sous un
nom qui n'est pas le sien.

## Ce que le manifeste EST, et ce qu'il n'est pas

**Il est déclaré, pas scrapé.** Un scanner ne peut pas décider qu'une route est une
capacité, ni qu'une intention comme « Brief du jour » en est une. Il ne peut pas
davantage écrire un nom lisible ni un cas de test. Le manifeste est donc écrit à la
main, typé, et versionné avec le code.

**Il est la source, pas une copie.** Les menus, l'aide, la fiche de commandes, le
centre des Capacités et la table des actions du backend en sont **dérivés**. Un
registre qui subsisterait en parallèle recommencerait à diverger.

**Le scanner devient un rapport de dérive**, pas une source : il vérifie que toute
surface enregistrée porte un identifiant du manifeste, et signale les orphelins.

## Le contrat d'une entrée

```ts
interface Capacite {
  id: string;                    // stable, jamais renommé — c'est la clé de tout
  nom: string;                   // lisible par un non-technicien, tel qu'affiché
  quoi: string;                  // une phrase, du point de vue de l'utilisateur
  famille: Famille;              // regroupement affiché (Quotidien, Documents, …)

  acces: Acces[];                // TOUS les chemins, pas seulement le principal
  prerequis: Prerequis[];        // ce qu'il faut avoir configuré avant
  limites?: string[];            // troncatures, plafonds, formats non lus

  etat: 'disponible' | 'partielle' | 'sans_interface' | 'contributeur';
  cas_de_test?: CasDeTest;       // ce que le testeur déroule, et ce qu'il doit voir
}

type Acces =
  | { type: 'rail'; libelle: string }
  | { type: 'palette'; terme: string }
  | { type: 'raccourci'; touches: string }
  | { type: 'commande'; slash: string }
  | { type: 'action'; expression: string }   // {action: ouvrir …}
  | { type: 'dans_vue'; vue: string; ou: string };  // bouton à l'intérieur d'une vue
```

Quatre décisions portent ce contrat.

**`acces` est une liste, pas un champ.** L'inventaire montre qu'une même capacité
s'atteint par le rail, la palette, un raccourci, une commande et une action, avec
des libellés différents à chaque fois. Un champ unique forcerait à choisir, et
c'est ce choix arbitraire qui produit les divergences actuelles.

**`etat: 'sans_interface'` est un état de première classe.** L'inventaire a trouvé
des fonctions au backend complet et au client API écrit, sans aucun consommateur :
étiquettes email, priorité manuelle, statistiques de boîte, rattachement d'un
message à un contact, installation d'outils sur mesure. Les taire reviendrait à
maintenir la fiction ; les annoncer comme disponibles serait mentir. On les
déclare, on dit qu'elles n'ont pas d'écran, et le rapport de dérive les compte.

**`limites` est obligatoire dès qu'il en existe une.** PDF plafonné à 100 pages,
CSV à 500 lignes, XLSX sans plafond, pièce jointe rejouée sur 3 tours et 4 fichiers,
13 extensions acceptées mais illisibles. Aucune n'est annoncée aujourd'hui.

**`cas_de_test` est écrit pour un humain, pas pour pytest.** C'est la demande
explicite du testeur : « présenter des cas de test pour permettre le test et en
même temps l'apprentissage ». Un test unitaire ne remplit pas cet office.

## Ce qui en est dérivé, et dans quel ordre

| Consommateur | Ce qu'il prend | Remplace |
|---|---|---|
| Centre des Capacités | tout, groupé par famille | sa liste écrite à la main |
| Réponse de `/aide` | nom, quoi, premier accès | sa table de onze destinations |
| Menu `/` | les accès de type `commande` | ses 21 entrées codées en dur |
| Fiche des raccourcis | les accès de type `raccourci` | sa liste de 21, dont 4 fictifs |
| Table des actions backend | les accès de type `action` | sa table sans `files` |
| Rail de navigation | les capacités marquées `epingle` | ses sept boutons figés |

**Ordre d'adoption imposé par le risque** : d'abord les consommateurs en lecture
seule (Capacités, `/aide`, fiche des raccourcis), qui ne peuvent rien casser. La
table des actions backend et le menu `/` ensuite, car ils exécutent. Le rail en
dernier, c'est le plus visible.

## Où il vit

**Côté frontend**, en TypeScript : `src/frontend/src/lib/capacites/`. Motif : cinq
des six consommateurs sont frontend, le typage y est vérifié par `tsc`, et le rail
comme la palette ne peuvent pas attendre un appel réseau pour s'afficher.

Le backend en a besoin pour deux choses seulement : la réponse de `/aide` et la
table des actions. Il les obtient par un **fichier généré** (`capacites.json`),
produit par un script et vérifié en CI — pas par un appel HTTP, qui ferait dépendre
une réponse de chat de la disponibilité du frontend.

## Le gate anti-dérive

Un test qui échoue si :

1. deux capacités portent le même `id` ;
2. un `id` référencé par une surface n'existe pas dans le manifeste ;
3. une vue déclarée dans `AppView` n'a aucune capacité qui la cible ;
4. un accès de type `raccourci` n'a pas de gestionnaire correspondant — c'est ce
   qui a laissé passer les quatre raccourcis fictifs ;
5. un accès de type `commande` ne correspond à aucune commande servie ;
6. `capacites.json` diverge du manifeste TypeScript.

Le point 4 est le plus important : c'est le seul qui teste une promesse faite à
l'utilisateur contre le code qui doit la tenir.

## Ce qu'on ne fait pas dans ce jalon

**On ne corrige pas les divergences en même temps qu'on les déclare.** Le manifeste
doit d'abord dire la vérité, y compris désagréable. Corriger et déclarer dans le
même lot rendrait impossible de savoir ce qui est décrit et ce qui est réparé — et
c'est exactement le mélange qui a produit deux NO-GO sur le lot précédent.

Les divergences deviennent une liste de correctifs, traitée dans un jalon suivant,
par ordre de gêne pour le testeur.

**On ne touche pas au rail** avant que les consommateurs en lecture seule ne soient
livrés et vérifiés.

## Questions ouvertes, à trancher avant de coder

1. **Le centre des Capacités connaît un état `pending` avec un motif.** Faut-il le
   fusionner avec `etat: 'partielle'`, ou garder deux notions ?
2. **`sans_interface` doit-il être visible par l'utilisateur final**, ou réservé au
   mode contributeur et au rapport de dérive ? Annoncer une capacité inatteignable
   peut frustrer plus qu'informer.
3. **Les 19 presets MCP et les 19 skills** : une capacité chacun (76 entrées, illisible)
   ou une capacité « connecteurs » avec une liste dérivée du registre ?
4. **Le manifeste doit-il porter les capacités absentes mais promises ailleurs**
   (guide utilisateur, landing) ? Elles n'existent pas dans le code, mais l'écart
   est précisément ce qui trompe les testeurs.
