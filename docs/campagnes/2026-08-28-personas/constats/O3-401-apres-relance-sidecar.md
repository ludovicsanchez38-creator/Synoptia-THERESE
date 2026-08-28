# O3 - Après une relance du moteur, l'application est morte sans le dire

**Vécu par le persona 03 (l'écrivaine)** : « le deuxième message a cassé le
flux, puis le jeton n'a plus passé ». Elle a terminé sa session en 401 sur tout.

- **Gravité** : bloquant
- **Nature** : defaut_app
- **Source** : `services/api/core.ts:93-110` et `:143-144`, `App.tsx:97-120`,
  `components/ui/SidecarStatusBanner.tsx:19-34`, `src-tauri/src/lib.rs:375-395`,
  `backend/app/main.py` (génération du token au démarrage)

## L'enchaînement

1. Le sidecar backend meurt (crash, veille/réveil, mise à jour, OOM).
2. Tauri le relance — c'est prévu et documenté : `lib.rs:375`, « jusqu'à
   3 tentatives », avec un événement `sidecar-status` émis à chaque étape.
3. Au démarrage, le backend **génère un nouveau token de session**
   (`main.py`, « Session token generated and saved to …/.session_token »).
4. Le frontend, lui, a chargé le token **une seule fois** :

```ts
let _sessionToken: string | null = null;              // core.ts:93
export async function initializeAuth() { … }          // core.ts:95, appelé une fois
headers.set('X-Therese-Token', _sessionToken);        // core.ts:144
```

`initializeAuth()` n'est appelé que dans un `useEffect` gardé par
`backendReady` (`App.tsx:97-106`), au démarrage. **Aucune ligne du frontend ne
traite un 401** : pas de `status === 401`, pas de `_sessionToken = null`, pas de
re-fetch.

5. `SidecarStatusBanner` **écoute** bien `sidecar-status` et affiche le bandeau,
   mais il ne recharge pas le token. Il annonce donc que le moteur est reparti…
   pendant que tout retourne 401.

## Pourquoi c'est grave

Le produit a soigné la relance côté Rust — trois tentatives, statut émis,
bandeau, bouton *Relancer*. Tout ce travail est neutralisé par une ligne
manquante côté TypeScript : après une relance réussie, l'application est
inutilisable et **rien ne le dit**. L'utilisateur voit une application qui se
déclare en marche et qui refuse chaque geste.

Le persona 03 l'a interprété comme « elle ne veut plus de moi ». Elle n'a pas
pensé à relancer l'application : elle a arrêté d'essayer.

## Correctif attendu

Deux gestes, indépendants :

1. `core.ts` : sur un 401, vider `_sessionToken`, rappeler `initializeAuth()`,
   rejouer la requête **une fois**. Sans boucle : un second 401 doit remonter.
2. Écouter `sidecar-status: running` et recharger le token à ce moment — le
   frontend sait déjà que le moteur vient de repartir, il ne s'en sert pas.

Le test qui manque : « le token change côté serveur → la requête suivante
réussit quand même ».

## Mise au point d'honnêteté

Le crash qui a déclenché ce scénario pendant la campagne vient très
probablement de **mon harnais**, pas du produit : Ollama occupait 36 % des 16 Go
de la machine, la mémoire libre était à 18 %, aucune trace d'erreur ni d'appel
`/api/shutdown` dans le journal (la route logge « Shutdown demandé »).
Le processus a été tué silencieusement.

Le crash est donc à mettre au compte de la campagne. **Le 401 qui suit, non** :
il se produira à chaque relance du sidecar, quelle qu'en soit la cause, et le
produit prévoit lui-même ces relances.
