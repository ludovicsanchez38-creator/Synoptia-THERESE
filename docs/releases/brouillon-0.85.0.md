# THÉRÈSE 0.85.0 · Brouillon de la bêta

Candidate locale sur `beta/c5-20261125`, à partir de la candidate du cycle 4. Ludo a choisi le nom public `v0.85.0-beta`. [Cycle 1](../qualite/boucle-beta-c1.md) · [Cycle 2](../qualite/boucle-beta-c2.md) · [Cycle 3](../qualite/boucle-beta-c3.md) · [Cycle 4](../qualite/boucle-beta-c4.md) · [Cycle 5](../qualite/boucle-beta-c5.md)

## Nouveautés

- Quinze modèles récents rejoignent le catalogue, dont Claude Fable 5.2, GPT-6.2 Astra et Sol, de nouveaux Gemini 4, Mistral Large 4.0 et Kimi K3.1 Pro. GPT-6.2 Sol devient le choix par défaut d’OpenAI et GPT-6.2 Astra reste proposé pour les tâches complexes. Si GPT-6 Sol est déjà enregistré, le chat conserve ce choix. Les anciennes préférences de modèle restent utilisables dans l’application. Avec GPT-6.2, le modèle choisit son effort de raisonnement, même avec les outils. Mistral Large 4.0 devient la recommandation Mistral.
- Synthetic rejoint les services d’IA disponibles. Ses identifiants, sa notice de confidentialité et l’accord d’envoi par fournisseur ont été éprouvés sans réseau. La connexion au service avec un compte réel reste à vérifier.
- La phase Bêta apparaît dans l’application. Les liens de téléchargement manuel mènent à la page bêta. L’onglet À propos traite un tag de préversion du même numéro comme la même version numérique lorsque le moteur ne donne que ce numéro.

## Réparations

- Le chat peut terminer la synthèse lorsqu’une première recherche utile est suivie d’une recherche vide.
- Les coûts Anthropic tiennent compte du prix de lecture et d’écriture du cache. Le total des réglages inclut l’extraction automatique du chat quand le fournisseur en renvoie l’usage.
- Un arrêt volontaire pendant le lancement d’un connecteur garde l’état arrêté et libère ses processus de préparation.
- La mise en route conserve les champs déjà saisis et les données légales du profil. Elle propose de relire le profil après un échec de chargement. Le moteur distingue ce cas d’un profil absent et protège la fiche illisible d’un remplacement. La vérification des clés reprend après l’écriture dans le coffre.
- Un connecteur actif termine son arrêt avant de redémarrer.
- Le Board protège la persistance d’une délibération une fois le suivi installé. Le test de déconnexion P24 passe 50 fois sur 50 à quatre processus.
- Le Board laisse partir un seul appel de récupération à la fois auprès du fournisseur concerné.
- Passer par GPT-6.2 conserve l’effort enregistré. Le plafond en mode réflexion de Qwen4-Max et le niveau Très élevé de DeepSeek suivent leurs contrats.
- DeepSeek conserve les outils et l’historique quand une réponse précédente ne contient plus son raisonnement. Le chat signale le passage sans réflexion pour cet échange. [Contrat DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode/)
- Le guide d’installation dirige les testeurs de la bêta vers les téléchargements. L’aide embarque le guide des testeurs 0.85, avec les écrans de démarrage, À propos et Synthetic. [Source du guide](../USER_GUIDE_ALPHA.md)
- Le composeur d’e-mail masque la commande Joindre jusqu’à la prise en charge des pièces jointes.
- La mise en route et les paramètres préviennent si THÉRÈSE rencontre un refus de création de lien physique dans le dossier des PDF. L’application propose de choisir un dossier dédié sur le disque interne.

## Points à vérifier avant diffusion

- Produire le PDF 0.85 à partir de la source du guide. Le canal de mise à jour des installations existantes utilise `/therese/alpha/latest.json`.
- Les PDF de facturation demandent un dossier où les liens physiques sont possibles. Essayer le choix du dossier et la génération PDF sur les trois systèmes, avec un volume interne et un volume externe incompatible. La reprise durable de l’anonymisation est au stade du design.
- Avec les comptes de Ludo, vérifier Synthetic, DeepSeek au deuxième message avec outil, Perplexity et Infomaniak. Le banc Linux a contrôlé les parcours Synthetic et DeepSeek avec des transports simulés.
- Vérifier les builds Tauri, les signatures, l’installation native et la mise à jour de la 0.84 à la 0.85.
- Rejouer le Board cloud jusqu’à la synthèse avec les comptes des conseillers. Le banc Anthropic a accepté l’appel de l’Analyste et atteint son délai de recette avant la fin de l’avis.

## Carte proposée

- De nouveaux Claude, GPT et Gemini rejoignent le catalogue. OpenAI propose GPT-6.2 Sol par défaut et GPT-6.2 Astra pour les tâches complexes.
- Synthetic rejoint les services d’IA. La connexion réelle reste à essayer.
- THÉRÈSE s’affiche en bêta, avec le lien de téléchargement mis à jour.
- À propos reconnaît les numéros publiés sur le canal bêta.
- La mise en route conserve mieux les informations que tu viens de saisir.
- Le chat peut finir sa réponse quand une recherche suivante ne trouve rien.
- Le guide 0.85 se lit directement dans l’aide. Pour les PDF de devis et de factures, THÉRÈSE peut te prévenir au choix du dossier.
- Pour Anthropic, le compteur prend en compte l’économie du cache et le coût de l’extraction automatique.
