# Stabilité du système pendant un tour Anthropic

Vérification du 28 octobre 2026 : hypothèse confirmée par la documentation officielle.

[Thinking, preserved thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) décrit la liaison des signatures au système, aux outils et aux messages précédents. [Troubleshooting thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting#a-400-error-says-a-thinking-block-signature-is-invalid) précise les modèles concernés (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5), le contrôle pour les comptes créés depuis le 31 août 2026 et le refus 400 si le préfixe change.

`LLMService.continue_with_tool_results` appelait `actualiser_fiches(..., suite)`, qui reconstruit le système et peut retailler les messages. Une fiche écrite par un outil suffisait à changer le préfixe signé. La continuation Anthropic conserve désormais ce préfixe et vérifie seulement le budget. Le premier appel du tour utilisateur suivant relit les fiches. Les résultats des outils restent transmis au tour courant.

Le test utilise le vrai adaptateur Anthropic et un serveur simulé qui refuse un système modifié. Il couvre l'ajout d'une première fiche et la modification d'une fiche existante, conserve le bloc signé et vérifie la relecture au tour suivant. Avant correction : deux refus 400 ; après : deux succès. Aucun compte ni clé réelle utilisé.
