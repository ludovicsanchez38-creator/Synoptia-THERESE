# O2 - « Écrire » ouvre une rédaction, le panneau s'appelle toujours « Consulter mes emails »

**Trouvé en vérifiant le finding F6 du persona 01** (le médecin cherchait un
courrier type et est tombé sur une rédaction d'e-mail).

- **Gravité** : mineur (requalifié — j'avais dit majeur sur une prémisse fausse)
- **Nature** : defaut_app (dérive de nommage)
- **Source** : `ConversationCanvasPrototype.tsx:120` et `:130`, contre
  `lib/etabli.ts:26`
- **Introduit par** : la v0.53.0, entrée 10 du plan UX (commit `31fdcc91`)

## Ce qui se passe

L'entrée 10 a changé le COMPORTEMENT de « Écrire » : le verbe ouvre désormais
une rédaction au lieu d'une liste de messages. Deux libellés n'ont pas suivi :

```ts
// lib/etabli.ts:26        — le bouton que l'utilisateur clique
{ id: 'email', label: 'Écrire' }

// ConversationCanvasPrototype.tsx:120 — le NOM du panneau qui s'ouvre
email: 'Consulter mes emails',

// ConversationCanvasPrototype.tsx:130 — la question envoyée si l'utilisateur valide
email: 'Montre-moi les messages à traiter et aide-moi à préparer une réponse.',
```

`scenarioLabels[scenario]` n'est pas décoratif : c'est le titre accessible du
canevas (`ConversationCanvasPrototype.tsx:317-319`, `id="prototype-context-canvas-title"`,
en `sr-only`). Un utilisateur au lecteur d'écran clique **Écrire** et s'entend
annoncer **« Consulter mes emails »**.

**Correction après contre-expertise Soso** : j'avais écrit que `scenarioPrompts`
« est envoyé au modèle ». **C'est faux.** Sa seule utilisation est un sous-titre
affiché dans la palette (`ConversationCanvasPrototype.tsx:559`,
`<span className="block text-xs text-text-muted">`). Rien ne part.

Le défaut se réduit donc à ce qui est **lu** : le titre accessible du canevas
(annoncé aux lecteurs d'écran) et un sous-titre de palette qui décrivent une
lecture d'e-mails là où le bouton ouvre une rédaction.

## Pourquoi ça compte

C'est précisément la dérive que le chantier P4 (« Les noms », 27/08) avait
entrepris de corriger, et que la 0.53 a réintroduite sur la surface qu'elle
venait de changer. Le gate `lexiqueTitres.test.ts` ne couvre pas
`scenarioLabels` : il n'a rien vu.

Le persona 01 l'a rencontré sans savoir le nommer : « Sur l'accueil, *Écrire*
ouvre une rédaction de mail (scénario `email` : "Consulter mes emails"). […]
Si *Écrire* veut dire e-mail, qu'on l'écrive. »

## Correctif attendu

Trois décisions à prendre ensemble, pas une :

1. `scenarioLabels.email` doit nommer ce que le panneau fait maintenant
   (« Écrire un message », pas « Consulter mes emails »).
2. `scenarioPrompts.email` doit correspondre à une rédaction.
3. Étendre le gate de lexique à `scenarioLabels` / `scenarioPrompts`, sinon la
   prochaine entrée qui change un comportement laissera le même écart.
