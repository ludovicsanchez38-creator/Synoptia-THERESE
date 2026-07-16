# Audit UI/UX expert - passe fable (Claude)

Grille : heuristiques de Nielsen + accessibilité WCAG. Coque 0.40 après vague 2.

| ID | Sévérité | Heuristique | Écran | Constat | Recommandation |
|---|---|---|---|---|---|
| FABLE-01 | MAJEUR | Correspondance monde réel / honnêteté | Brief « Ton attention aujourd'hui » | Promet de regrouper ce qui mérite l'attention mais liste l'agenda chronologique brut, tous items tagués « Agenda », aucune relance/urgence/notification (pourtant annoncées dans la description de la capacité), aucune hiérarchie urgent/important. | Curation par règle simple (validée Ludo) : RDV avec participants/contacts CRM + relances/échéances proches en tête, perso solo relégué ou masqué. Remonter aussi les autres sources (relances, tâches). |
| FABLE-02 | MAJEUR | Visibilité de l'état système | Composeur, dictée vocale | Aucun retour visuel du texte pendant qu'on dicte : l'utilisateur parle sans savoir si l'app l'entend ni ce qu'elle transcrit. | Transcription en direct dans le champ + indicateur d'écoute animé. Vérifier si présent en classique et manquant dans la coque. |
| FABLE-03 | MINEUR | Accessibilité (contraste WCAG AA) | Global, texte secondaire | Texte muté rgb(91,106,130) sur fond rgb(243,246,252) ≈ 4.0:1, sous le seuil AA de 4.5:1 pour le texte normal. | Assombrir légèrement le token de texte secondaire en clair pour atteindre 4.5:1. |
| FABLE-04 | MINEUR | Reconnaissance / feedback | Sidebar « + » nouvelle conversation | Le « + » ne donne pas de signal clair qu'un nouvel espace vierge s'est ouvert (l'écran reste très proche de l'accueil). Affordance de résultat faible. | Transition ou état vide explicite de conversation neuve. À confirmer (peut être le comportement attendu). |

## Convergences attendues avec la recette Ludo
- FABLE-01 = LUDO-10 (brief non curé)
- FABLE-02 = LUDO-11 (dictée sans retour visuel)

## Points positifs (à conserver)
- Affordances claires : chevron « > » sur chaque ligne cliquable, poignée de réouverture du panneau (vague 2).
- Transparence : bandeau « Sources réelles · Agenda », « Parcours réel · confirmation avant effet ».
- Thème sombre cohérent (vague 1), confirmations Email/Agenda/Images (vagues précédentes).
- Bouton « Synoptïa » désormais passif (fin du triple doublon).
