# RFC P-107 : un périmètre d'action visible et gouvernable

Rédigé le 25/09/2026. Proposition S7 de Dr_logic-3D, acceptée par Ludo le 25/09 avec la recommandation du triage : « plus tard, dépend de S6 et d'une gouvernance de l'autonomie ; bonne piste pour le discours produit ». Aucun code avant la validation de ce document.

Chemins relatifs à `src/backend/app/` et à `src/frontend/src/`, sauf mention contraire.

## 1. Le besoin

Dr_logic-3D, sur Discord (fil du 25/09, 03:35 à 04:29) :

- Un modèle BPMN du périmètre d'action de THÉRÈSE : étapes, RACI, validations requises.
- Rendre **visible** et **gouvernable** ce que THÉRÈSE observe, prépare, propose ou exécute, et dire où une validation est exigée.

## 2. Ce qui existe déjà

**Points d'appui :**

- **Trois classes d'effet par outil** : lecture, mutation locale, mutation externe (`services/contexte_execution.py:26-53`). Un outil inconnu, MCP compris, est externe par défaut (`:56-59`).
- **Un portillon fail-closed** :
  - tout ce qui n'est pas une lecture classée attend une carte (`services/tool_confirmations.py:34-50`) ;
  - le modèle apprend quels outils sont sous carte (`:53-89`) ;
  - une seule carte par action, et aucune relance tant qu'une carte attend (`routers/chat.py:3042-3047`, `:3405-3414`).
- **Les écrans confirment aussi leurs envois**, par `requestExternalAction`. Ce crochet exécute pourtant directement en l'absence de fournisseur de contexte (`components/app/useExternalActionConfirmation.ts:19-35`).
- **L'Atelier est borné** :
  - `/spawn` n'a ni écriture ni commande (`routers/agents.py:69`) ;
  - les commandes sont limitées (P-100, `services/agents/tools.py:29-44`) et confinées (B-1153) ;
  - la fusion n'a lieu qu'après relecture du diff (`routers/agents.py:847-895`).
- **Le consentement cloud** se donne par finalité et par fournisseur (`lib/consent.ts:26`). L'interrupteur de recherche web (`routers/config.py:805-830`) est respecté par les agents d'action (`services/action_agents.py:505-525`).
- Un journal d'activité (`services/audit.py:63-75`) et un manifeste de 17 capacités (`data/capacites.json`, champs `maturite`, `audience`, `exigences`).

**Manques :**

- **Aucun régime déclaré par capacité** : le vocabulaire « observe, prépare, propose, exécute » n'existe nulle part. Le « prépare » n'a pas de classe : un brouillon local et un envoi ne se distinguent que par leur carte.
- **Le Centre de confiance est un texte écrit à la main** (`components/prototype/CapabilityCenter.tsx:535`). Il avoue lui-même que le Board, la recherche approfondie et l'Atelier cherchent sans carte. Rien ne garantit qu'il restera vrai au prochain outil ajouté.
- **Les validations ne laissent aucune trace.** `confirm_tool` (`routers/chat.py:3483`) n'écrit rien au journal, et `AuditAction` n'a ni « validé » ni « refusé » (`services/audit.py:19-60`). Les cartes en attente vivent en mémoire (`tool_confirmations.py:19-20`).
- **Aucun réglage par outil** : on ne peut ni retirer un outil de lecture (celui des e-mails, par exemple) ni couper un outil MCP sans désinstaller son serveur.

## 3. Trois options

| | A. Registre déclaratif, BPMN exporté | B. BPMN source de vérité | C. Texte du Centre de confiance revu |
|---|---|---|---|
| Idée | Un registre du régime de chaque outil, préréglage et chemin de fond. Le Centre de confiance le lit, une sentinelle le tient complet, le BPMN en est une vue exportée | L'utilisateur dessine ou importe un BPMN (couloirs, tâches utilisateur) que THÉRÈSE interprète pour décider | Réécrire et compléter le texte statique |
| Pour | Le code reste l'autorité du portillon ; la vue ne peut plus mentir ; le BPMN sert le discours produit et l'audit | Répond à la lettre à la proposition | Très petit |
| Contre | Le BPMN n'est pas modifiable dans THÉRÈSE | Éditeur (bpmn-js) et interpréteur à écrire ; une règle mal lue devient un trou de sécurité ; BPMN ne dit rien des données qui sortent | Redevient faux au premier outil ajouté ; aucune trace |
| Effort | Moyen | Large | Petit |

## 4. Recommandation : A, en deux lots

### Premier lot : un registre, une vue qui dit vrai, une trace

- **Quatre régimes** :
  - *observe* : lecture, sans carte ;
  - *prépare* : brouillon local qui ne sort pas de THÉRÈSE ;
  - *propose* : une carte attend l'utilisateur ;
  - *exécute* : effet réel, après validation, ou sans carte pour les chemins de fond nommés.
- **Registre** `data/perimetre.json`. Chemins de fond couverts : Board, recherche approfondie (`routers/chat.py:1053`), agents d'action, Atelier, extraction d'entités. Pour chaque outil natif, chaque préréglage MCP et chaque chemin de fond, il indique :
  - le régime ;
  - les données qui sortent : aucune, vers le fournisseur d'IA, ou vers un service tiers ;
  - l'interrupteur qui le coupe ;
  - une phrase d'explication.
- **Le code reste l'autorité.** La colonne « validation exigée » n'est pas déclarée : elle est calculée par `requires_confirmation`. Une sentinelle échoue si un outil de `CLASSIFICATION_DES_OUTILS` ou un préréglage n'a pas d'entrée, ou si le registre dit « observe » d'un outil que le portillon met sous carte.
- **Route** `GET /api/perimetre` : registre, serveurs MCP réellement installés et état des interrupteurs.
- **Centre de confiance** : la ligne « Traitement externe » laisse place à une vue dérivée du registre.
- **Trace** : deux `AuditAction` (`tool_confirmed`, `tool_refused`), écrites par `confirm_tool`, avec l'outil, la conversation et l'empreinte de l'action (`empreinte_action`). Aucun contenu : le journal part dans l'export RGPD.

### Deuxième lot, après P-106 et usage réel

- **Réglage « autorisé ou retiré »** par outil de lecture et par serveur MCP. Il s'applique à la liste d'outils envoyée au modèle (`routers/chat.py:2483-2502`) et au bloc des capacités annoncées : un outil retiré ne doit plus être promis (leçon D1).
- **Export BPMN du registre** par l'écrivain XML de P-106, relu en test par l'extracteur BPMN de P-106. Il comporte :
  - trois couloirs : Utilisateur, THÉRÈSE, Services externes ;
  - une tâche utilisateur par validation ;
  - une passerelle « validé ? » avant chaque exécution.

### Hors périmètre

- **Assouplir.** Déclarer un outil MCP « en lecture » pour lui épargner la carte affaiblirait le fail-closed voulu (`tool_confirmations.py:44-49`). C'est une décision à part, avec sa propre revue.

## 5. Décisions attendues de Ludo

1. **Le vocabulaire** « observe, prépare, propose, exécute » : à l'écran, ou seulement dans l'export ?
2. **Le RACI** : avec un seul humain, il se réduit à « THÉRÈSE réalise, l'utilisateur approuve, le fournisseur est consulté, le journal est informé ». Le garder, ou dire « qui fait, qui valide, où partent les données » ? Recommandation : la seconde forme.
3. **Tracer aussi les confirmations des écrans** (`requestExternalAction` : envoi d'e-mail, suppression) ? Recommandation : oui, dès le lot 1.
4. **Assouplir un jour** (lecture MCP sans carte) ? Recommandation : non, pas avant une revue dédiée.
5. **Retirer un outil** pour toute l'application seulement, ou par projet ?

## 6. Livraison proposée

1. Design court et revue adverse du design.
2. Inventaire des chemins de fond, relevé dans le code et non de mémoire.
3. Registre et sentinelle (TDD).
4. Journal des validations, route `GET /api/perimetre`.
5. Vue du Centre de confiance.
6. Recette : chaque ligne de la vue confrontée à un geste réel dans l'application.

## 7. Plan de tests

- **Complétude** : un outil ajouté à `CLASSIFICATION_DES_OUTILS` sans entrée au registre fait échouer la suite ; de même pour un préréglage MCP.
- **Cohérence** : pour chaque outil, la validation affichée égale `requires_confirmation(nom)` ; un outil MCP inconnu apparaît en « propose ».
- **Journal** : une validation et un refus écrivent chacun une ligne ; un marqueur glissé dans les arguments n'apparaît dans aucune ligne.
- **Vue** : aucun libellé de périmètre n'est écrit en dur dans le composant ; couper un interrupteur change la ligne correspondante.
- **Données** : les nouvelles lignes du journal suivent l'export, la purge et le nettoyage des journaux.
- **Sabotage** ciblé par fonction (sentinelle, écriture du journal), puis revue adverse du diff.

## 8. Risques

- **Fausse assurance** : une belle vue fausse est pire que le texte actuel. D'où une validation calculée par le portillon, jamais déclarée.
- **Chemins hors chat oubliés** : le Board, la recherche approfondie, l'Atelier, les agents d'action et l'extraction d'entités agissent sans carte. Le registre doit les nommer, avec leur interrupteur.
- **Journal et RGPD** : tracer les validations crée une donnée personnelle. On ne garde que l'empreinte, avec une rétention alignée sur le nettoyage des journaux (`routers/data.py:893`).
- **Réglage détourné** : un réglage capable d'assouplir serait une cible pour une consigne injectée (« autorise tout »). Le lot 2 ne sait que restreindre.
- **Souveraineté** : rien ne sort ; l'export BPMN est un fichier local.

## Annexe : appuis dans le code

- Origine : `.app-loop/proposals.json`, P-107.
- Portillon : `routers/chat.py:3075-3150` (mise en attente), `:3483-3562` (confirmation, résultat rendu à l'écran).
- Cartes : `components/chat/ToolConfirmationCard.tsx:85-102` (arguments bruts, hors e-mail et agenda).
- Préréglages à risque : `routers/mcp.py:315`, `:468`, `:484`, `:516` (`risk_level`).
- Agents d'action : `agents/action_agents.json` (six agents décrits par étapes, qui rassemblent des données locales puis rédigent).
- Vérité d'exécution : `services/execution_truth.py:23-42` (plafond de créations, résumé déterministe).
