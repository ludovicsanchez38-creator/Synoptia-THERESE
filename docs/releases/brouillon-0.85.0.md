# THÉRÈSE 0.85.0 · Brouillon de la bêta

Candidate locale 0.85.0 sur `beta/c8-20261125`, avec les correctifs du catalogue jusqu’à `22f4b0ef7`. Ludo a choisi le nom public `v0.85.0-beta`. [Cycle 1](../qualite/boucle-beta-c1.md) · [Cycle 2](../qualite/boucle-beta-c2.md) · [Cycle 3](../qualite/boucle-beta-c3.md) · [Cycle 4](../qualite/boucle-beta-c4.md) · [Cycle 5](../qualite/boucle-beta-c5.md) · [Cycle 6](../qualite/boucle-beta-c6.md) · [Cycle 7](../qualite/boucle-beta-c7.md) · [Cycle 8](../qualite/boucle-beta-c8.md)

## Mise en route et usage

- Dès l’accueil, THÉRÈSE propose un premier geste utile, comme préparer une relance de devis. Tu peux créer ton profil, importer un profil existant ou continuer sans dossier.
- Si ton service d’IA est prêt, tu vois tout de suite son nom et le modèle choisi. La procédure de configuration se déplie à la demande. Avant de donner ton accord à Claude, tu peux lire ce qui accompagne un premier « Bonjour », y compris quand tu as rempli ton profil.
- **Paramètres > Service d’IA** affiche le coût mensuel estimé en dollars et le détail du jour et du mois. Le compteur applique le prix réduit des relectures du cache Anthropic et compte les appels annexes dont l’usage est reçu. Les mesures réelles sur Sonnet 5.5 et Fable 5.2 concordent au millième de dollar.
- Un filtre de la Mémoire précise où les fiches restent disponibles. Dans Devis et factures, la ligne du brouillon indique près du bouton PDF les mentions émetteur ou destinataire à compléter.

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
- Avec l’ouverture directe sur le chat activée, un lien vers Mémoire ouvre la vue demandée.
- Le Board protège la persistance d’une délibération une fois le suivi installé. Le test de déconnexion P24 passe 50 fois sur 50 à quatre processus.
- Le Board laisse partir un seul appel de récupération à la fois auprès du fournisseur concerné. Quand une clé de conseiller manque, le message renvoie vers **Paramètres > Service d’IA**.
- Passer par GPT-6.2 conserve l’effort enregistré. Le plafond en mode réflexion de Qwen4-Max et le niveau Très élevé de DeepSeek suivent leurs contrats.
- DeepSeek conserve les outils et l’historique quand une réponse précédente ne contient plus son raisonnement. Le chat signale le passage sans réflexion pour cet échange. [Contrat DeepSeek](https://api-docs.deepseek.com/guides/thinking_mode/)
- Le guide d’installation dirige les testeurs de la bêta vers les téléchargements. L’aide embarque le guide des testeurs 0.85, avec les écrans de démarrage, À propos et Synthetic. [Source du guide](../USER_GUIDE_ALPHA.md)
- Le composeur d’e-mail masque la commande Joindre jusqu’à la prise en charge des pièces jointes.
- La mise en route et les paramètres préviennent si THÉRÈSE rencontre un refus de création de lien physique dans le dossier des PDF. L’application propose de choisir un dossier dédié sur le disque interne.

## Limites connues de la bêta

- Après un arrêt manuel d’une réponse, le coût du début de la réponse n’apparaît pas au compteur.

## Points à vérifier avant diffusion

- Rejouer la construction à blanc sur la candidate du cycle 8. Le catalogue couvre les quatre bibliothèques relevées sur les runners Linux et Windows et l’archive Linux fournit les sources exactes de glibc `2.35-0ubuntu3.18`.
- Produire le PDF 0.85 à partir de la source de novembre 2026. Le canal de mise à jour des installations existantes utilise `/therese/alpha/latest.json`.
- Les PDF de facturation demandent un dossier où les liens physiques sont possibles. Essayer le choix du dossier et la génération PDF sur les trois systèmes, avec un volume interne et un volume externe incompatible. La reprise durable de l’anonymisation est au stade du design.
- Avec les comptes de Ludo, vérifier Synthetic, DeepSeek au deuxième message avec outil, Perplexity et Infomaniak. Le banc Linux a contrôlé les parcours Synthetic et DeepSeek avec des transports simulés.
- Vérifier les builds Tauri, l’installation native, le trousseau, l’enregistrement des fichiers Office et la mise à jour de la 0.84 à la 0.85.
- L’application macOS attend sa signature Apple. Ludo a décidé de diffuser la bêta pendant cette attente. Le guide explique comment ouvrir le téléchargement officiel si Gatekeeper le bloque.
- Rejouer le Board cloud avec les cinq comptes des conseillers. Sur le banc Anthropic, l’avis de l’Analyste et la synthèse sont terminés et consultables dans l’historique. Une délibération à cinq signale les comptes indisponibles avant de contacter les services.

## Carte proposée

- De nouveaux Claude, GPT et Gemini rejoignent le catalogue. OpenAI propose GPT-6.2 Sol par défaut et GPT-6.2 Astra pour les tâches complexes.
- Synthetic rejoint les services d’IA. La connexion réelle reste à essayer.
- THÉRÈSE s’affiche en bêta, avec le lien de téléchargement mis à jour.
- À propos reconnaît les numéros publiés sur le canal bêta.
- La mise en route montre l’IA utilisable, propose une relance comme premier geste et te permet de continuer sans dossier.
- Le chat peut finir sa réponse quand une recherche suivante ne trouve rien.
- Le guide 0.85 se lit dans l’aide. Il indique le geste d’ouverture sur macOS en attendant la signature Apple.
- Les réglages standard affichent le coût estimé en dollars, avec le prix des relectures du cache Anthropic.
