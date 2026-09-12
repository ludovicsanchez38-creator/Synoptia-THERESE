# DA « Application affinée » : écrans restants de la release 0.73

Date : 12/09/2026. Proposition P-090 acceptée par Ludo : « commence par une
release avec les écrans manquants en respectant la DA déployée récemment, je
te fais confiance ». Ce GO remplace le portail page par page prévu dans le
cadrage du 10/09. Il ne permet pas de modifier les comportements métier.

## Contrat commun

Les écrans restants consomment le socle livré dans les lots 1 à 9. Ils ne
redéclarent ni palette, ni ombre, ni rayon, ni nouvelle famille de composants.

- En-tête simple, surface `bg-surface`, bordure `border-border`, texte
  `text-text` et secondaire `text-text-muted`.
- Titres selon le socle Plus Jakarta Sans. Corps interactif à 14 px minimum ;
  `text-xs` réservé aux métadonnées non interactives.
- `Button`, `Input`, `Select`, `Textarea`, `FormField`, `Carte`, `Ligne`,
  `Etiquette`, `Segments`, `EtatVide`, `Alerte`, `Squelette` et `DialogShell`
  remplacent les équivalents locaux lorsqu'ils couvrent le même contrat.
- Bouton principal cyan uni, secondaire bordé, discret sans remplissage
  permanent. Aucun dégradé, soulèvement ou changement d'échelle au survol.
- Actions de tête regroupées et capables de revenir à la ligne sous 840 px.
  Un panneau couvrant garde sa fermeture, sa cascade Échap et sa restitution
  de focus existantes.
- États chargement, vide, erreur, confirmation et succès restent explicites.
  Aucun texte technique, aucune exception brute, aucune donnée réelle en mode
  démo.
- Aucun appel réseau, schéma, store, destination, raccourci ou règle de
  confirmation ne change dans ce chantier graphique.
- Recette obligatoire en clair, sombre, contraste élevé, 1280, 1024 et 800 px,
  avec grande police ; console, réseau et débordement horizontal contrôlés.

## Lots et frontières de fichiers

### 10A. Email et mise en route

`components/email/**` et `components/onboarding/**` : liste, lecture,
composition, signature, réponse générée, assistant Gmail/IMAP-SMTP et six
étapes de mise en route. Les champs et boutons maison passent aux primitives ;
les assistants gardent leur ordre, leur validation et leur consentement.

### 10B. Documents, fichiers et mémoire

`components/documents/**`, `components/files/**` et les couches encore brutes
de `components/memory/**` : atelier documentaire, trame, sections, pistes,
indexation locale, recherche et modales de projet. Les documents en cours ne
sont jamais présentés comme enregistrés.

### 10C. Actions et agents

`components/atelier/**`, `components/guided/**` et les surfaces Actions encore
brutes : catalogue, mission, session, revue, commande guidée et travaux en
cours. Les actions externes gardent leur confirmation et les états d'agent
restent factuels.

### 10D. Canevas et couches transversales

`components/prototype/*WorkspaceCanvas.tsx` encore bruts, palette, raccourcis,
notifications, Centre de confiance et bibliothèque de prompts. Les canevas
restent des régions latérales non modales sur grand écran et couvrantes aux
largeurs prévues. Les vues déjà harmonisées ne sont pas refaites.

## Critères de sortie

1. Gardes de structure DA ciblées, écrites avant ou avec le lot, puis vertes.
2. Suites ciblées, typecheck/build et lint sans nouvelle dette.
3. Aperçus réels inspectés pour chaque famille et chaque état critique.
4. Suite frontend complète, suite backend complète et parcours Playwright de
   navigation avant le bump.
5. Changelog précis soumis à Ludo avec la version exacte avant tag,
   publication GitHub, mise à jour du site ou annonce Discord.

