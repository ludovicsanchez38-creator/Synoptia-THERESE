# RFC P-110 : un Word reçu par mail, intégré dans un site PHP

Rédigé le 25/09/2026. Proposition S10 de Dr_logic-3D, acceptée par Ludo le 25/09 avec la recommandation du triage : « non en fonctionnalité dédiée : cas d'usage de l'Atelier (mission de changement sur le dépôt du site), à documenter comme exemple ». Aucun code avant la validation de ce document.

Chemins relatifs à `src/backend/app/` et à `src/frontend/src/`, sauf mention contraire.

## 1. Le besoin

Dr_logic-3D, sur Discord (fil du 25/09, 03:35 à 04:29) :

- Les membres de son association lui envoient des documents Word par e-mail.
- Il les intègre à la main dans les modules et les menus d'un site PHP sans framework.
- Le travail tient en trois gestes : récupérer la pièce jointe, transformer le Word en page propre, poser la page et son entrée de menu dans le site. Reste ensuite la mise en ligne.

## 2. Ce qui existe déjà

**Points d'appui :**

- Les deux fournisseurs de messagerie savent télécharger une pièce jointe (`services/email/gmail_provider.py:258-284`, `services/email/imap_smtp_provider.py:847-873`).
- Un Word déposé dans la conversation est lu et enveloppé comme document (`routers/chat.py:298-327`, `:420-426`).
- `nh3` assainit déjà le HTML sur une liste blanche, sans `style` (`services/html_sanitizer.py:5-33`).
- **L'Atelier sait mener une mission de changement sur un dépôt git** :
  - un espace de travail isolé (`services/agents/swarm.py:218-249`) ;
  - `write_file`, borné au dépôt et qui refuse les fichiers sensibles (`services/agents/tools.py:562-587`, `:730`) ;
  - un diff relu, puis une fusion faite par l'utilisateur (`routers/agents.py:847-895`).

  Pour poser une page et un menu, `write_file` suffit : aucune commande n'est nécessaire.
- Le préréglage MCP Filesystem écrit dans le dossier de travail (`routers/mcp.py:311-319`).

**Manques :**

- **La pièce jointe n'est pas atteignable.** Aucune route n'expose `get_attachment`, et l'interface n'affiche qu'un trombone (`components/email/EmailList.tsx:427-428`). Chez Gmail, le nom du fichier est perdu au téléchargement (`gmail_provider.py:279`). C'est le volet 2 de BUG-148, toujours ouvert.
- **Le Word est lu à plat.** `_extract_docx` ne garde que le texte des paragraphes (`services/file_parser.py:206-221`), sans titres, listes, tableaux, liens ni images. On ne peut pas en faire une page.
- **L'Atelier suppose qu'il travaille sur THÉRÈSE** :
  - son message dit « Le code source de THÉRÈSE n'est pas disponible » (`services/agents/tools.py:552-555`) ;
  - un seul dépôt est configurable (`agent_source_path`, `routers/agents.py:72-110`) ;
  - la recherche est limitée à des motifs sans `*.php` (`tools.py:57-71`) ;
  - la pile annoncée ne cite pas PHP (`services/agents/profiles.py:134-140`) ;
  - la branche `main` est supposée pour le diff et la fusion (`services/agents/git_service.py:282-334`, `routers/agents.py:870-874`).

  De plus, un site sans framework n'est souvent pas sous git.
- **Commandes** : elles sont refusées hors macOS en V1 (B-1153), et Dr_logic travaille sous Windows 10. Sans effet ici : ce cas n'en demande pas.
- **La voie MCP générique ne convient pas.** Chaque écriture passe par une carte qui montre le fichier entier en argument brut, sans différence (`components/chat/ToolConfirmationCard.tsx:85-102`). Et la chaîne s'arrête à la première carte (`routers/chat.py:3405-3414`).
- **Mise en ligne** : aucun connecteur SFTP. `ssh` et `scp` sont refusés comme commande de serveur MCP (`services/mcp_service.py:28-32`).

## 3. Quatre options

| | A. Mission Atelier et brique « Word vers HTML » | B. Fonction dédiée « publier une page » | C. Publication directe par SFTP | D. MCP Filesystem tel quel |
|---|---|---|---|---|
| Idée | Conversion déterministe du Word en fragment HTML assaini. La mission Atelier pose la page et le menu sur une copie git du site. L'utilisateur relit le diff, fusionne et met en ligne avec son outil habituel | Un profil de site (gabarit de page, fichier de menu) rempli par THÉRÈSE, avec aperçu et écriture dans une copie locale | THÉRÈSE compare et dépose les fichiers sur le serveur | Le modèle écrit par `filesystem__write_file` |
| Pour | Conforme au triage ; le diff relu sert de garde-fou ; la brique sert ailleurs (Word vers e-mail, vers note) | Parcours sur mesure, sans git | Un geste de moins | Existe déjà |
| Contre | Git requis ; trois ajustements de l'Atelier | Une fonction dédiée à un seul cas, refusée par le triage | Identifiants d'hébergement à garder ; écriture sur un site en production ; aucun retour arrière | Aucune différence à relire ; fichier réécrit en entier ; chaîne coupée |
| Effort | Moyen | Moyen à large | Large | Nul, risque élevé |

## 4. Recommandation : A, en deux lots

### Premier lot : convertir, puis confier à l'Atelier

- **Brique « Word vers HTML »** : un service déterministe, sans LLM, pour que le texte des membres passe tel quel.
  - Il produit titres, paragraphes, listes, tableaux, liens, gras et italique, puis passe le tout par `nh3`.
  - Les images sont extraites en fichiers (PNG, JPEG et GIF seulement), avec des noms normalisés.
  - `.doc` et `.docm` sont refusés.
  - Le résultat est un dossier téléchargeable (fragment `.html` et images), avec un aperçu dans la conversation.
- **Atelier, trois ajustements** :
  - `*.php` et `*.inc` ajoutés aux motifs de recherche ;
  - la branche de base lue dans le dépôt au lieu d'un `main` supposé, sans réintroduire le repli inventé que B-027 a retiré ;
  - des libellés qui ne parlent plus du « code source de THÉRÈSE » quand le dépôt est un autre projet.
- **Guide « Intégrer un document dans un site »** :
  1. Mettre une copie du site sous git, une seule fois (`git init`).
  2. Déposer le dossier converti dans la copie.
  3. Décrire la mission, par exemple : « crée `pages/assemblee-2026.php` sur le modèle de `pages/modele.php`, ajoute l'entrée dans `inc/menu.php` ».
  4. Relire le diff, fusionner, mettre en ligne.

### Deuxième lot, sur demande

- **La pièce jointe dans THÉRÈSE** : un bouton « Enregistrer dans les fichiers » sur la pièce jointe d'un e-mail. Il télécharge le fichier vers les fichiers d'un projet, avec les mêmes contrôles d'extension et de taille qu'à l'upload (`routers/files.py:427-500`). Le nom de fichier Gmail est repris des métadonnées. Ce lot ferme aussi le volet 2 de BUG-148.
- **Détection des données personnelles** avant publication (adresses, téléphones) : un signalement, pas un blocage.

### Hors périmètre

- C (SFTP), et toute écriture sur un serveur en ligne.

## 5. Décisions attendues de Ludo

1. **Git** : le site de Dr_logic est-il sous git ? Sinon, le guide lui demande-t-il de l'y mettre, ou faut-il une autre voie ?
2. **La conversion** : nouvelle dépendance (mammoth, licence BSD), ou conversion maison sur python-docx (plus longue, et les listes numérotées y sont difficiles) ?
3. **Plusieurs dépôts** : l'Atelier doit-il viser THÉRÈSE et le site sans qu'on reconfigure le chemin à chaque fois ? Recommandation : hors lot 1.
4. **Le lot 2** (pièce jointe) entre-t-il dans le prochain cycle, puisqu'il ferme une dette ouverte ?

## 6. Livraison proposée

1. Design court et revue adverse du design.
2. Service de conversion et ses fichiers témoins (TDD).
3. Aperçu et téléchargement dans la conversation.
4. Trois ajustements de l'Atelier.
5. Guide et recette sur une copie de site PHP de démonstration, sous Windows.

## 7. Plan de tests

- **Fidélité** : un Word témoin (titres sur trois niveaux, liste numérotée, tableau à cellules fusionnées, lien, image) donne la structure attendue, et le texte sort identique au caractère près.
- **Sécurité du fragment** : un Word qui contient `<?php system('id'); ?>`, `<script>`, un lien `javascript:`, un champ ou un objet OLE produit un fragment sans `<?`, sans script et sans lien dangereux actif.
- **Archives piégées** : un `.docx` bombe de décompression, une entrée de zip en `../` ou une image EMF donnent un refus ou une omission annoncée ; rien n'est écrit hors du dossier de sortie.
- **Atelier** :
  - un dépôt sur `master` se relit et se fusionne ;
  - un dossier sans git reçoit un message qui explique quoi faire ;
  - la recherche trouve un `.php`.
- **Lot 2** : pièces jointes Gmail et IMAP, nom conservé. Un `.exe` renommé en `.docx` est refusé, à l'extension comme au contenu.
- **Sabotage** ciblé par fonction (assainissement, refus de `<?`), puis revue adverse du diff.

## 8. Risques

- **Sécurité du site** : un Word de membre est un contenu tiers. Sans assainissement, il porte du script (XSS). Posé dans un `.php`, un `<?php` serait exécuté par le serveur. D'où la sortie échappée, `nh3` et le test dédié.
- **Injection de consigne** : le texte du Word arrive au modèle de l'Atelier et peut contenir des consignes. La mission n'écrit que dans l'espace isolé, et rien n'atteint le site sans diff relu.
- **Perte de données** : une mission qui réécrit `menu.php` peut effacer des entrées. Le diff relu et git permettent le retour arrière.
- **RGPD** : les documents d'association contiennent des données de membres qui finissent en ligne. La responsabilité reste à l'association ; THÉRÈSE peut seulement signaler (lot 2).
- **Souveraineté** : la conversion est locale. Seule la mission Atelier envoie le contenu au fournisseur choisi pour l'Atelier, sous la finalité `documents`.

## Annexe : appuis dans le code

- Origine : `.app-loop/proposals.json`, P-110 (triage : « cas d'usage de l'Atelier »).
- Messagerie : `services/email/gmail_provider.py:101-111` (métadonnées des pièces jointes seulement sur demande), `:340-359` (extraction des noms) ; `routers/email.py:106-107` (drapeau et compte, rien d'autre).
- Atelier : `services/agents/git_service.py:205-215` (branche courante sans repli inventé, B-027) ; `docs/plans/2026-09-24-b1153-bac-a-sable-commandes-agents.md` (commandes refusées hors macOS en V1).
- MCP : `services/mcp_service.py:23-26` (commandes autorisées pour lancer un serveur).
