# Infomaniak. Adresse de chat par produit

Le moteur utilise `/1/ai/chat/completions`. Le banc HTTP strict confirme l’écart avec `/2/ai/{product_id}/openai/v1/chat/completions`. L’identifiant entier de produit AI Tools appartient au compte et le catalogue se lit sur le même produit. La validité réelle du modèle `mix` reste à mesurer avec un compte autorisé. [Portail Infomaniak](https://developer.infomaniak.com/docs/api/post/2/ai/%7Bproduct_id%7D/openai/v1/chat/completions).

## Contrat à implémenter

1. Demander l’identifiant de produit dans la mise en route et les réglages. Proposer une lecture via `GET /1/ai` si le compte autorise cette opération. Plusieurs produits exigent un choix explicite. Traiter l’identifiant comme une préférence et la clé comme un secret séparé.
2. Former exclusivement les URL Infomaniak du produit retenu. Le même réglage doit être pris en compte en conversation, dans l’Atelier et dans la vérification des modèles. Une ancienne configuration sans identifiant doit indiquer le champ manquant et préserver sa préférence de modèle.
3. Exercer la mise à niveau de profil, le cas sans produit, le compte multiproduit et les clés refusées avec des réponses simulées. Lire le catalogue authentifié et sélectionner un modèle valide avant d’éprouver en compte de test le flux, les outils et l’usage.

Report pour la 0.85. Le chemin dépend d’une valeur qui manque dans la configuration actuelle. Une valeur arbitraire pourrait désigner un autre produit.
