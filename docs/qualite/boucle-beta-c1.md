# Boucle bêta, cycle 1

Travail local sur `beta/c1-20261124`, depuis `fed73a97b`. La candidate 0.85.0 couvre le catalogue, Synthetic, l’affichage bêta, le contrôle des versions et quatre défauts hérités. Le contrôle a aussi corrigé la notice de raisonnement des GPT-6.2. Le registre neuf utilise `bc1-` pour distinguer les nouveaux constats des identifiants hérités.

## Lots préparatoires

| Lot | Commit | Preuve principale dans le dossier du cycle |
| --- | --- | --- |
| A · Catalogue `bc1-B-001` | `7295e8f44` | `portes/20261124-202539-A-catalogue-7295e8f44/`. 15 ajouts et 17 références d’anciennes générations conservées. Contrôles du catalogue, des tarifs, de l’effort, de Responses et du rejeu des outils. |
| B · Synthetic `bc1-B-002` | `72386c899` | `portes/20261124-205707-B-synthetic-72386c899/`. Enregistrement de clé fictive par l’API, préférence, sélecteur, export, consentement, flux simulé et continuation d’outil. |
| C · Bêta `bc1-B-003` | `cb9849359` | `portes/20261124-212522-C-phase-beta-cb9849359/`. Libellé et suffixe de phase partagés. Liens de téléchargement manuel vers `/therese/beta/`. |
| D · Versions `bc1-B-004` | `f2f5f918e` | `portes/20261124-215515-D-version-f2f5f918e/`. Tests des tags, du badge et du trajet du manifeste local. 129 tests Vitest ciblés, 16 cas du manifeste et 247 tests de scripts. |

La première porte catalogue a échoué sur des attentes de l’ancienne liste et sur l’accès au compilateur du banc Windows. Elle a aussi révélé un rejeu Playwright sur Références juridiques, conservé dans `preuves/A-intermittence/`. La porte du commit A passe sans rejeu instable.

Les têtes Anthropic et OpenAI suivent la décision de Ludo. Mistral passe à `mistral-large-4-0`, la tête précédente étant dépréciée. Les fiches du relevé séparent plafonds, contexte, effort et prix. Le compteur applique aussi les seuils GPT et la bascule de tarif Gemini prévue au 1er décembre. Pour DeepSeek, l’estimation retient le tarif plein en l’absence de calendrier chinois dans le compteur. Les tarifs des identifiants historiques de Perplexity et d’Infomaniak restent non confirmés. Les essais fournisseur utilisent des réponses simulées.

Synthetic propose sept modèles et quatre alias de repli. Son inventaire dynamique reprend le chemin déjà employé pour OpenRouter. L’essai trace l’identifiant à deux-points et barre oblique depuis le choix utilisateur jusqu’aux outils, avec une clé fictive. L’accord d’un autre fournisseur ne permet pas l’envoi Synthetic. Le texte attribue à Synthetic ses affirmations sur l’absence de conservation et d’entraînement à partir des requêtes, et indique le traitement aux États-Unis.

Le contrôle À propos accepte pour un numéro nu `0.85.0` les tags `v0.85.0-beta` et `v0.85.0-beta.1` du même numéro et propose `v1.0.0`. Lorsque le moteur déclare une préversion explicite, l’ordre SemVer reste appliqué. Le badge conserve son suffixe lors d’un bump numérique. Le guide embarqué porte son numéro 0.83.

### Remontée de la 0.84

- Reproduit en simulation. Sur Linux, le manifeste réserve le paquet Debian à la cible `.deb`. Le bandeau propose la page manuelle pour les autres types, conformément aux tests du manifeste.
- Reproduit en simulation. La vérification automatique demande le contexte Tauri, la préférence active et le délai prévu de 5 secondes puis 6 heures.
- Écarté pour le trajet simulé. Un serveur HTTP jetable sert un `latest.json` 0.84.0 à un double du plugin. Une installation 0.83.0 simulée voit la 0.84.0 dans le bandeau.
- Non vérifié pour la livraison native 0.83 vers 0.84 et le trousseau macOS. Le point de mise à jour utilisé par les installations existantes reste `/therese/alpha/latest.json`.

## Instruments, lecture et parcours

Les cinq instruments valident un témoin et un contrôle sain dans `depot/.app-loop/cycles/1/calibration/essai-rs77sO/`. Le contrôle navigateur observe le bouton masqué, une capture différente, un HTTP 503 simulé et l’erreur console témoin. Le premier essai exigeait en plus une ligne d’accès Uvicorn absente du banc. Le second éprouve la console et conserve les journaux du moteur. Les recalibrations après réparations se trouvent dans `essai-mi00K8/` et `essai-c2Ptoz/`.

L’inventaire initial contient 165 fichiers issus du diff et de ses imports directs. Les preuves avec empreinte, ancres et invariant couvrent 66 fichiers, soit les 61 fichiers modifiés et cinq imports directs. Le validateur demande encore 99 lectures et 19 doubles lectures. La transition MAP vers CALIBRATE a été forcée avec ce motif. La lecture complémentaire du diff E dans `preuves/E-carte-delta.md` ancre les 12 fichiers ajoutés ou modifiés pendant l’audit.

La recette du navigateur couvre les 13 modules des conventions du dépôt avec des profils jetables. Les preuves `E-recette-modules-UWYHja`, `E-recette-A1-d1IEmB`, `E-parcours-A2-SY37Pk` et `E-parcours-A3-oz6tt3` contiennent les étapes, le contrôle de visibilité, l’avancement de l’horloge et les évènements réseau. La recette couvre les transitions sélectionnées et les gardes de configuration, avec une création fictive de contact CRM. L’envoi cloud, la dictée matérielle et l’installation de connecteurs restent hors banc. Le garde-fou de sécurité exclut l’étape A3 de reproduction d’une injection.

## Réparations héritées

| Sujet | Commit | Test et mesure ciblée |
| --- | --- | --- |
| B-2065 · La recherche vide coupe la synthèse | `05c5f706d` | `test_c20_b1799_recherche_vide.py`. `E-b2065-rejeux-DEn6uH` compte 32 cas, dont dix entrées nouvelles. |
| B-2066 · Arrêt volontaire d’un connecteur | `9cba41236` | `test_b1825_mcp_echec_initialisation.py`. `E-b2066-rejeux-JrIeYN` compte 80 cas, dont douze entrelacements nouveaux et une mesure ASGI de la route publique. |
| B-2067 · Préserver la saisie du profil | `bf1f1ee4f` | `ProfileStep.recharge.b1840.test.tsx`. `E-b2067-rejeux-Hbk3q2` compte 33 cas, dont dix champs rejoués après correction. |
| B-2068 · Relire après l’enregistrement des clés | `d16905df8` | `LLMStep.changementFournisseur.b2058.test.tsx`. `E-b2068-rejeux-Ybgbrl` compte 70 cas, dont cinq fournisseurs mis en échec ou en succès. |

Chaque reproduction a été constatée avant correctif. Chaque sabotage a reproduit l’erreur initiale et a été restauré avant le commit. Les deux suites de démarrage MCP conservent aussi les attentes sur un vrai échec et sur l’annulation d’une requête.

## Reports mesurés

- **B-2062, PDF sans liens physiques.** Deux retours 500 lors de la génération d’un devis et d’une facture sur volume simulé. Deux relectures NO-GO et [design](../plans/2026-11-25-b2062-design.md). Reprendre la réservation commune aux formats, la reprise et la restauration avant toute modification du moteur.
- **B-2069, Board.** Dix succès locaux, entre 0,132 et 0,231 s pour le cas JUnit. Le dépassement de délai CI ne se reproduit pas dans ces mesures. Le délai historique de 5 secondes est conservé.
- **B-1923 et B-2034.** Joindre est désactivé dans le composeur d’e-mail. Une seconde anonymisation simulée peut annoncer la réussite avec un fichier restant. Le sort de Joindre et la reprise durable après anonymisation partielle demandent l’arbitrage produit de Ludo.
- **B-1835, B-1836 et B-1838.** 24 simulations Windows et six cas d’envoi fictif passent sur la branche. Les essais d’installation, les moteurs réels et l’envoi de mail réel restent hors banc.
- **Perplexity (`bc1-B-017`) et Infomaniak (`bc1-B-018`).** Deux écarts aux contrats documentés reproduits par HTTP simulé. Le témoin du format historique Perplexity reste lisible. [Design Perplexity](../plans/2026-11-25-perplexity-agent.md), [design Infomaniak](../plans/2026-11-25-infomaniak-produit.md).

## Rondes et candidate

La relecture des imports s’est poursuivie après la sortie de MAP. Pour l’inventaire des lots A à D, 113 fichiers sur 165 ont finalement une preuve validée (68,48 %). Les 52 lectures restantes et les 19 doubles lectures manquantes empêchent une validation complète. Le diff E et la correction de GPT-6.2 ont leur relevé complémentaire dans `preuves/E-carte-delta.md`.

La relecture a révélé le défaut `bc1-B-019`. Les deux GPT-6.2 utilisaient déjà Responses mais l’écran annonçait une désactivation du raisonnement avec les outils. `3b7a35ea7` affiche Auto et explique le choix du modèle. Deux cas rouges, dix transitions depuis un autre modèle, 73 cas Vitest ciblés, 45 cas Python et sabotage reproduisant l’ancien texte dans `preuves/E-b019-*`.

Les deux premières rondes ont établi la référence sur `d16905df8`. La découverte de `bc1-B-019` a remis le compteur à zéro. Les deux rondes après correction ont exécuté la porte complète et les trois personas sur `3b7a35ea7`, avec des profils neufs. Chacune a franchi 38 étapes et terminé sans échec ni rejeu instable.

| Ronde après correction | Porte complète | Traces et contrôle visuel |
| --- | --- | --- |
| Première | `portes/20261124-234956-E-ronde-3-3b7a35ea7` | `preuves/E-ronde-3-A1-RbciUA`, `E-ronde-3-A2-qFY2fG`, `E-ronde-3-A3-eesqHF`, `E-ronde-3-visuel.md` |
| Seconde | `portes/20261125-001700-E-ronde-4-3b7a35ea7` | `preuves/E-ronde-4-A1-Il7OG3`, `E-ronde-4-A2-y9WB1o`, `E-ronde-4-A3-K4OH8R`, `E-ronde-4-visuel.md` |

Chaque porte complète déclare 7 355 cas pytest, 187 autonomes, 4 374 Vitest et 112 Playwright. Les listes de sauts hérités comptent 15 cas pytest et quatre autonomes. Les traces gardent le rechargement d’isolation du profil et la reprise de la lecture des accords avec HTTP 200. La console, le réseau et le moteur ne montrent aucun autre écart dans les transitions parcourues.

Le registre affiche 0/2 au plateau formel, neuf sujets corrigés, six reportés et quatre rejetés. La carte partielle et les sauts historiques suffisent au refus. Les deux rondes ont aussi le même agent. Les deux rondes locales vertes ont permis d’appliquer la dérogation du cycle pour passer de ZERO_CHECK à GAP_SCAN. La sortie initiale de MAP est l’autre transition forcée. Les refus sont conservés dans les preuves.

La proposition P-001 demande de vérifier le volume au choix du dossier facturation pour signaler la contrainte avant de produire le PDF. La proposition attend la décision de Ludo, comme les propositions P-163 à P-172 du cycle précédent.

Le bump en 0.85.0 a synchronisé les versions, y compris le verrou npm de la racine. La révision du format uv est passée de 2 à 3 sans changement de dépendance. Le rafraîchissement des licences réutilise les 1 327 notices vérifiées à archive et empreinte identiques. Les journaux sont dans `preuves/Candidate-bump-WAHbus/`.

La porte candidate complète la validation par le build frontend, le contrôle de synchronisation, les licences, Ruff sur les tests, `pip-audit` et les tests de scripts. Les résultats bruts de cette porte figurent dans `RENDU.md`, avec les contrôles natifs hors machine et les décisions proposées à Ludo.
