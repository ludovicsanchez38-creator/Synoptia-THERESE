# Skill: Présentation PowerPoint (pptx-pro)

## Description

Génère des présentations PowerPoint (.pptx) avec le thème dark premium Synoptïa.

## Format de sortie

Le LLM doit générer du contenu en **Markdown structuré** avec des séparateurs de slides.

### Structure attendue

```markdown
# Titre de la Présentation
Sous-titre ou tagline

---

## Slide 2 - Contexte
- Point clé 1
- Point clé 2
- Point clé 3

---

## Slide 3 - Problématique
Texte explicatif de la problématique.

- Élément A
- Élément B

---

## Slide 4 - Solution
Description de la solution proposée.

---

## Merci !
Contact : ludo@synoptia.fr
```

## Règles de formatage

1. **Première slide** : `# Titre` suivi d'une ligne de sous-titre
2. **Séparateurs** : Utiliser `---` pour séparer les slides
3. **Titres de slide** : `## Titre de la slide`
4. **Bullet points** : `-` ou `*` pour les listes
5. **Dernière slide** : Message de fin (remerciements, contact)
6. **Maximum** : 6-8 slides recommandé, 4-5 points par slide

## Charte Synoptïa (Dark Theme)

- **Fond** : #0B1226 (bleu nuit)
- **Texte principal** : #E6EDF7 (blanc cassé)
- **Titres** : #22D3EE (cyan accent)
- **Accents** : #E11D8D (magenta), #2451FF (bleu)
- **Police** : Outfit (titres), Inter (corps)

## Exemples d'usage

- Pitch deck client
- Présentation de projet
- Formation / Workshop
- Bilan trimestriel
- Réunion d'équipe
