# Proposition d’essais de compatibilité macOS pour THÉRÈSE 0.83

Ce plan répond à la carte val-2026-11-08-13, q3, issue de q4 de la carte val-2026-11-08-06 et de la réserve C252. Il attend une lecture de Ludo avant diffusion. Aucun essai macOS décrit ici n’a été exécuté dans cette préparation Linux. Aucune procédure de construction ou de restauration n’est présentée comme vérifiée.

## Point de départ vérifié dans le dépôt

La base applicative examinée est `26d75e5f1438f063ef946ba976f41f3983627011`, version 0.83.0. Le guide `docs/GETTING_STARTED.md` annonce macOS 14+. Le guide `docs/CONTRIBUTING.md` et `src/frontend/src-tauri/tauri.conf.json` indiquent 10.15. Ces trois mentions restent inchangées pendant la préparation des essais.

La matrice de construction de `.github/workflows/release.yml` prévoit un paquet macOS pour `aarch64-apple-darwin`. Elle ne prévoit pas de paquet macOS Intel dans cette matrice. Cette lecture du fichier ne prouve ni l’existence d’un paquet utilisable ni sa compatibilité. Aucun workflow n’est déclenché par ce plan.

## Versions et architectures à couvrir

| Version de macOS à examiner | Parcours prévu | État initial |
|---|---|---|
| 10.15 | Intel, pour examiner le minimum déclaré par Tauri et CONTRIBUTING | Non essayé ; paquet Intel à identifier avant tout essai |
| 11 | Apple Silicon ; Intel si un paquet Intel est retenu | Non essayé |
| 12 | Apple Silicon ; Intel si un paquet Intel est retenu | Non essayé |
| 13 | Apple Silicon ; Intel si un paquet Intel est retenu | Non essayé |
| 14 | Apple Silicon, pour vérifier le minimum annoncé dans GETTING_STARTED ; Intel si retenu | Non essayé |
| 15 | Apple Silicon ; Intel si retenu | Non essayé |
| 26 | Apple Silicon ; Intel si retenu | Non essayé |

Cette liste sert à départager les deux minima existants. Avant les essais, inventorier les machines de laboratoire disponibles et compléter la liste si d’autres versions sont visées. Noter la version complète et le numéro de build de chaque système. Une machine indisponible laisse une case « non essayé ». Un résultat sous traduction d’architecture doit être consigné séparément ; il ne valide pas une exécution native.

Le périmètre Intel reste à soumettre à Ludo si aucun paquet 0.83 de cette architecture n’est disponible. Ne pas en construire un pour combler la case dans cette passe.

## Préparation des essais futurs

Utiliser exclusivement un compte de laboratoire avec des données factices. Son dossier personnel et son trousseau doivent être séparés du profil habituel. Prévoir une copie de l’état initial du laboratoire avant tout essai qui écrit des données. Aucun compte client ni secret de production ne doit être utilisé.

Identifier un paquet 0.83 dont l’utilisation pour ces essais est autorisée. Consigner son origine et son empreinte SHA-256, avec le commit de construction s’il est attesté. Chaque cellule de la matrice doit désigner exactement le paquet essayé. Un changement de paquet invalide la comparaison tant que les cellules concernées n’ont pas été rejouées.

Contrôler l’origine du paquet et les protections de macOS avant le lancement. Si une alerte apparaît, conserver son motif et interrompre le parcours jusqu’à son analyse. Aucune désactivation de Gatekeeper ni suppression manuelle de quarantaine n’est prévue par ce plan.

Préparer les fichiers factices et les modèles locaux nécessaires dans le laboratoire. Bloquer les sorties vers les fournisseurs distants pendant l’essai. Si une ressource locale manque, noter le blocage au lieu de déclarer le parcours réussi ou d’utiliser une clé réelle.

## Vérifications dans chaque cellule

| Vérification prévue | Résultat attendu et preuve à conserver |
|---|---|
| Métadonnées des exécutables | Relever les architectures et les minima macOS réellement déclarés par Tauri, le backend Python et leurs bibliothèques embarquées. Un minimum déclaré reste une condition à confronter au fonctionnement réel. |
| Installation dans le laboratoire | Le paquet est accepté avec les protections actives. Consigner tout refus, sans le contourner. |
| Premier lancement | L’interface Tauri et le backend embarqué démarrent. L’amorçage privé aboutit sans afficher ni extraire le jeton. Conserver une capture sans donnée sensible ou un constat daté. |
| Santé des données | Contrôler la réponse de `/health` sur la boucle locale. Le parcours nominal attend `healthy` avec les services disponibles. Une réponse `degraded` ou `recovery` impose un diagnostic et ne vaut pas réussite du parcours nominal. |
| Persistance locale | Créer une fiche contact factice, quitter normalement puis rouvrir. Vérifier que cette fiche est conservée et lisible. |
| Index embarqué | Indexer un document factice puis retrouver son contenu par une recherche. Un index indisponible maintient ce contrôle en échec ou bloqué. |
| Parcours local sans fournisseur distant | Essayer une conversation avec un modèle local identifié. Consigner le modèle utilisé. Une réponse obtenue avec un autre service ne valide pas ce parcours. |
| Sauvegarde et restauration | Créer une sauvegarde chiffrée du profil factice. Essayer sa restauration dans un second profil de laboratoire séparé, après copie de l’état de ce second profil. Vérifier les données restaurées sans ouvrir ni afficher de clé. En l’absence de procédure isolée vérifiée, consigner « bloqué », sans remise à zéro. |
| Fermeture et second lancement | Quitter normalement et vérifier que le port 17293 est libéré avant de relancer. Un résidu ou une perte de données constitue une anomalie. |
| Dossier personnalisé | Rejouer la persistance et la sauvegarde avec un dossier de données factice distinct. Vérifier son emplacement avant toute copie ; conserver le profil initial. |

Pour chaque contrôle, relever « réussi », « échec », « bloqué » ou « non essayé », avec la preuve locale et l’anomalie éventuelle. Les journaux remis doivent être limités aux erreurs utiles, sans ligne de commande complète ni configuration privée. La date et le nom du relecteur doivent accompagner le résultat.

## Comment proposer un minimum commun

Pour un paquet et une architecture donnés, retenir comme borne technique le plus élevé des minima déclarés par les composants obligatoires. Une inspection de métadonnées seule ne suffit pas à annoncer la compatibilité.

Le minimum proposé doit aussi correspondre à un système où tous les contrôles ci-dessus réussissent avec le même paquet. Les versions intermédiaires et supérieures visées par la matrice doivent être couvertes ; une case en échec, bloquée ou non essayée ne permet pas d’étendre la compatibilité à cette version. Un résultat sur un système récent ne valide pas un système plus ancien.

Si plusieurs architectures sont retenues, calculer la borne pour chacune et proposer une borne commune seulement si les résultats complets le permettent. Si leurs périmètres diffèrent, présenter les options à Ludo avant de rédiger une mention publique ; ne pas transformer l’absence de paquet Intel en promesse de compatibilité.

Après les essais, remettre à Ludo la matrice avec ses preuves et une proposition de minimum justifiée. Présenter les Avant et Après exacts des deux guides et de la configuration Tauri dans une même décision. Les minima affichés ne changent qu’après ces essais et son accord sur les textes.
