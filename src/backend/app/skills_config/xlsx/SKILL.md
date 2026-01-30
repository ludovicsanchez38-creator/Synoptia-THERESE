# Skill: Tableur Excel (xlsx-pro)

## Description

Génère des tableurs Excel (.xlsx) professionnels avec mise en forme Synoptïa.

## Format de sortie

Le LLM doit générer du contenu en **JSON structuré** ou **Markdown table**.

### Option 1 : JSON (recommandé)

```json
{
  "title": "Titre du tableau",
  "headers": ["Colonne 1", "Colonne 2", "Colonne 3"],
  "rows": [
    ["Valeur 1A", "Valeur 1B", "Valeur 1C"],
    ["Valeur 2A", "Valeur 2B", "Valeur 2C"]
  ]
}
```

### Option 2 : Markdown Table

```markdown
| Colonne 1 | Colonne 2 | Colonne 3 |
|-----------|-----------|-----------|
| Valeur 1A | Valeur 1B | Valeur 1C |
| Valeur 2A | Valeur 2B | Valeur 2C |
```

## Règles de formatage

1. **En-têtes** : Toujours en première ligne, formatés en gras
2. **Données** : Lignes alternées (blanc/gris clair) pour lisibilité
3. **Nombres** : Utiliser le format numérique approprié
4. **Dates** : Format français (JJ/MM/AAAA)
5. **Formules** : Préférer les valeurs calculées côté LLM

## Charte Synoptïa

- **En-têtes** : Fond #2451FF, texte #FFFFFF, police Outfit Bold
- **Lignes paires** : Fond #F8FAFC
- **Lignes impaires** : Fond #FFFFFF
- **Bordures** : #E2E8F0 (gris clair)
- **Police corps** : Inter 11pt

## Exemples d'usage

- Budget prévisionnel
- Suivi de facturation
- Planning projet
- Liste de contacts
- Tableau de bord KPI
- Inventaire produits
