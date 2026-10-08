# Composition Git → listener préparée, non exécutée

Ce dossier est un successeur additif. Aucun gel antérieur n'a été changé.
Le renderer et ses dix méthodes de test sont préparés, mais ni évalués ni
exécutés dans ce lot. Le parseur Python est seulement utilisé pour une
vérification syntaxique et la comparaison statique des constantes et ancres.

## Origine et ordre exacts

1. Le port CDP historique a produit `trace-chrome.mjs` au SHA `93f3fef0…`.
2. Le gel Git `e28e4aa0…` contient onze textes effectivement rendus et le
   helper `f302e0fd…` de 15 031 octets. Son ancien préfixe `64555c1d…`
   est intégralement conservé. Son contexte porté est `9960ba63…`.
3. Le nouveau renderer consomme exactement ces onze textes et le seul
   `ownership-only.mjs` original `41eb7fcd…`. Il exige les pins complets,
   le helper Git et la même représentation du contexte Git. Il retourne
   douze textes, avec les trois seules différences du listener.

L'ancien renderer listener `af6a4af5…`, qui exige `64555c1d…`, reste intact.
Le nouveau module n'importe ni n'appelle cet ancien renderer. Ses quatre
constantes JS de transformation sont des copies exactes, et les neuf autres
textes sont préservés par son contrat. Le helper n'est pas transformé.
Sa table historique contient toujours cinq enfants RPC et neuf sites directs.

## Revue indépendante du listener

L'INDEX `04382da8…` a été rehashé : 23 références SHA/taille conformes.
Les trois différences et leurs inverses sont reconstruites exactement.
Aucun défaut déterministe du petit port n'a été identifié. Les contrôles
URL/verbes, les options Chrome, le CDP et le contexte restent inchangés.
Le helper coalesce seulement les scans en vol, sans cache TTL entre requêtes.
L'observation effective et les deux scans attribués demeurent à la charge
du parent Session ; ce renderer n'en fabrique aucune preuve.

Les six cas JS listener et les trente-cinq cas JS Git ont été rejoués par
main, dans des reçus distincts. Ils ne sont pas des résultats de ce renderer
composé et ne qualifient ni listener natif, ni G1, ni ronde A/B.

## Fichiers préparés et contrôle futur

`preimages/definitions/` contient les douze entrées épinglées. Les trois
fichiers sous `expected-definition-only/` sont copiés du gel listener comme
fixtures d'égalité attendue, pas produits par une exécution du nouveau module.
Les six différences JS avant/arrière et les préimages des renderers sont
conservées. `diffs/renderer-listener-to-git-listener.diff` explicite le seul
changement de lecteur : admission des textes Git/helper/context exacts,
retour des douze textes et garde de trois chemins modifiés.

Après lecture et GO distinct de main, les dix tests préparés peuvent être
joués en Python isolé sous une garde process/socket/écriture externe interdits.
Aucun runner Node, snapshot, checkout, appel produit ou Session n'est émis ici.
Les cas JS existants restent épinglés comme définitions, sans nouveau rejeu.

## Limites conservées

La couverture épinglée conserve encore son import Playwright historique et
son backend `17493`. Le listener refuse tous les ports hors `17593`/`5173`.
Ces définitions ne sont donc pas présentées comme un instrument A/B actuel
exécutable. Un futur port de préparation physique, séparé et relu, devra
fermer ces chemins et la source de ronde avant tout lancement réel.

`RUNTIME_ENABLED` et `OS_STARTUP_QUALIFIED` restent faux ; admissions et
capacités restent vides. Aucun accord, identité, HEAD courant, admission,
résultat WRAPPER ou réussite A/B n'est déduit d'une copie de définition.
Les obligations 27/78 et les quatorze sites sont inchangés.
