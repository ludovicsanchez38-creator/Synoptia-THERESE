# Protocole — campagne cinq personas, THÉRÈSE 0.61.0-alpha

> Demandée par Ludo le 30/08/2026, après quatre essais à la main dont **trois
> ont cassé** pendant que 2632 tests backend, 1189 tests frontend et un audit
> graphique sur 17 surfaces étaient tous verts. Les tests mesuraient
> l'apparence et des unités ; personne ne mesurait si ça FONCTIONNE.

## Ce qui change par rapport aux campagnes précédentes

**Le modèle est bon.** Les campagnes des 28 et 29/08 tournaient sur
`qwen3:8b` en local, ce qui obligeait à distinguer `limite_modele_local` de
`defaut_app`. Ici le modèle est **gpt-5.6-luna en effort bas** (cloud), choisi
par Ludo pour le coût. **Cette distinction disparaît** : si ça casse, c'est
l'application. La colonne « Nature » n'accepte plus que `defaut_app` ou
`friction_ux`.

**La couverture est exhaustive.** Le persona 1 balaie TOUT. Les quatre autres
traversent en usage ce qu'il voit en inventaire.

## L'application

Instance neuve, isolée, à toi seul :

- URL : `http://127.0.0.1:17941`
- En-tête obligatoire : `X-Therese-Token: <TOKEN>` (donné dans ton brief)
- Routes : `GET /openapi.json` — 296 endpoints exposés
- Dossier de données : isolé, vide au départ. Tu pars d'une installation neuve.

Tu disposes de **deux** moyens et tu dois utiliser **les deux** :

1. **L'API**, pour exécuter réellement les parcours.
2. **Le code de l'interface** (`src/frontend/src/`), que tu LIS pour savoir ce
   que l'utilisateur voit : libellés, écrans, enchaînements, messages d'erreur.
   Composant central : `components/prototype/ConversationCanvasPrototype.tsx`.

**Dis toujours de laquelle des deux sources vient un constat.**

## Interdictions — elles ne se discutent pas

- `POST /api/config/llm`, `/api/config/api-key` et tout changement de
  configuration du modèle. La clé est fournie par Ludo et sera révoquée : tu
  n'y touches pas, tu ne la lis pas, tu ne l'écris nulle part.
- Toute écriture hors de ton fichier de rapport. Tu ne modifies **aucun
  fichier du dépôt**.
- Toute commande `git`.
- Tout envoi réel vers l'extérieur : e-mail, webhook, appel à un tiers.
- Réparer ce que tu trouves. Tu constates, tu ne corriges pas.

## Tu ne t'arrêtes pas à la première panne

**C'est la règle la plus importante de cette campagne.**

Un défaut constaté n'est pas une raison de s'arrêter, c'est une ligne de plus
dans ton rapport. Tu le notes, tu le contournes, **tu continues**.

- Une fonctionnalité casse ? Tu la fiches et tu passes à la suivante.
- Un parcours est bloqué au troisième pas ? Tu fiches le blocage, puis tu
  attaques les pas suivants **par un autre chemin** : l'API directement, une
  autre commande, un état préparé à la main. Tu n'abandonnes le parcours que
  si aucune porte n'existe, et tu le dis.
- Dix défauts d'affilée ? Tu en fiches dix et tu continues. Le nombre n'est
  pas un signal d'arrêt.

**Ce qui justifie de t'arrêter, et rien d'autre :** le serveur ne répond plus,
ton jeton est refusé, ou le modèle est indisponible. Dans ces trois cas
seulement, tu écris `HARNAIS ?` en tête de ton rapport, tu décris ce que tu
observes, et tu t'arrêtes. Tu ne répares rien.

**Ton livrable, c'est la COUVERTURE.** Un rapport avec quatre défauts
magnifiques sur 20 % du périmètre est un rapport raté. Un rapport avec quatre
défauts sur 100 % du périmètre est un bon rapport. Si tu manques de place,
raccourcis les descriptions, jamais le balayage.

Avant de rendre ton rapport, relis ton mandat point par point et réponds :
**ai-je touché à tout ce qu'on m'a demandé ?** Si non, tu y retournes.

## Format du rapport

En français, dans le fichier que ton brief te désigne.

```
# Rapport — <ton nom>, <ton métier>

## Mon impression générale
## Ce que j'ai réussi à faire
## Ce que je n'ai pas réussi à faire

## Findings
### F1 — <titre court>
- **Nature** : defaut_app | friction_ux
- **Source** : API (route + code) ou interface (fichier:ligne), ou les deux
- **Ce que je croyais obtenir** :
- **Ce que j'ai obtenu** :
- **Reproduction** : les étapes exactes
- **Gravité** : livrable faux > échec franc > friction

## Ma conclusion
Est-ce que je m'en servirais lundi matin ? Oui ou non, et la raison en une phrase.
```

**Quota** : 6 findings maximum, sauf le persona 1 qui n'en a pas.
Un finding = un mécanisme, pas un écran. Au-delà, fusionne.

**Sans source vérifiable, le finding est nul.** Pas de « il me semble que ».

## Hiérarchie de gravité, imposée

1. **Livrable faux** : un document, un e-mail ou une facture qui a l'air
   correct et ne l'est pas. Le pire, parce que ça sort de l'application.
   Exemple réel du 30/08 : un PPTX contenant le code Python du modèle.
2. **Échec franc** : ça ne marche pas et ça le dit.
3. **Message inutile** : ça échoue et le message n'apprend rien (`API error: 400`).
4. **Friction** : ça marche, c'est pénible.

Un échec franc vaut MIEUX qu'un faux résultat. Si tu vois l'inverse, dis-le.
