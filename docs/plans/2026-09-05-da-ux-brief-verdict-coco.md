VERDICT : GO AVEC RÉSERVES

Le brief mérite une exploration, mais il n’est pas encore un contrat de réalisation suffisamment précis. **Application affinée est la base la plus solide. Continuité et Hybride restent explorables, sous conditions explicites.** Aucun changement de couleur ou de police ne résoudra seul le sentiment d’une application générique.

Audit effectué en lecture seule : documents lus dans l’ordre, captures jointes et captures sombres 30, 31, 33 inspectées, contrastes calculés avec Python. Les tests ont été analysés, pas exécutés.

1. **[Majeur] Continuité : risquée. La transposition littérale du site rencontre des verrous réels.**

   Remplacer `--font-family-display` par Instrument Serif ferait échouer [polices.test.ts:59](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/polices.test.ts:59>), qui exige Jakarta en tête de pile. **Ce test n’interdit cependant pas toute police supplémentaire** : une famille éditoriale distincte, réellement embarquée, est techniquement envisageable.

   Autre verrou absent des six tests cités : [couleursDeDomaine.test.ts:281](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/couleursDeDomaine.test.ts:281>) refuse le littéral `#2451FF` dans les composants TSX et documente l’identité propre de THÉRÈSE. Importer exactement la couture Synoptïa exige donc davantage qu’un copier-coller.

   **Correction :** conserver Jakarta pour les titres fonctionnels et les cartes ; éprouver Instrument Serif uniquement sur quelques grands titres éditoriaux, avec un jeton distinct et un chargement local. À 16 px, ses déliés constituent un risque de lecture à tester, pas une non-conformité WCAG automatique. Le papier est admissible ; les encres du site ne le sont pas toutes.

2. **[Majeur] Application affinée : solide, mais « davantage de respiration » peut aggraver les écrans.**

   Elle respecte les familles, l’accent d’action et les rayons existants : [globals.css:124](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/globals.css:124>) et [Button.tsx:25](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/ui/Button.tsx:25>).

   Sur la capture **18**, trois factures occupent déjà une grande hauteur. Sur **51**, l’espace entre la carte, les parcours et le composeur est abondant. Ajouter systématiquement des marges de 24 ou 32 px produirait surtout moins d’informations visibles.

   **Correction :** définir deux rythmes dans le même système : lecture confortable pour une synthèse, densité maîtrisée pour les listes. Donner une signature par l’organisation du travail, les montants, les échéances et les relations entre éléments. « Un geste principal » signifie une priorité visuelle, sans disparition des autres actions ni des confirmations.

3. **[Majeur] Hybride deux mondes : risquée, avec le coût d’intégration le moins visible dans le brief.**

   « Garder ses jetons » tout en introduisant du papier et un sous-espace navy impose de définir des **contextes de couleur locaux complets**. Changer seulement le fond rendrait certains textes et contrôles illisibles.

   Les bulles possèdent déjà une identité cohérente entre thèmes dans [globals.css:448](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/globals.css:448>). Les captures **30 à 33** montrent également une continuité sombre entre factures, projets, accueil et tâches.

   **Correction :** conserver un ordre conversationnel unique, y compris dans le DOM. Éviter deux colonnes permanentes à 1024 px. Définir, pour chaque région, fond, surface, texte, texte secondaire, domaine, focus, sélection et états. Prévoir aussi les menus et tiroirs rendus hors de cette région.

   En sombre, les messages humains doivent pouvoir rejoindre les surfaces sombres existantes : une grande colonne papier permanente contredirait le choix du thème. Enfin, le navy doit identifier un rôle, sans faire passer une suggestion d’IA pour une action exécutée ou une information validée.

4. **[Bloquant] Les encres du site ne peuvent pas devenir directement les encres de l’application.**

   Sur papier, `#0891B2` donne **3,52:1** et `#DB2777` **4,40:1**. Les deux échouent au seuil demandé. Sur le fond actuel, elles descendent respectivement à **3,40:1** et **4,25:1**.

   THÉRÈSE distingue justement les couleurs de remplissage des encres dans [globals.css:28](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/globals.css:28>). Remplacer ses encres par celles du site ferait échouer les assertions correspondantes de [a11y.test.tsx:203](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/test/a11y.test.tsx:203>).

   **Correction :** conserver `#0E7490` et `#BE1A72` comme références d’encres claires ; réserver les couleurs vives aux usages validés de remplissage et de décoration. Le violet demandé passe sur papier, mais échoue sur navy : il ne doit pas devenir une constante indépendante du thème.

   La paire bouton `#06121F` sur `#22D3EE` atteint bien **10,43:1**. Aucune nécessité de la remplacer pour gagner en caractère.

5. **[Bloquant] Le brief surestime ce que les gardes prouvent, notamment pour des maquettes HTML séparées.**

   Trois distinctions doivent être écrites :

   - [contrasteDesTeintes.test.ts:33](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/contrasteDesTeintes.test.ts:33>) compose **dix couleurs d’agent et sémantiques sur blanc**, à 10, 20 et 30 %. Ce n’est pas un contrôle universel de chaque texte sur chaque surface.
   - [opaciteSurLeTexte.test.ts:27](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/opaciteSurLeTexte.test.ts:27>) cherche `text-text-muted/…`. Il ne détecte pas toutes les opacités de parents, les animations ou les mélanges CSS.
   - Les balayages de composants ciblent les sources TS/TSX de l’application. Une page HTML déposée dans la documentation peut leur échapper entièrement.

   Les autres gardes comptent aussi : domaines sur leurs teintes opaques, encres sur remplissages, focus, splash et contraste élevé. Les paires couvertes en contraste élevé sont exigées à **7:1** dans [a11y.test.tsx:287](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/test/a11y.test.tsx:287>).

   **Correction :** partager réellement les jetons et composants avec les prototypes, ou contrôler explicitement leurs styles calculés. Exiger à la fois gardes inchangés et recette du rendu. « Vitest vert dans le dépôt » ne valide pas automatiquement une proposition HTML extérieure.

6. **[Majeur] Les références doivent distinguer décision historique, capture ancienne et code actuel.**

   La planche reste une référence d’intention, pas une feuille CSS à réimporter. Son anneau clair utilise encore le cyan vif : [planche-da.html:11](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/audits/2026-08-30-planche-da.html:11>). Celui-ci ne donne que **1,67:1** sur le fond clair actuel ; `globals.css` a depuis un jeton d’anneau distinct.

   La capture **90** montre du Markdown brut. Or le détail d’une décision appelle déjà `CompactMarkdown` dans [BoardConversationCard.tsx:275](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/BoardConversationCard.tsx:275>). Cela justifie une nouvelle recette, pas l’affirmation que le défaut subsiste. En revanche, la synthèse est encore placée après les avis dans ce composant.

   **Correction :** joindre à chaque écran une référence datée, la version du code et trois mentions possibles : « observé sur capture », « présent dans le code », « vérifié au rendu ». Présenter les compteurs historiques du brief comme des mesures datées tant qu’ils ne sont pas recomptés.

7. **[Bloquant] L’accessibilité doit devenir une condition de comparaison, pas rester “possible”.**

   Les tailles utilisateur correspondent à des racines de **14, 16 et 18 px**, selon [accessibilityStore.ts:90](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/stores/accessibilityStore.ts:90>). Le garde typographique précise que son plancher interactif de 14 px concerne la taille par défaut : [typographie.test.ts:68](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/typographie.test.ts:68>). Les rayons sont également en `rem`, donc variables avec cette préférence.

   Les deux réductions de mouvement existent déjà : préférence système et préférence applicative, dans [globals.css:476](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/globals.css:476>). Une animation ne doit pas perdre son information lorsqu’elle s’arrête.

   **Correction :** imposer aux propositions les trois tailles, les deux thèmes, le contraste élevé, la réduction de mouvement système et applicative. Vérifier focus visible et non masqué, retour du focus après fermeture, annonces des changements, et fonctionnement sans survol.

   Pour Hybride, un sous-arbre sombre peut redéfinir des variables héritées du contraste élevé : il faut vérifier cette cascade. Les repères indispensables de sélection et de focus doivent rester discernables à **3:1**, indépendamment de la couture décorative. [Référence W3C](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

8. **[Majeur] 1024 px ne couvre pas le contrat réel de la fenêtre. Les listes longues manquent également.**

   La configuration autorise **800 × 600**, avec une ouverture par défaut à **1200 × 800** : [tauri.conf.json:17](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src-tauri/tauri.conf.json:17>).

   Sur la capture **15**, le pipeline déborde déjà horizontalement. Le code prévoit ce défilement et des colonnes `w-72` dans [PipelineView.tsx:167](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/crm/PipelineView.tsx:167>). Le rendre plus aéré sans stratégie de largeur accentuerait le problème. Sur **86**, plusieurs rendez-vous sont déjà tronqués.

   **Correction :** conserver 1280 et 1024 pour comparer, ajouter une recette à 800 × 600 et préciser la hauteur de chaque viewport. Tester des noms longs, des montants importants et un scénario de plusieurs centaines d’éléments. Vérifier accès au texte complet, filtres, défilement, focus et déplacement des cartes hors écran. Une éventuelle virtualisation doit préserver ces comportements.

9. **[Majeur] Les objectifs par écran sont trop généraux pour garantir l’absence de perte fonctionnelle.**

   Le plan accepté distingue explicitement **agir dans un contexte** et **administrer un domaine** : [plan-simplification-ux.md:17](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/plans/2026-08-27-plan-simplification-ux.md:17>). Il faut conserver les deux parcours.

   **Correction :** ajouter ces critères à la recette de chaque écran :

   | Écran | Critère supplémentaire indispensable |
   |---|---|
   | Accueil, capture 51 | Priorité compréhensible et destination explicite. Les formulations « mutations du chat confirmées » encombrent la lecture ; placer les détails techniques dans leur espace dédié, tout en conservant sources et confirmations utiles. |
   | Tiroir et catalogue | Distinguer retrouver une conversation et choisir une capacité ; conserver les destinations directes et rendre les détails progressivement accessibles. |
   | Contacts et pipeline, capture 15 | Garder accessibles les contacts exclus du pipeline. Préserver le déplacement au clavier, déjà prévu dans le code, et l’accès à la fiche. |
   | Devis et factures, capture 18 | Préserver types, filtres, actions et historique ; distinguer statut d’envoi, paiement et échéance. Tester aussi la création et les erreurs de formulaire. |
   | Projets et tâches, captures 31 et 33 | Conserver liste, colonnes, changements d’état et échéances. « Trois secondes » doit devenir un scénario mesurable, avec ses champs et son point de départ. |
   | Décision, capture 90 | Présenter la synthèse tôt, garder les cinq avis et leurs divergences accessibles ; prévoir réponse partielle, interruption et échec d’un conseiller. |
   | Agenda, capture 86 | Préserver aussi Jour et Liste, visibles dans la capture mais absents de l’objectif résumé ; tester chevauchements et consultation du titre complet. |
   | Paramètres, capture 22 | Préserver les rubriques et fonctions avancées ; distinguer service configuré, clé masquée, clé invalide et service indisponible. |

   Un état vide et une erreur uniquement pour l’accueil et les devis ne suffisent pas à qualifier les huit familles d’écrans.

10. **[Majeur] L’ambition artistique reste trop attachée au serif et au filet multicolore.**

   Une direction plus affirmée est possible sans changer les gardes. Voici six pistes CSS à éprouver :

   | Piste | Réalisation concrète | Risque à maîtriser |
   |---|---|---|
   | **Une couture rare et identifiable** | Pseudo-élément de 3 px sur un seul bord du cadre de travail, avec les accents existants, sans intercepter les clics. Boutons toujours unis. | Un arc-en-ciel sur chaque carte brouillerait les couleurs de domaine et les états actifs. |
   | **Une typographie de registre** | Jakarta pour les titres, Inter pour les lignes ; `font-variant-numeric: tabular-nums` pour montants, dates et compteurs. Hiérarchie par poids et alignement. | Des titres plus grands peuvent évincer l’information utile à petite largeur. |
   | **Des factures organisées en lignes** | Grille commune pour identité, statut, échéance et montant ; séparateurs dans un conteneur au rayon existant. | Une ligne trop dépouillée peut perdre son caractère interactif : maintenir survol et focus explicites. |
   | **Une matière périphérique** | Très léger dégradé de surface ou trame CSS dans les marges ; surfaces de lecture opaques et ombres existantes. | Moiré à DPR 1, surcharge graphique et contraste local. Supprimer la matière en contraste élevé. |
   | **Un mouvement qui indique une relation** | Translation courte à l’ouverture d’un panneau ou déplacement d’un repère décoratif ; durée explicite, sans faire disparaître le texte par opacité. | Gêne vestibulaire et déplacement des cibles. Prévoir un état fixe équivalent. |
   | **Un passage clair/navy sans fondu de lecture** | Basculer ensemble les couples encre/fond ; animer éventuellement un repère périphérique. | L’interpolation des couleurs peut produire des contrastes insuffisants entre deux états pourtant conformes. |

   Les ombres douces et les transitions sont déjà structurées dans [globals.css:385](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/globals.css:385>). Les rayons doivent conserver les valeurs exactes exigées par [rayons.test.ts:68](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/rayons.test.ts:68>).

   Enfin, `spring 300/30` décrit des paramètres de ressort ; « 150 ms » décrit une durée. Le brief doit attribuer ces comportements à des interactions précises.

11. **[Majeur] Windows, Linux et l’impression constituent des recettes distinctes.**

   Les polices embarquées réduisent les variations de famille, sans garantir un rendu identique. Tauri utilise WebView2 sous Windows et WebKit sous macOS et Linux. [Documentation Tauri](https://v2.tauri.app/reference/webview-versions/)

   **Correction écran :** vérifier dans les applications natives les accents français, déliés éventuels du serif, graisses réellement chargées, troncatures, contrôles natifs et filets à DPR 1. Tester Windows avec sa configuration de rendu du texte et Linux avec le moteur réellement livré. Une capture JPEG de 1300 px ne prouve pas cette qualité. Contrôler aussi que la couture de barre de titre conserve les zones de déplacement et les commandes de fenêtre.

   **Correction impression :** distinguer impression de la prévisualisation et PDF métier. Les factures utilisent ReportLab et un thème Python dans [invoice_pdf.py:17](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/invoice_pdf.py:17>) : modifier le CSS ne modifiera pas leur PDF.

   Pour les documents, prévoir pagination, tableaux sur plusieurs pages, polices incorporées, rendu en niveaux de gris et contrôle avec le moteur Apple. Éviter le texte découpé dans un dégradé. « PDF conforme » doit avoir une recette propre ; une belle page de devis ne le démontre pas.

12. **[Majeur] Le coût doit être annoncé par direction, avec un périmètre comparable.**

   Ce ne sont pas huit fichiers : l’inventaire comporte notamment **21 composants dans `prototype`, 19 dans `settings` et 15 dans `ui`**. Le canevas conversationnel fait 2 095 lignes, le formulaire de facture 1 002.

   **Correction :** annoncer une estimation de cadrage pour l’intégration des huit familles, leurs états, les thèmes, les tests et la documentation. Pour un développeur connaissant le dépôt, sans chantier métier supplémentaire :

   | Direction | Fichiers touchés, ordre de grandeur | Effort indicatif |
   |---|---:|---:|
   | Application affinée | 35 à 60 | 10 à 18 jours-personne |
   | Continuité corrigée | 55 à 90 | 18 à 30 jours-personne |
   | Hybride deux mondes | 55 à 95 | 20 à 35 jours-personne |

   Ce sont des **estimations**, pas un devis. Elles incluent les fichiers de validation ; elles excluent une refonte du générateur PDF. Trois variantes de prévisualisation ne signifient pas trois implémentations complètes à maintenir.

13. **[Majeur] Méthode de dépôt : GO après correction du comparateur et du vote.**

   Une page par écran et trois directions en onglets sont utiles. Le côte à côte permanent est trompeur : deux applications à 1280 px nécessitent au moins **2560 px**, avant même les marges du comparateur. Les réduire pour les faire tenir fausse précisément le jugement typographique.

   **Correction proposée :**

   - Comparaison avant/après à l’échelle 1:1 par bascule ; côte à côte lorsque l’espace disponible le permet.
   - Même contenu, même état, même viewport et position de défilement comparable.
   - Référence actuelle datée ; signalement clair lorsqu’un « avant » reste une capture.
   - Choix d’une direction commune pour polices, couleurs, rail, boutons et tiroirs, puis décisions écran par écran. Sinon, huit votes indépendants peuvent recréer plusieurs applications dans une seule.
   - Décision enregistrée avec écran, direction, version et réserve éventuelle. « Plus tard » conserve l’existant.
   - Parcours vérifiables entre les pages, avec les noms déjà décidés et les mêmes confirmations.

   Le seul socle demandé représente déjà **96 configurations nominales** : 8 écrans × 3 directions × 2 thèmes × 2 largeurs, avant les tailles utilisateur et les états. Mieux vaut qualifier d’abord quelques écrans discriminants, puis étendre la direction retenue aux huit.

Les contrastes ci-dessous sont calculés sur les couleurs fournies, sans prélèvement dans les JPEG. Pour chaque canal sRGB normalisé \(c\), la linéarisation vaut \(c/12{,}92\) si \(c \le 0{,}04045\), sinon \(((c+0{,}055)/1{,}055)^{2{,}4}\). Puis \(L=0{,}2126R+0{,}7152G+0{,}0722B\) et le ratio vaut \((L_{\max}+0{,}05)/(L_{\min}+0{,}05)\). [Méthode W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

Les teintes sont composées en sRGB par canal : **30 % teinte + 70 % fond**, avec texte opaque et sans arrondi intermédiaire. Les décisions utilisent le ratio non arrondi. `#A9B8D8` est bien calculé à ta demande ; le texte secondaire sombre actuel est `#B6C7DA`, selon [globals.css:184](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/styles/globals.css:184>).

| Encre et traitement du fond | Papier `#FAFAF7` | Fond actuel `#F3F6FC` | Navy `#0B1226` |
|---|---:|---:|---:|
| `#0891B2`, fond uni | **3,52:1 · Échec** | **3,40:1 · Échec** | 5,05:1 · Passe |
| `#DB2777`, fond uni | **4,40:1 · Échec** | **4,25:1 · Échec** | **4,05:1 · Échec** |
| `#7C3AED`, fond uni | 5,45:1 · Passe | 5,26:1 · Passe | **3,26:1 · Échec** |
| `#E6EDF7`, fond uni | **1,13:1 · Échec** | **1,09:1 · Échec** | 15,79:1 · Passe |
| `#A9B8D8`, fond uni | **1,91:1 · Échec** | **1,84:1 · Échec** | 9,33:1 · Passe |
| `#0E7490`, sur `#DEF4F9` à 30 % du fond indiqué | 4,99:1 · Passe | 4,87:1 · Passe | Non demandé |
| `#92400E`, sur `#FAEFDC` à 30 % du fond indiqué | 6,61:1 · Passe | 6,45:1 · Passe | Non demandé |