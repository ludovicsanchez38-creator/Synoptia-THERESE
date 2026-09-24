# Arbitrages par délégation (24/09/2026)

Consigne de Ludo après la v0.75.0-alpha : « Décide ce que tu peux décider,
corrige et entame le prochain cycle ». Chaque arbitrage ci-dessous est pris par
Claude, dans le sens le plus prudent et réversible ; Ludo peut revenir sur
n'importe lequel. Ne sont pas tranchés ici : ce qui demande une maquette ou un
goût (P-092) et le ménage du Mac (Ludo a déjà choisi le 24/09).

## Règles techniques

**B-1120 : neutralisation des formules à l'import et à l'export.** Une valeur
est une formule potentielle si elle commence par `=`, `@`, une tabulation ou un
retour chariot, ou par `+` ou `-` suivi d'autre chose qu'une forme de nombre ou
de téléphone (chiffres, espaces, points, tirets, barres obliques, parenthèses).
« +33 6 12 34 56 78 » et « -500 » restent intacts ; « +1+cmd|' /C calc'!A0 »
est désamorcé par une apostrophe. La même règle vaut à l'import et à l'export,
qui divergeaient : l'import abîmait les téléphones, l'export laissait passer
« +1+cmd ». Les valeurs déjà stockées avec une apostrophe ne sont pas réécrites.

**B-1108, B-1125 : la synchronisation du tableur n'efface pas.** Le tableur
fait foi pour ce qu'il dit, pas pour ce qu'il tait : une cellule vide ou une
valeur inconnue ne remplace pas la valeur enregistrée (client d'un projet,
statut d'un projet, d'une tâche ou d'un livrable). Les statuts accentués ou en
anglais sont reconnus. Une ligne incomplète (livrable sans projet) est écartée
avec un message, sans faire tomber la synchronisation. Même règle que les
imports de fichier (B-1083, B-1106, B-1109).

**B-1139 : l'extraction d'entités suit le fournisseur de la conversation.**
Une conversation menée avec un modèle local n'envoie pas ses messages à un
fournisseur en ligne pour en extraire les contacts et projets. Si le modèle
local est indisponible, l'extraction est sautée, sans repli en ligne. Même
promesse que B-1071.

**B-1153 : les commandes des agents s'exécutent dans un bac à sable.** La garde
des arguments (P-100) ne confine pas l'exécution : un `pytest.ini` écrit par un
agent a vidé un dossier hors du dépôt. Le cycle 13 conçoit un confinement de
l'écriture au dossier de travail de l'agent et au dossier temporaire, design
contesté avant le code (règle maison), avec un refus explicite sur une
plateforme où le confinement n'est pas disponible.

## Propositions

**P-102 : acceptée.** Sous Linux, une commande supprimée va dans la corbeille
du bureau (freedesktop) plutôt que d'être effacée. Petite, réversible, dans la
ligne « jamais d'effacement définitif sans le dire ».

**P-092 : non tranchée.** Trois panneaux côte à côte change la coque : elle
attend une maquette et le regard de Ludo.

## P-096, brouillons d'e-mails en lot : les onze décisions

Options retenues, toutes celles recommandées dans le plan (`2026-09-24-p096-brouillons-en-lot.md`) :

1. Libellé visible « Écrire un e-mail », repris dans la palette et le titre.
2. Pas de signature ajoutée ; l'aperçu dit « sans signature ».
3. RGPD : contacts archivés exclus ; consentement expiré et base légale vide
   signalés, sans blocage ; portée globale seule en V1.
4. Espace de noms `{contact_prenom}` confirmé, préfixe `contact_` réservé.
5. Le moteur garde le modèle non résolu jusqu'à la fin du lot plus 30 jours ;
   la promesse devient « aucun corps personnalisé en base ».
6. « Déjà écrit il y a moins de 24 h » : avertissement, contact décoché par défaut.
7. Pas de trace sur la fiche tant que le brouillon n'est pas envoyé.
8. Éléments du lot conservés 30 jours, effacés avec le contact.
9. Pas de saisie en ligne d'un champ manquant en V1 ; lien vers la fiche.
10. Réponses de la V1 confirmées : champ vide bloquant sans repli, plafond 50.
11. Signature : voir le point 2.

La V3 du design intègre ces choix et les constats P2 et P3 de la revue V2 ;
elle passe en revue adverse avant tout code.
