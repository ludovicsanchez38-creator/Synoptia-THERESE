# Refonte charte graphique THÉRÈSE - Direction "Manuscrit"

**Date** : 4 mai 2026 (révision après pivot du 30 avril)
**Auteur** : Ludo + Claude Code (brainstorm /brainstorm)
**Branche** : `feature/theme-atelier` (nom de branche conservé, on bascule juste la direction visuelle)
**Cible release** : v0.12.0-alpha (release groupée, pas d'intermédiaires)

## Historique des décisions

- **30/04** : direction A "Atelier" (crème/sauge/terracotta) explorée puis abandonnée → trop sage, pas assez de panache
- **04/05** : pivot vers direction D "Manuscrit" (ivoire/encre nuit/corail vif) → tempérament grave et lumineux

## Contexte et problème résolu

Charte actuelle THÉRÈSE (`#0B1226` sombre + `#2451FF` bleu + cyan/magenta) signale "startup tech" alors que le positionnement Synoptïa est "Humain d'abord, IA en soutien". Ce décalage trahit la posture aux yeux des cibles (dirigeants TPE, formateurs, freelances) et fait fondre THÉRÈSE dans la masse des outils IA actuels (ChatGPT, Claude, Gemini, Copilot, tous sombres + bleu/violet).

## Direction retenue : "Manuscrit"

Ivoire chaud + encre bleu nuit + corail signature. Ambiance carnet de notes, livre rare moderne, éditeur littéraire contemporain. Personnalité forte par le contraste typographique (Editorial New italique sur Inter), parti-pris assumé. **Tempérament : grave et lumineux.**

### Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg` | `#F4EFE2` | Background global (ivoire chaud, papier vélin) |
| `--color-surface` | `#FBF7EC` | Cards, modales (papier plus clair) |
| `--color-surface-alt` | `#EAE3D2` | Surfaces secondaires, hover, séparation |
| `--color-text` | `#1A2B4A` | Texte principal (encre bleu nuit) |
| `--color-text-muted` | `#6B7180` | Texte secondaire, placeholders (gris ardoise) |
| `--color-primary` | `#1A2B4A` | Boutons d'action (le texte sert d'action, geste éditeur) |
| `--color-primary-hover` | `#0F1B33` | Encre plus profonde au hover |
| `--color-signature` | `#E4644E` | **Corail vif réservé** (badge, alerte, accent fort, moments rares) |
| `--color-signature-soft` | `#F4A88E` | Version douce du corail (background highlight, lien hover) |
| `--color-muted` | `#C9C2B0` | Bordures, séparateurs (papier vieilli) |
| `--color-success` | `#3D5A3D` | Vert encre profond (cohérent avec l'esprit ink) |
| `--color-error` | `#A8534B` | Rouge oxyde (terre brûlée, pas rouge néon) |

### Typographie

- **Display / titres / wordmark** : Editorial New (italique fort sur titres principaux, regular sur sous-titres). Alternative open source à valider : Reckless Neue, Cormorant Garamond Bold Italic, Tiempos Headline.
- **UI courant** : Inter (lisibilité optimale)
- **Mono** : JetBrains Mono ou IBM Plex Mono (code blocks)
- Chargement via Fontsource (offline-first, cohérent avec philosophie souveraine)

## Décisions structurantes

| Sujet | Décision | Raison |
|-------|----------|--------|
| Mode | Full clair, **pas de dark mode** | Simplification radicale, anti-fatigue, différenciation forte |
| Logo | **Repenser complètement** | Le wordmark actuel + accents trémas colorés ne colle plus à l'esprit Manuscrit |
| Cibles | Toutes à égalité (TPE, formateurs, freelances) | Charte assez chaleureuse pour évacuer le tech froid, assez forte pour marquer |
| Stratégie release | Branche `feature/theme-atelier`, release groupée v0.12.0 | Pas de pollution v0.11.x, retours testeurs concentrés sur changement majeur |

## Plan d'attaque

> Estimations en heures de travail Claude Opus, pas en jours-homme.

### Phase 1 - Logo (~2h itératif, démarre maintenant)

**Outil** : claude.ai/design pour exploration (3-5 directions), finalisation locale.

**Pistes à briefer** :
- T calligraphique en Editorial New italic, jeu sur la diagonale et le pied
- Accent grave devenant un trait calligraphique étiré au-dessus du E
- Point de tréma stylisé en corail (rappel signature)
- Motif de signature manuscrite (style paraphe d'auteur, encre)
- Combinaison T + accent en monogramme cursif
- Lettrine éditoriale (T initiale ornée, livre ancien revisité)
- Anti-piste : symbole tech (atome, molécule, circuit, robot, étoile, spark)

**Livrables** :
- `logo-mark.svg` (symbole seul)
- `logo-wordmark.svg` (THÉRÈSE typographié)
- `logo-lockup.svg` (mark + wordmark)
- `favicon.ico` 16/32/64
- macOS `.icns`
- Windows `.ico`
- Versions monochrome

### Phase 2 - Foundation (~1h)

- Créer `src/frontend/src/design/tokens.css` (variables CSS centralisées)
- Charger Inter + alternative Editorial New via Fontsource
- Test contraste WCAG AA sur toutes les paires
- Backup ancien thème : tag `theme-legacy-v0.11`

### Phase 3 - Refonte écrans par lots (~6-10h Claude)

**Ordre** (du plus impactant au moins) :
1. App shell (sidebar, topbar, splash, fond global)
2. Chat (bulles, input, streaming, code blocks)
3. Panneaux latéraux (Memory, Files, Calendar, Email)
4. Modales/Wizards (Settings, Email setup, Skills)
5. Formulaires (login, factures, CRM, calendrier)

Chaque lot : refonte → screenshot avant/après → commit dédié.

### Phase 4 - Validation + release (~1h)

- Test interne sur Mac (déjà installé en v0.11.6)
- Si OK, release v0.12.0-alpha
- Annonce Discord cadrée : "changement majeur d'apparence, retours bienvenus"

## Brief claude.ai/design (Phase 1 - Logo)

> À coller directement dans claude.ai/design. Génère 3-5 directions distinctes.

```
Je dois créer le logo d'une application desktop appelée THÉRÈSE.

CONTEXTE
THÉRÈSE est un assistant IA personnel pour PC/Mac, à destination de dirigeants de TPE, formateurs et freelances. Elle gère emails, CRM, factures, agendas, documents, tout depuis le bureau, en local. Produit open source de Synoptïa, marque française dont le positionnement est "Humain d'abord, IA en soutien".

ESPRIT À TRADUIRE
- Grave et lumineux (parti pris assumé, pas de tiédeur)
- Carnet de notes, livre rare moderne, éditeur littéraire contemporain
- Posée, fiable, française, avec du tempérament
- Anti-IA-froide : surtout pas de symbole tech (atome, circuit, molécule, robot, étoile, spark)
- Doit donner envie de l'ouvrir le matin pour passer du temps avec

PALETTE DE LA CHARTE
- Ivoire chaud #F4EFE2 (fond, papier vélin)
- Encre bleu nuit #1A2B4A (texte, actions)
- Corail vif #E4644E (signature, accent rare et fort)
- Gris ardoise #6B7180 (texte secondaire)

TYPOGRAPHIE PRÉVUE
- Display/wordmark : Editorial New (italique fort) ou alternative similaire (Reckless Neue, Tiempos Headline, Cormorant Garamond Bold Italic)
- UI courant : Inter

RÉFÉRENCES VISUELLES INSPIRANTES
- Pentagram pour éditeurs littéraires
- Phaidon, Acne Paper (édition design)
- The New York Review of Books (typographie éditoriale)
- Anciennes éditions Gallimard repensées
- iA Writer (sobriété éditoriale forte)
- Substack premium (carnet moderne)

ANTI-RÉFÉRENCES
- ChatGPT, Claude, Gemini, Copilot (sombre + bleu/violet tech)
- Linear, Vercel, Stripe (SaaS standard)
- Tout logo "AI assistant" générique

CE QUE JE TE DEMANDE
Génère 3 à 5 directions distinctes pour le logo THÉRÈSE :
1. Wordmark seul (THÉRÈSE typographié, en valorisant l'accent grave et le tréma)
2. Symbole + wordmark (lockup horizontal et carré)
3. Symbole seul (utilisable en favicon 16x16 et en dock icon 1024x1024)

Pistes à explorer (toutes ne sont pas obligatoires, choisis les plus fortes) :
- T calligraphique en serif italique, jeu sur la diagonale et le pied
- Accent grave devenant un trait calligraphique étiré au-dessus du E (signature visuelle forte)
- Point de tréma stylisé en corail (rappel de la couleur signature)
- Motif de signature manuscrite (paraphe d'auteur, encre)
- Monogramme T + accent en cursif
- Lettrine éditoriale (T initiale ornée, style livre ancien revisité)

CONTRAINTES TECHNIQUES
- Doit rester lisible en 16x16 (favicon)
- Doit fonctionner en monochrome (impression, contexte mono)
- SVG vectoriel propre
- Pas de gradient (charte sans dégradés)
- Le corail s'utilise SEUL (jamais sur le wordmark complet, juste comme accent ponctuel : un point de tréma, un trait, une virgule)

Présente chaque direction avec :
- Le wordmark
- Le symbole (si présent)
- Le lockup horizontal (symbole + wordmark)
- Une mention courte de l'idée derrière
- Un mockup en favicon 16x16 et dock 256x256
- Une mention monochrome
```

## Synthèse du brainstorm (final)

| Question | Réponse |
|----------|---------|
| Frustration #1 | Trop tech/SaaS, décalage avec positionnement humain |
| Cible prioritaire | Toutes à égalité (TPE, formateurs, freelances) |
| Scope | App THÉRÈSE Desktop + THÉRÈSE Server uniquement |
| Ressenti recherché | Apaisant et serein |
| Mode | Full clair, pas de dark |
| Sage vs caractère | Caractère fort assumé |
| Direction visuelle finale | **D - Manuscrit** (ivoire + encre nuit + corail) |
| Tempérament | Grave et lumineux |
| Logo | Repenser complètement |
| Démarrage | Logo d'abord via claude.ai/design |
| Stratégie release | Branche feature, release groupée v0.12.0 |

## Risques identifiés

1. **Editorial New est payante (Pangram Pangram)** : licence à vérifier ou bascule sur alternative libre (Reckless Neue, Cormorant Garamond Bold Italic, Tiempos Headline). Mitigation : explorer alternatives gratuites avant validation finale.
2. **Rejet testeurs Discord habitués au sombre** : annonce cadrée + tag rollback `theme-legacy-v0.11`
3. **Corail jugé trop pop ou trop daté** : tester sur 2-3 testeurs alpha avant intégration globale
4. **Synoptïa corporate vs Thérèse produit** : cette refonte ne touche QUE Thérèse, la charte Synoptïa marque (`#0B1226`/`#2451FF`/...) reste inchangée pour le site, propales, LinkedIn

## Prochaines actions immédiates

1. Ludo colle le brief ci-dessus dans claude.ai/design
2. Génère 3-5 directions, partage les meilleures
3. Finalisation ensemble de la direction retenue (ajustements, exports SVG)
4. Phase 2 : foundation tokens (Claude Code peut démarrer en parallèle pendant l'exploration logo)
