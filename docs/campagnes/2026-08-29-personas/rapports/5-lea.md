# Léa Martin — le fichier existe bel et bien, mais rien dans le chat ne me le donne : j'ai un message qui m'annonce un bouton de téléchargement qui n'est pas là.

## Ce que j'ai fait

8 h 40. Je dicte mes trois créneaux en une phrase : « lundi 10h visite chantier Martin, mercredi 14h rendez-vous fournisseur, vendredi 16h rendu client ». **136 secondes** de réflexion, et la réponse est juste : lundi 31 août, mercredi 2 septembre, vendredi 4 septembre, les trois en attente de ma confirmation. Rien n'a été créé dans mon dos. Bon point, je n'ai pas eu à répéter.

Je demande la suite : « fais-moi le fichier Excel de la semaine, ma cliente doit pouvoir l'ouvrir ». **77 secondes.** La réponse est nette :

> « Le fichier Excel **Planning de la Semaine_dbe098bc.xlsx** a été généré avec succès. […] Votre cliente peut l'ouvrir directement via **l'interface de téléchargement affichée**. Aucun lien n'est fourni, car le fichier est disponible dans le cadre de l'application. »

Et là je cherche. Il n'y a rien à chercher. Pas de prose bizarre, pas de bloc de code, pas de bouton : **rien du tout sous le message**. Le flux ne contient aucun événement `skill_file` (source API : les seuls types reçus sont `generation`, `status`, `text`, `tool_result`, `done`), donc la carte « Fichier généré » de `MessageBubble.tsx:560` n'a jamais de quoi s'afficher. À ce moment-là, il est 8 h 46 et une assistante pressée ouvre Excel. J'ai facturé une demi-heure pour un message qui me dit d'aller cliquer sur quelque chose qui n'existe pas.

Je suis allée chercher le fichier autrement, en lisant le flux brut et en devinant son identifiant dans le nom : `GET /api/skills/download/dbe098bc` → **HTTP 200, 5 356 octets, vrai `.xlsx`** (`Microsoft Excel 2007+`), enregistré dans mes livrables. Il contient bien les en-têtes Jour / Heure / Événement et mes trois créneaux (Lundi 10h Visite chantier Martin, Mercredi 14h Rendez-vous fournisseur, Vendredi 16h Rendu client). Il n'a pas les lignes mardi et jeudi que j'avais demandées, et il s'appelle « Tableau » à l'intérieur : ça, c'est du `limite_modele_local`, je m'en accommode. **Mais ce geste-là n'est pas un geste d'utilisatrice.** Dans l'app, je n'avais aucun moyen d'y arriver.

Le lendemain, nouvelle conversation : « retrouve le planning Excel d'hier ». **80 secondes.** Elle lance `search_files`, qui répond `{"found": false, "total": 0}`, et me conseille « l'atelier Documents » ou « le sélecteur de projet ». Son propre fichier de la veille, qu'elle a écrit elle-même dans `data-lea/outputs/`, elle ne le retrouve pas.

Dernier essai, pour comprendre : la même demande avec la compétence explicite (`skill_id: "xlsx-pro"`, ce que fait un prompt suggéré de l'écran d'accueil). **87 secondes**, et cette fois **le chunk `skill_file` arrive** et `extra_data` est bien peuplé en base. Donc la mécanique de carte marche — mais pas sur le chemin que j'ai pris en écrivant ma phrase.

Total modèle : 6 min 20 sur quatre échanges. Le décrochage réel s'est joué à la minute 6, pas sur la lenteur.

## Dette connue rencontrée

| Dette | Je l'ai vue | Une ligne de preuve |
|---|---|---|
| 501 à l'envoi de facture | non | jamais approché la facturation |
| TVA à 20 % par défaut | non | aucun document commercial dans mon parcours |
| Notification après l'échéance | non | pas d'échéance dans mon usage |
| Pas de chemin pour un 2e calendrier | non | une seule destination proposée (`calendar_name: "Mon calendrier"`), je ne l'ai pas cherchée |
| Cloison absente | non | une seule cliente, rien à cloisonner |
| Pas d'écran « cabinet » | non | hors de mon métier |

## Correctifs tenus (0.54 / 0.55)

- **Trois rendez-vous dictés en une phrase = trois créneaux justes**, aux bonnes dates calendaires (31/08, 02/09, 04/09), chacun en `confirmation_required` : rien n'a été écrit sans mon accord (source API, flux msg1).
- **Le chemin compétence explicite est propre de bout en bout** : chunk `skill_file` émis avant `done`, puis persisté en `extra_data: {"skill_files": [...]}` sur le message assistant (source API, conversation `f0f37532`). Rechargée demain, cette carte-là revient.
- **Le téléchargement par identifiant survit au cache** : `/api/skills/download/dbe098bc` (identifiant court) a rendu le fichier via le repli disque de `src/backend/app/routers/skills.py:227`, avec le bon type MIME xlsx.
- **Le fichier produit est un vrai classeur**, ouvrable par ma cliente sans bidouille (OOXML valide, chaînes en clair, 5 356 octets).
- **Les deux boutons de la carte sont des actions, pas des vues** : « Télécharger » et « Afficher dans le dossier » (`src/frontend/src/components/chat/MessageBubble.tsx:584` et `:593`) — rien à redire côté libellés.

## Findings

### 1. Un fichier créé par l'outil `generate_document` n'a jamais de carte, ni en direct ni au rechargement — bloquant

Le tour a bien produit le fichier (source API, flux msg2 : `tool_result` = `[generate_document] OK (104ms): Document XLSX généré : Planning de la Semaine_dbe098bc.xlsx`) et le disque le confirme (log serveur : `Generated XLSX (fallback): .../outputs/Planning de la Semaine_dbe098bc.xlsx (5356 bytes)`). Mais **aucun chunk `skill_file` n'est émis**, et `GET /api/chat/conversations/f889da3d-.../messages` rend `extra_data: null` sur le message assistant. Le collecteur par tour (`drain_generated_files()`, `src/backend/app/routers/chat.py:2592`) repart vide alors que l'outil a bien appelé `record_generated_file` (`src/backend/app/services/workspace_tools.py:770`), une fonction dont le commentaire dit lui-même « no-op hors collecte » : elle a écrit dans le vide. Contre-épreuve dans la même session : la même demande avec `skill_id` explicite émet le chunk ET remplit `extra_data`. Le test unitaire de la mécanique (`tests/test_chat_skill_file_stream.py:139`) appelle `record_generated_file` puis `drain_generated_files` dans le même contexte : il est vert et ne voit rien.
**Pourquoi ça compte pour moi** : c'est exactement mon geste, et c'est mon livrable. Le fichier existe, je ne peux pas le joindre à un mail.

### 2. Le chemin outil n'a ni carte ni message d'erreur — à la place, l'app fait promettre au modèle un bouton qui n'existe pas — majeur

Quand une génération par *compétence* échoue, il y a un filet visible : `_skill_file_error_event` (`src/backend/app/routers/chat.py:2580` et suivants) et une notification « Fichier non généré » côté interface (`ChatInput.tsx:705`). Le chemin *outil* n'a rien de tel : ni carte, ni erreur, ni log d'alerte. Pire, la valeur de retour de l'outil injecte une promesse dans le contexte du modèle : « L'utilisateur peut l'enregistrer via **la carte affichée sous ce message** - ne fournis aucun lien » (`src/backend/app/services/workspace_tools.py:783-786`). Le modèle a obéi au mot près et m'a écrit « via l'interface de téléchargement affichée. Aucun lien n'est fourni ».
**Pourquoi ça compte pour moi** : un silence, je le repère et je recommence. Une affirmation fausse, je la crois, je cherche pendant trois minutes, puis je doute de moi.

### 3. Le seul chemin qui produit une carte est inatteignable en tapant sa demande — majeur

`resolve_skill_from_message` ne rend un `skill_id` que sur trois entrées : un identifiant explicite, la syntaxe `{{action: skill_id}}`, ou rien. La détection par mots-clés a été retirée (`src/backend/app/services/skills/intent_detector.py:148-154`, « SUPPRIMÉ (BUG-137) »), alors même que la table `SKILL_PATTERNS` juste au-dessus contient toujours le motif `\b(?:excel|xlsx|tableur…)\b` → `xlsx-pro`. Côté interface, `skill_id` n'est posé que par les prompts suggérés (`ChatInput.tsx:626`, `pendingSkillId`, commentaire « si provient des guided prompts ») : dans une conversation en cours, il n'existe aucun sélecteur de compétence. Donc écrire « fais-moi le fichier Excel » ne peut emprunter que le chemin outil, celui du finding 1. La seule barre oblique qui parle de fichiers, `/fichier <chemin>`, sert à faire LIRE un fichier existant (`FILE_COMMAND_PATTERN`, `src/backend/app/routers/chat.py:189-192`) : elle n'en produit aucun.
**Pourquoi ça compte pour moi** : je parle à Thérèse, je ne connais ni `{{action: xlsx-pro}}` ni la différence entre un outil et une compétence. Le chemin qui marche est celui que je ne prends pas.

### 4. Un fichier produit par Thérèse est invisible à la recherche de Thérèse le lendemain — majeur

Nouvelle conversation, « retrouve le planning Excel d'hier » : elle appelle `search_files`, qui rend `{"found": false, "total": 0, "affiches": 0, "documents": []}` (source API, flux msg3). Confirmé hors chat : `GET /api/files/` rend `[]`. Les sorties de compétences sont écrites dans `Path(settings.data_dir) / "outputs"` (`src/backend/app/services/skills/registry.py:32`) et ne sont jamais versées à l'index de fichiers ; seul l'identifiant, gardé sur le message d'origine, permet d'y revenir — et sur mon tour, ce message n'a rien gardé (finding 1). Sa réponse me renvoie vers « l'atelier Documents » et le « sélecteur de projet », deux endroits où le fichier n'est pas.
**Pourquoi ça compte pour moi** : mon mandat, c'est de le retrouver le lendemain. Un livrable que l'app a écrit et que l'app ne sait plus trouver, c'est un livrable perdu.

## Ai-je abandonné ?

**Oui.** Ligne rouge franchie à la minute 6 : le message m'annonçait un bouton de téléchargement, il n'y avait rien sous le message, et je n'avais aucun fichier à joindre au mail de ma cliente. J'ai récupéré le `.xlsx` ensuite, mais en lisant le flux brut de l'API et en devinant l'identifiant dans le nom du fichier — pas un geste qu'une assistante peut faire. Dans l'app, à 8 h 46, j'ouvrais Excel.
