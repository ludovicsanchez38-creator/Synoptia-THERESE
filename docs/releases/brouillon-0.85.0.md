# THÉRÈSE 0.85.0 · Brouillon de la bêta

Cette candidate est préparée sur la branche `beta/c2-20261125`. Ludo décide du numéro et du tag public après lecture des deux rapports et du rendu du banc. [Cycle 1](../qualite/boucle-beta-c1.md) · [Cycle 2](../qualite/boucle-beta-c2.md)

## Nouveautés

- Quinze modèles récents rejoignent le catalogue, dont Claude Fable 5.2, GPT-6.2 Astra et Sol, de nouveaux Gemini 4, Mistral Large 4.0 et Kimi K3.1 Pro. Les anciennes préférences de modèle restent utilisables dans l’application. Avec GPT-6.2, le modèle choisit son effort de raisonnement, même avec les outils. Mistral Large 4.0 devient la recommandation Mistral.
- Synthetic rejoint les services d’IA disponibles. Ses identifiants, sa notice de confidentialité et l’accord d’envoi par fournisseur ont été éprouvés sans réseau. La connexion au service avec un compte réel reste à vérifier.
- La phase Bêta apparaît dans l’application. Les liens de téléchargement manuel mènent à la page bêta. L’onglet À propos traite un tag de préversion du même numéro comme la même version numérique lorsque le moteur ne donne que ce numéro.

## Réparations

- Le chat peut terminer la synthèse lorsqu’une première recherche utile est suivie d’une recherche vide.
- Un arrêt volontaire pendant le lancement d’un connecteur garde l’état arrêté et libère ses processus de préparation.
- La mise en route conserve les champs déjà saisis et les données légales du profil. Elle demande une nouvelle lecture après un échec de chargement. La vérification des clés reprend après l’écriture dans le coffre.
- Un connecteur actif termine son arrêt avant de redémarrer.
- Le Board protège la persistance d’une délibération une fois le suivi installé. Le test de déconnexion P24 passe 50 fois sur 50 à quatre processus.
- Passer par GPT-6.2 conserve l’effort enregistré. Le plafond en mode réflexion de Qwen4-Max et le niveau Très élevé de DeepSeek suivent leurs contrats.

## Points à vérifier avant diffusion

- Le guide embarqué reste celui de la 0.83. Le guide 0.85 est à produire et le canal de mise à jour des installations existantes reste `/therese/alpha/latest.json`.
- Les PDF de facturation demandent encore un volume prenant en charge les liens physiques. Le report de la reprise RGPD, celui de la commande Joindre et les migrations des fournisseurs historiques figurent dans le rapport du cycle.
- Sur DeepSeek, une nouvelle question avec outils peut être refusée si la conversation contient une réponse précédente. Le second appel du banc simulé montre l’absence de `reasoning_content` dans l’historique renvoyé au fournisseur. Régler ce cas avant diffusion. [Contrat DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode/)
- Les installations natives Windows et macOS, les signatures, la mise à jour de la 0.83 en natif et la clé Synthetic restent à éprouver en dehors de ce banc Linux.

## Carte proposée

- Plus de modèles sont disponibles dans THÉRÈSE, dont les nouveaux Claude, GPT et Gemini.
- Synthetic rejoint les services d’IA. La connexion réelle reste à essayer.
- THÉRÈSE s’affiche en bêta, avec le lien de téléchargement mis à jour.
- À propos reconnaît les numéros publiés sur le canal bêta.
- La mise en route conserve mieux les informations que tu viens de saisir.
- Le chat peut finir sa réponse quand une recherche suivante ne trouve rien.
- Le guide reste en 0.83. Pour les PDF de factures, garde un dossier de travail sur un disque compatible.
