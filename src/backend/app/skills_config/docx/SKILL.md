# Skill: Document Word Professionnel (docx-pro)

## Description

Génère des documents Word (.docx) professionnels avec la charte graphique Synoptïa.

## Format de sortie

Le LLM doit générer du contenu en **Markdown structuré** qui sera converti en Word.

### Structure attendue

```markdown
# Titre Principal du Document

## Section 1
Contenu de la section avec du texte **en gras** et *en italique*.

- Point 1
- Point 2
- Point 3

## Section 2
Autre contenu...

### Sous-section
Texte détaillé...
```

## Règles de formatage

1. **Titres** : Utiliser `#` pour le titre principal, `##` pour les sections, `###` pour les sous-sections
2. **Listes** : Utiliser `-` ou `*` pour les listes à puces
3. **Emphase** : `**gras**` et `*italique*` supportés
4. **Pas de tableaux complexes** : Préférer les listes

## Charte Synoptïa

- **Police** : Outfit (titres), Inter (corps)
- **Couleurs** :
  - Fond : #FFFFFF
  - Texte : #0B1226
  - Accent primaire : #2451FF
  - Accent cyan : #22D3EE
  - Accent magenta : #E11D8D

## Exemples d'usage

- Propositions commerciales
- Rapports d'audit
- Comptes-rendus de réunion
- Documentation technique
- Contrats et devis
