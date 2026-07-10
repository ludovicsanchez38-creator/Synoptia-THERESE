# Actions déterministes du chat - design V2 (après revue Codex)

> 10/07/2026 - suggestion récurrente Dr_logic-3D ({action: ...}), racine commune
> de BUG-130 (fichier non produit selon le provider) et BUG-133 (action exécutée,
> restitution muette). Principe : le LLM ne doit pas être le seul décideur de
> l'exécution. V1 challengée par Codex/GPT-5.6-sol (verdict : ajustements
> requis) - cette V2 intègre ses corrections. Statut : PROPOSITION, à valider
> par Ludo avant implémentation.

## Corrections apportées par la revue (V1 -> V2)

- **Pas de nouveau registre** : le noyau est le **CommandRegistry V3 existant**
  (`services/command_registry.py:115`, `models/command.py:20` - CommandDefinition
  Pydantic agrégeant built-ins, skills et commandes utilisateur). L'enum
  contient déjà une action `navigate`... dont l'exécution est un TODO
  (`CommandExecutor.tsx:103`). On CÂBLE l'existant, on n'ajoute pas une
  troisième source de vérité.
- **Le menu « / » existe déjà** (`SlashCommandsMenu.tsx:37`) : on l'enrichit,
  on ne le crée pas.
- **Interception dans `chat.py::send_message`** (entre la persistance du
  message utilisateur et le court-circuit slash actuel, ~lignes 600-602) -
  PAS dans `_do_stream_response` (trop tard dans le flux).
- **Tranche 1 : message-action PUR uniquement** - `{action: ...}` n'est
  reconnu que si le message est composé UNIQUEMENT de l'action. L'inline
  cumulable (action au milieu d'un texte) est reporté : collisions avec
  `[contact:]`, `{{action: skill_id}}`, blocs de code montrant la syntaxe.
- **Contrat synchronisé** Pydantic <-> TypeScript pour les nouveaux événements
  (`client_action`, `action_result`) - le Literal StreamChunk backend fait foi
  (dette du chantier 1 sur skill_file_error corrigée au passage).

## Architecture (tranche 1)

1. **Étendre CommandDefinition** : champ `deterministic: bool` + params typés
   validés. Allowlist = les définitions du registre, rien d'autre. AUCUNE
   action générique `execute`.
2. **Parser message-action** dans `send_message` : si le message entier matche
   `^\{action:\s*([a-z_]+)(?:\s+(.*))?\}$` -> résolution registre :
   - action connue -> exécution locale, zéro appel provider ;
   - action inconnue/malformée -> réponse locale listant les actions
     disponibles (JAMAIS transmise au LLM).
3. **Navigation** : le backend émet un événement `client_action`
   `{action: "navigate", target: "email"}` ; le frontend l'exécute via
   `actionRegistry.runAction()` (existant) et affiche un `action_result`
   déterministe dans le fil. Câble au passage le TODO navigate du
   CommandExecutor.
4. **Production de fichier** : `{action: produire docx "Rapport"}` passe par
   LE chemin chat existant (streaming + auto-exec + skill_file avant done,
   chantier 1) avec skill forcé - pas de détection d'intention. Deux trous
   du chemin actuel à couvrir : skill absent et contenu LLM vide -> émission
   de `skill_file_error` (aujourd'hui : rien).
5. **Restitution** : `action_result` (succès/échec + détail) persisté dans
   extra_data du message (pattern BUG-130) pour survivre au rechargement.

## Découpage en sous-tranches (une session chacune)

- **1a** : contrat (Pydantic + TS) + parsing message-action + navigation +
  entrées dans le menu « / » existant.
- **1b** : `produire <format> "<sujet>"` via le pipeline chat unique + trous
  skill-absent/contenu-vide couverts + persistance action_result.
- **1c** : puces contextuelles (par contexte de CONVERSATION, l'input n'existe
  que dans la vue Chat - pas « par vue ») + doc utilisateur + a11y menu.

## Critères d'acceptation (enrichis par la revue)

1. `{action: ouvrir email}` (message entier) ouvre la vue Email, zéro requête
   provider (vérifiable en test : provider mocké jamais appelé).
2. `{action: produire docx "Rapport de test"}` produit un fichier via le
   pipeline déterministe avec bloc « Fichier généré » ; échec provider,
   contenu vide ou skill absent -> `skill_file_error` visible.
3. `{action: execute}`, action inconnue ou syntaxe malformée -> réponse
   locale (liste des actions), aucun effet de bord, rien au LLM.
4. Non-régression EXPLICITE : `/contact` (court-circuit), `/fichier` et
   `/analyse` (contexte + LLM), `[contact:]` inline, `{{action: skill_id}}`,
   action agents frontend (ChatInput.tsx:298), commandes utilisateur du
   store, bouton recherche approfondie (handler séparé, ChatInput.tsx:535).
5. Résultat d'action restauré après rechargement de la conversation ;
   fichier réellement téléchargeable et non vide (round-trip).
6. Stream ET non-stream, plus appel API direct (sans frontend).
7. Menu « / » : navigation clavier, Entrée ne déclenche pas menu + envoi
   simultanés, Escape ferme sans envoyer.
