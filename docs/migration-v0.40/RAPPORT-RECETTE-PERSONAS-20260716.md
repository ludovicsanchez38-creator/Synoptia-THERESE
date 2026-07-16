# Rapport de recette THÉRÈSE 0.40 - campagne personas double regard

Date : 16 juillet 2026. Demandé par Ludo : 5 personas solopreneurs, deux passes
indépendantes (OPT en pilotage à l'écran + sol en analyse code/captures), rapport
consolidé et plan d'action.

Personas : coach (Estelle), artisan BTP (Karim), formatrice (Claire), dev
freelance (Tom), graphiste (Léa). Espaces de données vierges dédiés. Aucun effet
externe confirmé.

## Synthèse

- **0 bloquant absolu**, mais **1 parcours métier bloqué** (premier devis artisan).
- **9 findings majeurs**, **5 mineurs**.
- **2 convergences fortes** (trouvées par les deux passes indépendamment).
- La coque est solide sur le fond (30 capacités, états vides soignés, confirmations
  Email/Images, retour classique fiable) ; les défauts sont ciblés et réparables.
- **Non prêt pour bêta en l'état** ; prêt après la vague 1 du plan.

## Convergences (les deux passes, priorité haute)

| # | Sévérité | Constat | Sources |
|---|---|---|---|
| C1 | MAJEUR | Bouton « Synoptïa » (mallette + chevron) ouvre `Paramètres > Profil`, comme l'avatar et la roue dentée : 3 contrôles → même écran, et le changement d'espace annoncé par le chevron n'existe pas. | OPT (LUDO-6) + SOL-02 |
| C2 | MAJEUR | Identité et brief changent silencieusement entre sessions (Estelle/0 élément puis Ludo/6 éléments) : état initial pas stable sans action profil. | OPT-02/03 + SOL-05 |

## Findings majeurs

| ID | Écran | Constat | Preuve |
|---|---|---|---|
| M1 (SOL-01) | Coque, thème sombre | La bascule bureau clair→sombre n'a **aucun effet** sur la coque : fond et texte identiques, aucune classe de thème appliquée. Confirmé aussi dans les captures OPT du matin (thème sombre = clair). Bloquant pour la graphiste. | captures/31-sombre-centre.png (= clair) ; sol SOL-20/21 |
| M2 (SOL-04) | Canevas Devis, artisan | « Nouveau devis » → « Aucun contact disponible » sans moyen d'ajouter un contact dans la coque. Parcours premier devis bloqué, seul recours : quitter vers la facturation complète. | sol SOL-10 |
| M3 (SOL-03) | Canevas Agenda | La confirmation de création d'événement n'a pas de bouton « Annuler » (seulement Modifier / Confirmer), incohérent avec Email et Images. | sol SOL-16 |
| M4 (OPT-01) | Onboarding LLM | Spinner infini sans message ni échappatoire quand le backend est occupé (téléchargement du modèle d'embeddings ; HF 504 pendant le test). Nouvel utilisateur au réseau lent coincé. | captures-p1/04 |
| M5 (OPT-02) | Onboarding / état | Le wizard se rejoue depuis l'étape 1 dans tout contexte neuf tant que le POST de fin n'a pas abouti, même profil backend rempli. | a2-fin-wizard |
| M6 (OPT-03) | Chat espace vierge | Modèle par défaut `gemma4-tia:latest` (Ollama local) ; sans Ollama ni clé cloud, THÉRÈSE ne peut pas répondre et ne l'explique pas au 1er message. | captures-coque/10 |
| M7 (LUDO-5) | Cloche notifications | Ouvre l'accueil de l'ancienne interface en vue intégrée (impression de retour en arrière). | recette Ludo |

## Findings mineurs

| ID | Constat |
|---|---|
| m1 (SOL-06) | À propos affiche `0.32.1` en pleine coque 0.40 ; libellé de l'interrupteur n'indique pas la version d'interface active. |
| m2 (SOL-07) | Confirmation Images : « Qualité : Standard » devient « qualité medium » (valeur technique au lieu du libellé). |
| m3 (SOL-08) | Fenêtre 900×650 : « Contrôle des données » passe sur deux lignes avant tout mode mobile. |
| m4 (SOL-09) | Calculateur ROI : « 75 % » dans la valeur, « 75.0% » dans le commentaire (notation FR + décimales incohérentes). |
| m5 (OPT-04) | Onboarding étape 2 : « Enregistrement en cours… » long sans retour clair, risque de double clic. |

## Déjà corrigé aujourd'hui (recette Ludo du matin)

| ID | Constat | Commit |
|---|---|---|
| LUDO-1 | Carte facturation à tort (profil chiffré, cache vide) | a404267 |
| LUDO-2 | Pouce du switch bêta décentré | 79e738b |
| LUDO-3 | Dictée vocale absente du composeur coque | b8768db |
| LUDO-4 | Barre latérale en doublon du tiroir | b8768db |

## Plan d'action

### Vague 1 — avant toute bêta (bloque la release)
1. **Thème sombre de la coque (M1)** : appliquer le thème/`data-theme` au conteneur de la coque comme en classique. → sol.
2. **Premier devis sans contact (M2)** : permettre d'ajouter/saisir un contact depuis le canevas devis, ou rediriger proprement vers la création de contact puis retour. → sol.
3. **Onboarding robuste (M4, M5, m5)** : timeout + message + « configurer plus tard » sur l'étape LLM ; marquer terminé dès l'étape profil ; état de sauvegarde clair. → sol.
4. **Chat sans modèle (M6)** : état explicite « choisis d'abord un modèle » + raccourci réglages au lieu d'un échec muet. → sol.

### Vague 2 — cohérence coque
5. **Confirmation Agenda (M3)** : ajouter « Annuler » explicite, aligné sur Email/Images.
6. **Bouton Synoptïa (C1)** : étiquette passive sans chevron, ou vrai menu d'espaces (arbitrage Ludo).
7. **Cloche (M7)** : brancher sur le Brief du jour de la coque.
8. **Version affichée (m1)** : afficher la version d'interface réelle en bêta.

### Vague 3 — finitions
9. Libellé qualité Images (m2), en-tête fenêtre réduite (m3), format ROI (m4), stabilité identité entre sessions (C2, à relier au correctif profil déjà posé).

## Verdict croisé

- **OPT** : prêt bêta après vague 1 (le premier contact d'un nouvel utilisateur est le vrai risque).
- **sol** : non prêt en l'état ; défauts ciblés et réparables.
- **Consolidé** : NON pour l'instant, GO bêta réaliste après la vague 1 + un tour de recette Ludo.
