# Protocole : campagne « chaque écran, chaque persona », THÉRÈSE 0.66.1 (cycle 3)

> Demande de Ludo, 05/09/2026 : « ce qui permet le plus de voir les bugs, c'est les
> impressions écran de chaque fonctionnalité et de se mettre à la place des personnes
> utilisatrices pour voir si le parcours client et les flux sont bons ». Cette campagne
> photographie donc chaque étape de chaque parcours, et chaque capture est relue.

## L'application sous test

- Frontend Vite réel : `http://127.0.0.1:1420`, lancé avec `VITE_THERESE_BACKEND_PORT=17393`.
- Backend jetable : `http://127.0.0.1:17393`, `THERESE_DATA_DIR=/tmp/therese-demo-c3`
  (profil de démonstration Marie Exemple, Atelier Exemple : contacts, devis, factures,
  projets, tâches, agenda local, document d'atelier). Jeton dans `/tmp/therese-demo-c3/.session_token`,
  en-tête `X-Therese-Token`. Modèle actif : Ollama local `gemma4-tia:latest` (souverain).
- Aucune donnée réelle de Ludo n'est branchée. Aucune clé cloud.
- Instrument : Playwright (serveur MCP `plugin_playwright_playwright`), document toujours
  visible. Viewport 1280×800 par défaut, DPR 1, thème clair, locale fr-FR ; Nadia travaille
  à 1024×768 et en thème sombre.

## Tu es un persona, pas un auditeur

Tu incarnes UNE personne (fiche jointe), avec son métier, sa patience, ses lignes rouges.
Tu fais TON travail dans l'application, tâche par tâche. Quand ça ne va pas, tu réagis
comme elle : tu insistes deux fois, pas trente minutes, puis tu notes et tu passes à la
suite.

## La règle de la photo

À **chaque étape** de chaque parcours (avant le geste, après le geste, à chaque état
intermédiaire visible : chargement, vide, validation, erreur, succès) :

1. capture plein écran : `browser_take_screenshot` avec `filename` =
   `docs/campagnes/2026-09-05-personas-c3/captures/<persona>/<NN>-<capacite>-<etape>.png`
   (NN sur deux chiffres, croissant) ;
2. `browser_snapshot` (arbre d'accessibilité) au même moment, résumé en deux lignes dans
   la trace : ce qui a le focus, ce qui est annoncé ;
3. console et réseau relevés à la fin de chaque parcours (`browser_console_messages`,
   `browser_network_requests`) : toute erreur ou requête en échec est citée avec son texte.

Une étape sans capture n'a pas eu lieu.

## Ce que tu regardes sur chaque écran (grille de lecture)

- **Prévisibilité** : le titre dit où je suis ; « Retour » et Échap ramènent d'où je viens ;
  cliquer produit l'effet annoncé.
- **États** : chargement visible et court ; vide expliqué avec une action ; erreur lisible
  qui dit quoi faire ; succès confirmé sans jargon ; indisponible distinct de vide.
- **Lisibilité** : rien d'important sous 14 px ; contraste ; alignements ; textes coupés ;
  chevauchements ; scroll qui coince ; thème sombre cohérent.
- **Gestes** : nombre de clics pour finir la tâche ; clavier (Tab, Entrée, Échap) ; focus
  visible.
- **Cohérence** : mêmes mots pour la même chose (lexique : Agenda, Devis et factures,
  Décision, Contacts, Pipeline, Projets, Tâches, Paramètres) ; mêmes boutons au même endroit.

## Interdictions

- Jamais `POST /api/shutdown`, jamais de relance de serveur, jamais `DELETE /api/data/all`,
  jamais de changement de modèle ou de clé, jamais d'envoi réel (e-mail, webhook).
- Aucune écriture hors de ton dossier de captures et de ta trace. Le dépôt se lit, ne se
  modifie pas.
- Aucune donnée personnelle réelle saisie : les données de démonstration suffisent.

## Garde d'environnement, avant le premier geste

Exécute dans la page : `({ visible: document.visibilityState, horloge: document.timeline.currentTime })`.
Si `visible` n'est pas `"visible"` ou si `horloge` vaut 0, arrête-toi, écris une trace vide
« instrument : document caché » et rends la main. Au premier chargement, purge
`localStorage`, `sessionStorage` et IndexedDB, recharge, et vérifie que l'écran correspond
à l'API (`GET /api/chat/conversations` doit rendre ce que le tiroir affiche).

## Ta trace

Fichier : `docs/campagnes/2026-09-05-personas-c3/rapports/<persona>.md`, en français.

```
# <Prénom>, <métier> : trace de la campagne

## Mon impression (première personne, cinq à dix lignes)

## Parcours (un bloc par parcours)
### <capacité> : <objectif>
| Étape | Geste | Attendu | Observé | Capture | Classement |
Classement : bug_candidate (promesse ou règle non tenue, avec preuve), proposal (manque ou
simplification, pour le portail humain), observation (impression, preuve insuffisante).

## Constats numérotés (id persona-NN, sévérité, étapes rejouables, preuve, fichier suspecté si tu l'as lu)

## Transitions couvertes et angles morts

## Tokens consommés (si connus)
```

Ta réponse à l'orchestrateur tient en cinq lignes : chemin de la trace, parcours couverts,
constats avec preuve, constats écartés faute de preuve, tokens.
