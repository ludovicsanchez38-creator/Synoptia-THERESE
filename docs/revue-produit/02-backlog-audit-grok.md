# Backlog issu de l'audit Grok du 25/08/2026

> Source : [docs/audits/AUDIT-GROK-20260825.md](../audits/AUDIT-GROK-20260825.md).
> Arbitrage Ludo (25/08) : **0.48 = Board frontier + P1 (établi/tiroir) + P3
> (lexique)**. Tout le reste vit ici, à prioriser jalon par jalon.

## Retenu pour 0.48 (design dédié)
- Modèles frontier du Board + raisonnement maximal (chantier préparé le 25/08,
  vérifications sources faites).
- P1 - un établi, un tiroir (périmètre exact précisé au design).
- P3 - lexique « un mot par chose ».

## Backlog priorisé (l'ordre de Grok, nos nuances en note)

| Reco | Contenu | Note interne |
|---|---|---|
| P0 (reste) | Boucler les 5 jobs du quotidien : envoi devis (501), brief curaté, IMAP 2 min, contact unique | Le gel des nouvelles fonctions n'interdit pas les finitions de qualité |
| P2 | Onboarding 90 secondes (3 étapes, sécurité dite avant la 1re requête, le reste en contexte) | |
| P4 | Le canevas EST la vue (mort du double panel classic), renommer ConversationCanvasPrototype → AppShell | |
| P5 | Mémoire visible (« Ce que THÉRÈSE sait », badge de source par message, contact unique Mémoire=CRM) | Contact unique déjà identifié P4 revue de juin |
| P6 | Réponses en 3 couches (verdict / pourquoi / sources pliées) | |
| P7 | Contrats d'agent avant Board/Atelier/deep-research (durée, coût, limites) + briefing au retour | |
| P8 | Lot WCAG (cibles 44 px, contraste AA) + tests Windows DANS la gate + notarisation/signature | Backlog Windows 11 tests déjà documenté 0.43.4 |
| P9 | Doc utilisateur et changelog public alignés sur la version courante | Le moins cher, le plus visible - candidat au fil de l'eau |
| P10 | Mesure : 5 tâches × 5 personnes TPE sans Ludo dans la pièce (workbench test chiffré) | Juge de paix avant toute bêta élargie |

Nuances actées : Board et project.sync ne sont pas du « feature theater »
(project.sync demandé et utilisé par un testeur réel) - ils vont au tiroir,
ils ne sont pas dévalorisés.
