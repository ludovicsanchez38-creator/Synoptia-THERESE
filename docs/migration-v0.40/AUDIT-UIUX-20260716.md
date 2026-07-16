# Audit UI/UX croisé THÉRÈSE 0.40 - fable + sol

Date : 16 juillet 2026. Deux audits d'expert UI/UX indépendants (OPT/fable en
pilotage écran, sol en analyse statique du code), grille heuristiques Nielsen +
accessibilité WCAG. Sur la coque après vague 2. À lire avec le rapport personas
(RAPPORT-RECETTE-PERSONAS-20260716.md).

sol a produit 49 findings, fable 4, avec de fortes convergences. Total après
dédup : ~50 findings. Le gros du volume est de l'accessibilité (ARIA, focus,
WCAG) : cohérent et réel, mais c'est un chantier en soi, pas un blocage de bêta.

## Bloquants / importants pour la bêta (à traiter avant de sortir)

| # | Sévérité | Constat | Sources |
|---|---|---|---|
| B1 | MAJEUR produit | Brief « ce qui mérite l'attention » = agenda brut chronologique, pas de curation ni relances/urgences. Règle simple de tri validée par Ludo. | LUDO-10 + FABLE-01 |
| B2 | MAJEUR UX | Dictée vocale sans retour visuel (pas de transcription live, durée, niveau, ni annulation pendant le traitement). | LUDO-11 + FABLE-02 + SOLUX-11 |
| B3 | CRITIQUE fiabilité | Les confirmations (Devis, Board, Atelier, Images) valident à l'ouverture mais les champs restent modifiables : on peut altérer l'instruction/le montant/le fournisseur puis confirmer un état incohérent, avec appels IA coûteux pour Board/Images. | SOLUX-01 |
| B4 | ÉLEVÉ données | Fermer le canevas / Échap / replier annule silencieusement un Board ou une mission Atelier en cours (destructif, non confirmé). | SOLUX-02 |
| B5 | ÉLEVÉ souveraineté | Le consentement au transfert cloud est obligatoire à l'onboarding même en mode 100 % local Ollama : contredit la promesse « données locales ». | SOLUX-16 |
| B6 | MAJEUR (régression vague 2) | Confirmation Agenda : « Annuler » et « Modifier » exécutent la même action (`setConfirming(false)`), le fix vague 2 a ajouté un Annuler cosmétique. La confirmation de note n'a même pas d'Annuler. | SOLUX-37 |

## Chantier accessibilité (vague dédiée, avant diffusion large)

~35 findings cohérents, à traiter en un lot WCAG :
- Focus & modales : pas de focus trap ni de restauration sur onboarding, tiroir, panneaux latéraux, palette de commandes (SOLUX-03, 04, 21, 29).
- Accessibilité cachée / inopérante : réglages d'accessibilité planqués sous « Mode Contributeur », taille de texte sans effet réel (rem non piloté à la racine), « réduire les animations » n'agit pas sur les animations CSS (SOLUX-05, 06, 07, 27).
- Sémantique ARIA : onglets réglages sans pattern tablist, faux radios/switches/tabs sans état annoncé, progressbars sans role, champs sans label (SOLUX-17 à 20, 22, 25, 32, 41, 44, 46, 48).
- Contraste & lisibilité : couleurs codées en dur hors tokens, contraste texte secondaire < 4.5:1, tailles 9-11px, cibles < 44px (SOLUX-34, 35, 23 + FABLE-03).
- États & erreurs silencieuses : faux succès, pertes de saisie, erreurs en console uniquement (SOLUX-08, 09, 12, 13, 14, 15, 26, 38, 40, 44, 49).
- Responsive : grilles fixes, pas de bascule mobile (SOLUX-33, 42, 43).
- Divers cohérence : pastilles macOS décoratives trompeuses, ⌘K affiché hors Mac, avatar sans nom accessible (SOLUX-24, 47).

## Recommandation OPT

Vague 3 = les 6 bloquants B1-B6 ce soir → bêta opt-in honnête. Puis vague
accessibilité dédiée (chantier WCAG complet) avant toute diffusion large. Une
bêta opt-in n'a pas à être WCAG-parfaite, mais B3/B4 touchent la fiabilité et
les données, B5 l'image de souveraineté : ceux-là ne peuvent pas attendre.

Verdict croisé : NON pour l'instant. GO bêta après B1-B6 + un tour de recette Ludo.
