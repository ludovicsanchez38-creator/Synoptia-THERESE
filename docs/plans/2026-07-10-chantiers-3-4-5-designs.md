# Designs chantiers 3-4-5 - V2 après revue Codex (programme suggestions 10/07)

> Statut : PROPOSITIONS V2 - revue Codex passée (verdict V1 : « aucun des
> trois validable tel quel, le 5 le plus proche du GO »), tous ses ajustements
> intégrés ci-dessous. À valider par Ludo avant implémentation.

## Chantier 5 - ExportProfile DOCX (le plus mûr - effort M)

- Un seul profil global actif, **uniquement pour les deux exports
  déterministes** (Atelier + conversations, `markdown_docx.py`) - les DOCX du
  chat (`docx-pro`) restent sur leur pipeline, annoncé clairement.
- Schéma **Pydantic versionné, strict et borné** (couleurs, langue - défaut
  fr-FR déjà en place, tailles, marges, longueurs police/footer). Défauts =
  charte actuelle, y compris `_style_title` (hero H1) et la couleur H2
  DISTINCTE (oubli de la V1). Champ marges = nouveau helper.
- Fichier JSON dans le data dir, **écriture atomique**, import par CONTENU
  (taille bornée, jamais un chemin arbitraire), endpoint
  `/config/export-profile` (`/config/export` existe déjà). Ajout à
  l'**allowlist du backup** (data.py:593). Fichier corrompu -> repli défauts +
  notification UI (pas juste un log). Avertir qu'une police non installée
  chez le destinataire sera substituée par Word.
- V1 SANS : logo, en-tête, template Word, découverte de polices, PPTX/XLSX.
- Tests : assertions sémantiques sur DOCX rouvert (Normal, Title, H1-H4,
  couleur H2, langue, footer, 4 marges), fichier absent/corrompu/version
  inconnue, round-trip import/export/reset, backup/restore, les 2 endpoints.

## Chantier 4 - Variables V1 (effort M/L)

- **Résolution canonique BACKEND** (la V1 frontend était impossible : les
  actions/slash/directives sont parsées côté backend). Ordre strict dans
  send_message : classification de TOUTES les syntaxes déterministes sur le
  message BRUT (action, slash, directives inline) -> substitution {nom}
  UNIQUEMENT dans la partie destinée au LLM -> check_prompt_safety.
  **Une valeur de variable ne peut JAMAIS fabriquer une action, une
  slash-command ou une directive** (zéro effet de bord, testé).
- Frontend : **endpoint de prévisualisation** (le même service, sans effet de
  bord) - l'aperçu montre exactement le payload qui deviendra bulle et
  historique ; variables inconnues -> confirmation explicite « envoyer quand
  même ». Périmètre V1 : chat principal + prompts insérés ; Deep Research,
  RFC et agents EXCLUS explicitement.
- Rubrique Réglages : CRUD, noms [a-z0-9_] uniques (« action » interdit),
  limites (nom/valeur/description/nombre). Présenter honnêtement : PAS un
  coffre à secrets (les valeurs partent au LLM, persistent en SQLite et dans
  l'historique).
- Table SQLite dédiée : migration Alembic, export RGPD, purge.
- Tests : valeurs avec accolades/retours ligne/placeholders (pas de
  récursion), valeurs simulant action/slash/directive -> zéro effet de bord,
  aperçu sans appel LLM, payload = bulle = historique, migration, limites,
  absence des valeurs dans les logs.

## Chantier 3 - Ollama auto-hébergé MVP LAN (le plus lourd - effort L)

- **Résolveur d'URL Ollama backend UNIQUE** consommé par chat, /api/tags,
  dashboard, Board, agents et fallbacks - aujourd'hui l'URL n'est même pas
  configurable côté frontend (setLLMConfig n'envoie que provider+model),
  plusieurs chemins recodent localhost:11434 (llm.py:441) et le **Board
  appelle Ollama directement depuis le navigateur** (BoardPanel.tsx:67).
  Préférence persistée + précédence DB/env + invalidation du singleton.
- **Anti-SSRF V1 strict** : localhost/loopback ou IPv4 RFC1918 littérale,
  HTTP, port 11434 seul, sans userinfo/chemin/query. `.local`, IPv6, ports
  libres, TLS/auth, VPS : REPORTÉS. Client HTTP dédié avec
  `follow_redirects=False` et `trust_env=False` (le client partagé suit les
  redirections et honore les proxies système).
- **Honnêteté** : dire explicitement que le LAN en HTTP = prompts en clair
  vers un serveur de confiance. Badges : « Local » (loopback) vs
  « Auto-hébergé (LAN) » - et **provenance local|lan|cloud PERSISTÉE par
  message** pour que l'historique reste juste après un changement de config
  (MessageBubble:542 et le prompt système affirment aujourd'hui « rien ne
  sort »).
- Activation atomique : mode + URL -> test -> modèle (découvert via /api/tags
  ou saisi) -> activer. Instance hors ligne : configurable quand même
  (saisie manuelle du modèle - le bouton Custom est aujourd'hui masqué pour
  Ollama et le provider désactivé si localhost ne répond pas, LLMTab:510).
- Tests : matrice SSRF (redirections, proxy, ports, adresses réservées),
  persistance/redémarrage, précédence env/DB, même URL partout (tags, chat,
  Board, agents, fallback), modèle manuel hors ligne, provenance en stream
  et après rechargement.

## Ordre proposé (révisé par coût/risque) et release

**5 -> 4 -> 3** (le 5 est mûr et pas cher, le 3 est le plus lourd et touche
la promesse de souveraineté - à faire en dernier avec le plus de soin).
L'ordre initial 3->4->5 reste possible si la valeur testeur prime.
Release 0.29.0-alpha dès que le chantier 2 (1a+1b+1c) est recetté.
