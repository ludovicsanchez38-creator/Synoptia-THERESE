# Refonte charte graphique THÉRÈSE - Direction "Atelier"

**Date** : 30 avril 2026
**Auteur** : Ludo + Claude Code (brainstorm /brainstorm)
**Branche** : `feature/theme-atelier`
**Cible release** : v0.12.0-alpha (release groupée, pas d'intermédiaires)

## Contexte et problème résolu

La charte actuelle de THÉRÈSE (`#0B1226` fond sombre + `#2451FF` bleu primaire + `#22D3EE` cyan + `#E11D8D` magenta) signale "startup tech / SaaS" alors que le positionnement Synoptïa est "Humain d'abord, IA en soutien". Ce décalage trahit la posture aux yeux des cibles (dirigeants TPE, formateurs, freelances) et fait fondre THÉRÈSE dans la masse des outils IA actuels (ChatGPT, Claude, Gemini, Copilot - tous sombres + bleu/violet).

## Ressenti recherché

**Apaisant et serein**. L'utilisateur ouvre l'app le matin, ça doit le poser, pas le stimuler. Référence : Things 3, Bear, Reflect, iA Writer. Anti-fatigue oculaire pour usage long.

## Direction retenue : "Atelier"

Crème chaud + sauge + terracotta. Ambiance artisan numérique / cabinet de conseil, anti-startup, anti-IA-froide.

### Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#FAF7F2` | Background global (crème pierre) |
| `--color-surface` | `#FFFFFF` | Cards, modales, panneaux |
| `--color-surface-alt` | `#F2EEE6` | Surfaces secondaires, hover subtil |
| `--color-text` | `#2A2823` | Texte principal (presque noir mais chaud) |
| `--color-text-muted` | `#6B6760` | Texte secondaire, placeholders |
| `--color-primary` | `#5C7C5C` | Boutons d'action, focus, liens (sauge) |
| `--color-primary-hover` | `#4A6649` | Sauge plus foncée au hover |
| `--color-accent` | `#C97B5C` | Highlights, badges, CTAs secondaires (terracotta) |
| `--color-muted` | `#8A8377` | Bordures, séparateurs (gris chaud) |
| `--color-success` | `#5C7C5C` | Identique au primary (cohérence) |
| `--color-error` | `#A8534B` | Erreurs (terracotta foncé, pas rouge vif) |
| `--color-warning` | `#C9A961` | Warnings (or pâle) |

### Typographie

- **UI** : Inter (system fallback)
- **Display / titres éditoriaux** : Source Serif Pro
- Chargement via Fontsource (offline-first, pas de Google Fonts en runtime - cohérent avec la philosophie souveraine)

## Décisions structurantes

| Sujet | Décision | Raison |
|-------|----------|--------|
| Mode | Full clair, **pas de dark mode** | Simplification radicale, anti-fatigue oculaire, différenciation forte vs concurrence |
| Logo | **Repenser complètement** | Le wordmark actuel + accents trémas colorés ne colle plus à l'esprit Atelier |
| Cibles | Toutes à égalité (TPE / formateurs / freelances) | Charte assez chaleureuse pour évacuer le tech froid, assez pro pour ne pas ringardiser les usages B2B |
| Stratégie release | Branche `feature/theme-atelier`, release groupée v0.12.0 | Pas de pollution v0.11.x, retours testeurs concentrés sur un changement majeur |

## Plan d'attaque

### Phase 1 - Logo (1-2 jours, démarre maintenant)

**Outil** : claude.ai/design pour exploration (3-5 directions), puis finalisation locale.

**Pistes à briefer** :
- T calligraphique en Source Serif Italic
- Motif feuillage discret (sauge, branche d'olivier)
- Vague apaisée / coquillage stylisé
- Point organique (peinture, encre)
- Anti-piste : symbole tech (atome, molécule, circuit, robot)

**Livrables** :
- `logo-mark.svg` (symbole seul)
- `logo-wordmark.svg` (THÉRÈSE typographié)
- `logo-lockup.svg` (mark + wordmark combinés)
- `favicon.ico` 16/32/64
- macOS `.icns`
- Windows `.ico`
- Versions monochrome (impression, contexte mono)

### Phase 2 - Foundation (0.5 jour)

- Créer `src/frontend/src/design/tokens.css` (variables CSS centralisées)
- Charger Inter + Source Serif via Fontsource
- Test contraste WCAG AA sur toutes les paires
- Backup de l'ancien thème : tag `theme-legacy-v0.11`

### Phase 3 - Refonte écrans par lots (3-4 jours)

**Ordre** (du plus impactant au moins) :
1. **App shell** (sidebar, topbar, splash, fond global) - omniprésent
2. **Chat** (bulles, input, streaming, code blocks) - cœur de l'app
3. **Panneaux latéraux** (Memory, Files, Calendar, Email)
4. **Modales/Wizards** (Settings, Email setup, Skills)
5. **Formulaires** (login, factures, CRM, calendrier)

Chaque lot : refonte → screenshot avant/après → commit dédié.

### Phase 4 - Validation + release (0.5 jour)

- Test interne sur Mac (déjà installé en v0.11.6)
- Si OK, release v0.12.0-alpha
- Annonce Discord cadrée : "changement majeur d'apparence, retours bienvenus"

**Total estimé : 5-7 jours de travail concentrés.**

## Brief claude.ai/design (Phase 1 - Logo)

> À coller directement dans claude.ai/design. Génère 3-5 directions distinctes.

```
Je dois créer le logo d'une application desktop appelée THÉRÈSE.

CONTEXTE
THÉRÈSE est un assistant IA personnel pour PC/Mac, à destination de dirigeants de TPE, formateurs et freelances. Elle gère emails, CRM, factures, agendas, documents - tout depuis le bureau, en local. C'est un produit open source de Synoptïa, une marque française dont le positionnement est "Humain d'abord, IA en soutien".

ESPRIT À TRADUIRE
- Apaisant et serein (l'utilisateur passe ses journées avec)
- Artisan numérique, cabinet de conseil chaleureux, pas startup tech
- Posée, fiable, française, contemporaine sans être hype
- Anti-IA-froide : surtout pas de symbole tech (atome, circuit, molécule, robot, étoile, "spark")

PALETTE DE LA CHARTE
- Crème pierre #FAF7F2 (fond)
- Sauge profonde #5C7C5C (primaire)
- Terracotta #C97B5C (accent)
- Presque noir chaud #2A2823 (texte)

TYPOGRAPHIE PRÉVUE
- UI : Inter
- Display/wordmark : Source Serif Pro

RÉFÉRENCES VISUELLES INSPIRANTES
- Things 3 (Apple-like, douceur)
- Reflect (calme, premium)
- Craft (artisan)
- iA Writer (sobre, sérieux)
- Notion early days
- Identités d'éditeurs littéraires français contemporains

ANTI-RÉFÉRENCES
- ChatGPT, Claude, Gemini, Copilot (sombre + bleu/violet)
- Linear actuel (trop tech)
- Tout logo "AI assistant" générique

CE QUE JE TE DEMANDE
Génère 3 à 5 directions distinctes pour le logo THÉRÈSE :
1. Wordmark seul (THÉRÈSE typographié, jeu sur l'accent grave et le tréma)
2. Symbole + wordmark (lockup horizontal et carré)
3. Symbole seul (utilisable en favicon 16x16 et en dock icon 1024x1024)

Pistes à explorer (toutes ne sont pas obligatoires) :
- T calligraphique en serif italique
- Motif feuillage discret (branche d'olivier, sauge, organique)
- Vague apaisée, courbe douce
- Point d'encre / tache de peinture organique
- Initiale stylisée jouant sur la diagonale du T
- Combinaison T + accent grave devenant un trait calligraphique

CONTRAINTES TECHNIQUES
- Doit rester lisible en 16x16 (favicon)
- Doit fonctionner en monochrome (impression)
- SVG vectoriel propre
- Pas de gradient (charte sans dégradés)

Présente chaque direction avec :
- Le wordmark
- Le symbole (si présent)
- Le lockup horizontal (symbole + wordmark)
- Une mention rapide de l'idée derrière
- Un mockup en favicon 16x16 et dock 256x256
```

## Synthèse du brainstorm

| Question | Réponse |
|----------|---------|
| Frustration #1 | Trop tech/SaaS - décalage avec positionnement humain |
| Cible prioritaire | Toutes à égalité (TPE / formateurs / freelances) |
| Scope | App THÉRÈSE Desktop + THÉRÈSE Server uniquement |
| Ressenti recherché | Apaisant / serein |
| Mode | Full clair, pas de dark |
| Direction visuelle | A - Atelier (crème + sauge + terracotta) |
| Logo | Repenser complètement |
| Démarrage | Logo d'abord via claude.ai/design |
| Stratégie release | Branche feature, release groupée v0.12.0 |

## Risques identifiés

1. **Rejet testeurs Discord habitués au sombre** - mitigation : annonce cadrée + possibilité de rollback (tag `theme-legacy-v0.11`)
2. **Logo trop "déco" pour audiences B2B** - mitigation : tester wordmark monochrome dans propales DOCX avant validation
3. **Scope qui dérape** - mitigation : Phase 1 (logo) gate strict avant Phase 2 (foundation)
4. **Synoptïa corporate vs Thérèse produit** - cette refonte ne touche QUE Thérèse, la charte Synoptïa marque (`#0B1226`/`#2451FF`/...) reste inchangée pour le site, propales, LinkedIn

## Prochaines actions immédiates

1. Ludo colle le brief ci-dessus dans claude.ai/design
2. Génère 3-5 directions, partage les meilleures avec Claude Code
3. On finalise ensemble la direction retenue (ajustements, exports SVG)
4. Phase 2 : foundation tokens (Claude Code peut démarrer en parallèle pendant l'exploration logo)
