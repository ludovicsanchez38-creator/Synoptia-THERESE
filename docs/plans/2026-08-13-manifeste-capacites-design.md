# Manifeste de capacités — design V2 (13/08/2026)

> Chantier 0.44, fondation A. **V2 après NO-GO de la revue de design.**
> Ce que le NO-GO a changé est récapitulé en fin de document.
> Matière : inventaire multi-agents du 13/08 (178 capacités, 63 divergences
> confirmées sur cinq surfaces, plus une passe de complétude).

## Le problème, tel que l'inventaire l'établit

Un testeur dit ne pas savoir configurer un serveur MCP ni créer une commande. Les
deux existent. Le défaut n'est pas l'absence de fonctions, c'est qu'elles sont
introuvables — et que rien, dans le code, ne fait autorité sur ce qui existe.

**Sept consommateurs** déclarent aujourd'hui « ce que l'app sait faire », tous
tenus à la main, aucun dérivé d'un autre : le registre d'actions frontend (qui se
présente lui-même comme « la source de vérité UNIQUE »), les commandes codées en
dur du menu `/`, le registre de commandes backend, la fiche des raccourcis, le
centre des Capacités, la table des actions backend, et la palette active de la
coque. La liste des vues, elle, est redéclarée à **sept endroits**.

Ils divergent déjà : `files` manque à la table du backend, donc la vue qui porte
l'indexation et le RAG est absente de `{action: ouvrir …}` **et** de `/aide`.

## L'erreur de la V1, et la règle qui en découle

La V1 voulait que le manifeste **remplace** les registres. C'est intenable, pour
deux raisons établies dans le code.

**Les relations sont plusieurs-à-plusieurs.** La capacité « produire un document
Office » correspond à une action guidée, trois actions `produire`, et trois skills.
« Contacts et mémoire » couvre une vue, une recherche, une création, une commande
`/contact` et un scénario. À l'inverse, `settings.open` sert plusieurs capacités.
Un identifiant unique par capacité écraserait ces liens.

**Une partie du vocabulaire n'existe qu'à l'exécution.** Les commandes créées par
l'utilisateur, les skills découverts au démarrage, les outils installés sous
`~/.therese/tools` et les serveurs MCP branchés ne peuvent pas figurer dans un
fichier statique.

> **Règle du design V2 : une source de vérité ne veut pas dire un seul fichier
> pour tous les faits. Chaque FAIT a une autorité unique.** Le texte produit
> appartient au manifeste ; l'exécution appartient aux registres ; la
> disponibilité appartient à une évaluation à l'exécution ; les commandes
> utilisateur appartiennent à leur propre stockage.

Le manifeste ne remplace donc rien : **il relie**.

## Le modèle : trois objets, pas un

```ts
/** Ce que l'utilisateur cherche à FAIRE. Vocabulaire produit, stable. */
interface Capacite {
  id: CapabilityId;              // stable, jamais réutilisé après retrait
  famille: Famille;
  textes: TextesLocalises;       // fr-FR aujourd'hui ; jamais un identifiant
  maturite: 'complete' | 'partielle';
  audience: 'tous' | 'contributeur';
  entrees: EntrypointId[];       // les chemins ; l'accès principal est explicite
  exigences: RequirementId[];    // évaluées à l'exécution, pas documentaires
  limites?: string[];            // troncatures, plafonds, formats non lus
  cycle: { introduite: string; remplacee_par?: CapabilityId };
}

/** Un CHEMIN vers une capacité. Porte une référence typée au code réel. */
interface PointEntree {
  id: EntrypointId;
  capacites: CapabilityId[];     // un point d'entrée peut servir plusieurs capacités
  type: 'vue' | 'action' | 'commande' | 'raccourci' | 'scenario'
      | 'lien_profond' | 'ui_contextuelle' | 'outil' | 'api';
  binding: Binding;              // PAS une chaîne opaque
  principal?: boolean;
}

/** Le lien vérifiable avec l'existant. C'est lui qui rend le gate possible. */
type Binding =
  | { registre: 'action'; actionId: string }        // actionRegistry
  | { registre: 'vue'; view: AppView }
  | { registre: 'commande'; commandId: string }     // command_registry backend
  | { registre: 'raccourci'; actionId: string }     // via une action, jamais un callback nu
  | { registre: 'scenario'; scenarioId: string }
  | { registre: 'lien_profond'; parametre: string }
  | { registre: 'ui'; composant: string; testid: string }  // ancrage vérifiable
  | { registre: 'externe'; note: string };          // assumé non vérifiable
```

Cinq décisions portent ce modèle.

**Le `binding` référence un identifiant existant**, il ne le remplace pas.
`memory.open`, `/contact`, `AppView.memory` gardent leur nom dans leur espace. Le
manifeste établit le crosswalk.

**Un raccourci passe obligatoirement par une action.** C'est ce qui rend la règle
de gate tenable : aujourd'hui, un raccourci n'existe que si la coque passe un
callback optionnel au hook, ce qui est invérifiable statiquement — et c'est
précisément ainsi que quatre raccourcis fictifs ont pu être annoncés. En le faisant
pointer sur un `actionId`, on peut tester mécaniquement que la cible existe.

**L'accès principal est un champ**, pas « le premier de la liste ». Sinon l'ordre
du tableau devient un contrat caché.

**Les textes sont localisés dès le départ.** `nom` et `quoi` en français ne
doivent jamais devenir des identifiants fonctionnels — sinon toute traduction
casse le catalogue.

**Le cycle de vie est explicite** et les identifiants retirés sont réservés à vie.
Un `id` réutilisé ferait réapparaître une capacité morte dans un catalogue publié.

## La frontière statique / dynamique

Trois couches, et un agrégateur qui les fusionne avec une politique écrite.

| Couche | Autorité sur | Exemples |
|---|---|---|
| **Manifeste statique** | le vocabulaire produit et les capacités natives | vues, actions de navigation, familles, textes |
| **Registres exécutables** | ce qui s'exécute | `actionRegistry`, `command_registry`, hook clavier |
| **Contributions à l'exécution** | ce qui n'existe qu'installé | commandes utilisateur, skills, outils, serveurs MCP |

Une contribution à l'exécution porte un `parentCapabilityId` : un serveur MCP
branché s'affiche **sous** la capacité « Connecteurs », pas comme une capacité
autonome. Un skill se rattache à la capacité métier qu'il sert. Un skill ne devient
une capacité à part entière que s'il porte un résultat utilisateur durable et
distinct.

**Politique de collision, écrite plutôt que subie** : aujourd'hui le menu `/`
fusionne trois sources et donne silencieusement priorité au statique en cas de
collision d'identifiant. Le design retient l'inverse pour la disponibilité — une
commande réellement servie l'emporte sur une déclaration statique — et conserve la
provenance, affichée dans le rapport de dérive.

## Le fichier canonique

**Un seul fichier JSON, source neutre**, validé par schéma, importé par TypeScript
et embarqué par PyInstaller. Pas de génération TypeScript vers JSON.

Motif décisif, vérifié dans le pipeline de release : le sidecar PyInstaller est
construit **avant** que Node ne soit installé et que le frontend ne soit bâti. Un
générateur accroché au build frontend produirait un fichier que le sidecar ne
verrait jamais.

Emplacement : `src/backend/app/data/capacites.json` — `backend.spec` embarque déjà
tout `app/data`, et le sidecar bascule correctement sous `_MEIPASS`. Le backend le
lit par un chemin relatif au module, jamais depuis le bundle frontend ni le
répertoire courant de Tauri.

Le fichier porte une **version de schéma** et une **empreinte de contenu**,
comparées au démarrage. Un frontend et un sidecar issus de deux générations
différentes doivent le dire, pas diverger en silence.

## Les gates, réécrits pour être tenables

La V1 posait six règles dont trois étaient des vœux. Version tenable :

| Règle | Comment |
|---|---|
| Aucun `id` dupliqué, aucun `id` retiré réutilisé | lecture du fichier |
| Tout `binding` pointe une cible qui existe | les registres sont des structures énumérables |
| Tout raccourci cible une action existante | contrepartie directe du modèle |
| Aucune collision de combinaison de touches | normalisation puis comparaison |
| Toute vue de `AppView` est couverte | après passage d'`AppView` en constante dont le type dérive |
| JSON conforme au schéma, empreinte cohérente | validation + comparaison au démarrage |
| Chaque combinaison produit un effet réel | **test d'intégration** : monter la coque, envoyer la combinaison, observer |

Le dernier point est le seul qui teste une promesse faite à l'utilisateur contre le
code qui doit la tenir. Il coûte plus cher, il est le plus utile.

## L'ordre d'adoption

La V1 disait « les consommateurs en lecture seule d'abord ». C'est faux : le centre
des Capacités déclenche des scénarios, des vues et des prompts, et `/aide` écrit un
message persistant. Rien n'est en lecture seule.

1. **Schéma, espaces de noms et crosswalk**, sans migrer aucun consommateur.
2. **Génération et packaging**, avec empreinte vérifiée des deux côtés.
3. **Mode fantôme** : l'ancien et le nouveau calculent chacun leur sortie, un test
   compare. Aucun changement visible. C'est ce qui prouve la frontière
   statique/dynamique avant d'y toucher.
4. **Pilote : les vues et les actions de navigation**, le sous-ensemble le mieux
   délimité — et celui qui porte la divergence `files`.
5. Centre des Capacités et palette, avec tests de destination.
6. Menu `/` et table des actions backend.
7. Le rail en dernier.

## Ce qu'on ne fait pas dans ce jalon

**On ne corrige pas les divergences en même temps qu'on les déclare.** Le manifeste
doit d'abord dire la vérité, y compris désagréable. Mélanger description et
réparation rendrait impossible de savoir ce qui est décrit et ce qui est réparé —
c'est exactement ce mélange qui a produit deux NO-GO sur le lot précédent.

**Les promesses documentaires restent dehors.** Ce que le guide ou la landing
annoncent sans que le code le tienne ne va pas dans le manifeste : un registre de
promesses séparé, comparé au catalogue réel par un gate. Une promesse absente ne
doit jamais pouvoir remonter dans le rail, `/aide` ou le menu `/`.

**`sans_interface` disparaît du catalogue utilisateur.** Les fonctions sans écran
(étiquettes email, priorité manuelle, statistiques, rattachement d'un message à un
contact) restent visibles du mode contributeur et du rapport de dérive. Et une
fonction atteignable par la conversation n'est pas « sans interface » : son point
d'entrée est de type `outil`.

## Ce que le NO-GO a changé

| V1 | V2 |
|---|---|
| Le manifeste remplace les registres | il les **relie**, par un crosswalk plusieurs-à-plusieurs |
| Un objet `Capacite` avec un champ `acces` en chaînes | trois objets : `Capacite`, `PointEntree`, `Binding` typé |
| Le dynamique n'était pas traité | trois couches explicites + politique de collision écrite |
| `capacites.json` généré depuis le TypeScript | **fichier canonique neutre**, embarqué des deux côtés, empreinte comparée |
| Raccourci décrit par une chaîne de touches | raccourci **routé par une action**, donc vérifiable |
| Six règles de gate, dont trois invérifiables | sept règles tenables, dont une en test d'intégration |
| « Lecture seule d'abord » | **mode fantôme** d'abord ; rien n'est en lecture seule |
| Accès principal implicite (le premier) | champ explicite |
| Textes en français dans le modèle | textes localisés, jamais des identifiants |
| Pas de cycle de vie | `introduite` / `remplacee_par`, identifiants réservés à vie |
| `pending` et `partielle` confondus | deux axes : `maturite` (fonctionnelle) et disponibilité (à l'exécution) |

Deux inexactitudes de la V1 corrigées au passage : la table des consommateurs
comptait quatre surfaces frontend et deux backend, pas cinq sur six ; et la palette
active de la coque constitue un septième consommateur, oublié. Les presets MCP et
les skills font 38 entrées, pas 76.
