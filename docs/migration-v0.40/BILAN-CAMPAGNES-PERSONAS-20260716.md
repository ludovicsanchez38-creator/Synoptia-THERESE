# Bilan des campagnes personas THÉRÈSE 0.40 - double regard

Date : 16 juillet 2026. Deux campagnes de recette indépendantes sur la nouvelle
interface (coque conversationnelle) devenue le mode par défaut, chacune sur des
espaces `THERESE_DATA_DIR` vierges, sans qu'aucune ne consulte les résultats de
l'autre. Objectif : ne laisser passer aucun bug avant la sortie.

## Les deux regards

**Campagne OPT (10 personas touche-à-tout).** Dix profils métier lâchés sur des
espaces vierges puis sur la vraie base, avec un crawler qui clique chaque bouton
et un détecteur de boutons morts. Rapport : `CAMPAGNE-10-PERSONAS-20260716.md`.
Verdict : 0 vrai bug résiduel après correction des deux plantages agenda (500
calendriers Google avec `#` dans l'ID, 400 `account_id` à froid). Tous les
findings d'ergonomie relevés par Ludo à l'œil traités (bouton calendrier, Vue
complète, avatar/roue, aide, languette, trois traits, double +).

**Campagne Codex/sol (5 personas un par un, en computer use).** Cinq profils
joués séquentiellement par sol via Playwright, onboarding complet + 30/30
capacités ouvertes + focus métier + dictée + thèmes + fenêtre 800×600 + aller-
retour interface classique. Rapport source : `personas/findings-personas-codex.md`.
Verdict : 9 findings, dont 1 critique de confidentialité que le crawler OPT
n'avait pas vu.

## Ce que le croisement a prouvé

Les deux campagnes se complètent au lieu de se doubler. Le crawler OPT trouve
les plantages (500, 400, boutons morts) et confirme la couverture ; il ne voit
pas une fuite de données entre espaces parce qu'un espace « vierge » qui affiche
50 images n'est pas un plantage, c'est un contenu. Le regard Codex, lui, compare
ce qu'il devrait voir (rien) à ce qu'il voit (50 images d'un autre espace) et
lève le drapeau. À l'inverse, l'œil de Ludo en test réel a trouvé des boutons
inutiles qu'aucun robot n'a signalés. Trois angles, trois familles de défauts.

## Les 9 findings Codex et leur traitement

| # | Sévérité | Constat | État | Commit |
|---|----------|---------|------|--------|
| CODEX-01 | Critique | Studio Images ignorait `THERESE_DATA_DIR` : un espace vierge affichait les 50 images d'un autre espace | Corrigé | 952d4d9 |
| CODEX-02 | Majeure | Connecteurs MCP lisaient `~/.therese/mcp_servers.json` au lieu du répertoire isolé | Corrigé | 952d4d9 |
| CODEX-03 | Majeure | Suggestion fantôme appelait `/api/chat/complete` (endpoint absent) : 404 à chaque frappe | Corrigé (feature neutralisée) | 7a05678 |
| CODEX-04 | Majeure | Fichiers et connaissances plantait hors application Tauri (`invoke` undefined) | Corrigé (garde isTauri + message clair) | 7a05678 |
| CODEX-05 | Majeure | Récapitulatif onboarding affichait une fausse coche verte `openai / gpt-5.5` après « Configurer plus tard » | Corrigé (basé sur `available` réel) | 7a05678 |
| CODEX-06 | Modérée | Pied de page onboarding coupé à 1280×900 (Retour, Commencer sous le pli) | Corrigé (footer épinglé) | 7a05678 |
| CODEX-07 | Modérée | Dictée sans clé Groq renvoyait le JSON brut d'erreur à l'utilisateur | Corrigé (message lisible extrait) | 7a05678 |
| CODEX-08 | Faible | « Taches » sans accent dans le titre, le compteur, les états vides | Corrigé | 7a05678 |
| CODEX-09 | Modérée | Confirmation Studio Images (action payante) sous le pli à 1280×900 | Corrigé (amenée à l'écran) | 4538a90 |

Bilan : 1 critique, 4 majeures, 3 modérées, 1 faible. Les neuf sont corrigées.

## Note sur les findings non-bloquants restants

Les artefacts liés au contexte de test (micro absent en headless, dictée qui
échoue faute de clé Groq configurée sur l'espace de test) ne sont pas des
régressions produit : ce sont des prérequis d'environnement. CODEX-07 a quand
même été traité pour que le message soit propre le jour où la clé manque en vrai.

## État des tests après corrections

- Frontend : 642 tests vitest verts, `tsc --noEmit` propre, ESLint 1 warning
  (baseline, pré-existant).
- Backend : suite pytest verte (sortie 0, hors e2e).
- mypy : vérifié sous le seuil de référence (997).

## Lecture release

Les deux campagnes convergent : après ces neuf corrections, plus aucun bug
résiduel connu, y compris le point de confidentialité qui était le seul vrai
bloquant. La nouvelle interface est le mode par défaut, avec un pop-up qui
explique comment revenir à l'ancienne. Reste la recette finale de Ludo à l'écran
avant de lancer la sortie.
