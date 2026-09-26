# Passation à Codex : lancer le cycle 14 de la boucle Plateau

Écrit par Claude le 26/09/2026, à la demande de Ludo, à la fin du cycle 13.
Cette note dit où en est le dépôt et comment reprendre. Elle ne remplace ni le
skill ni `CLAUDE.md` : relis-les.

## État au 26/09/2026

- **Version publiée** : `v0.76.0-alpha` (tag sur `7b1af274`, bump `74f4dd55`),
  landing et `latest.json` en ligne, changelog Discord posté, app installée
  chez Ludo. Rapport : `docs/releases/v0.76.0-alpha.md`.
- **Boucle** : cycle 13 en phase `POST_RELEASE`
  (`python3 ~/.claude/skills/boucle-amelioration-app/scripts/app_loop.py status --repo .`).
- **Bugs du cycle 13** : 365 corrigés, 178 reportés (76 moyens, 101 faibles,
  aucun grave), 9 rejetés. Les reportés sont dans `.app-loop/bugs.json`
  (`status: deferred`, `cycle: 13`) : c'est la file de départ du cycle 14.
- **Plateau** : 2/2 sur `779383f5` (ronde A Claude, ronde B2 Grok 4.7). Trois
  correctifs sont arrivés APRÈS le plateau (B-1704, B-1705, B-1706) : couverts
  par leurs tests et la CI verte, pas par une ronde.
- **CI** : verte sur `7b1af274` (principale, Windows, e2e). mypy à froid :
  937 erreurs, égal à la baseline CI (`MYPY_BASELINE` dans `.github/workflows/ci.yml`).

## Lancer le cycle 14

1. `python3 ~/.claude/skills/boucle-amelioration-app/scripts/app_loop.py new-cycle --repo . --note "cycle 14, Codex"`
2. MAP différentiel : `cartography.py refresh` sur l'inventaire existant
   (`.cartography-work/inventory/`), jamais `inventory` (il orphelinerait les
   1 400 rapports). La carte est à 100 % sur `779383f5` ; seuls les fichiers
   modifiés depuis sont à relire.
3. CALIBRATE : les calibrations expirent le 27/09. L'instrument de couverture
   écran (`tests/couverture/couverture-ecran.mjs`) pose désormais le thème
   dans le store et refuse de mesurer si `data-theme` ne suit pas (B-1648).
4. REPRODUCE puis REPAIR en commençant par les reportés moyens (liste ci-dessous).

## Décisions attendues de Ludo (ne pas trancher à sa place)

1. **Périmètre du mode démo** : bloqués aujourd'hui, supprimer, anonymiser,
   renouveler le consentement, exporter une fiche, déplacer (projet, fiche du
   pipeline, tâche). En suspens : créations, import, exports du carnet, factures,
   fenêtre d'une tâche (B-1694, B-1698, B-1701, B-1702, B-1708).
2. Effacement des dictées déjà stockées chez les testeurs (réservé à Ludo).
3. Pied de page « Généré par THERESE - Synoptia » (réservé à Ludo).
4. B-1642 : le skill de proposition injecte les offres et tarifs Synoptïa dans
   les propositions de toute utilisatrice (marque, réservé à Ludo).

## Reportés à traiter en priorité (moyens)

- Factures : B-1605 (quantité 0,5 refusée par le formulaire), B-1615 (numéro
  attribué dès le brouillon, trou de numérotation), B-1671 (facture émise
  passable à « Annulée » sans avoir), B-1633, B-1634, B-1649, B-1682.
  Règles légales : vérifier à la source avant de coder.
- RGPD : B-1680, B-1696, B-1707 (transaction de campagne tenue pendant Qdrant,
  course avec un renouvellement), B-1693 (notifications de tâches et rendez-vous
  qui gardent un nom), B-1687 (préavis qui ne dit pas que les dossiers partent).
- Sécurité : B-1240 (accord cloud seulement côté interface pour la réponse à un
  e-mail), B-1563, B-1564 (`/preferences`).
- Agenda hors métropole : B-1499, B-1553, B-1609, B-1672.
- Tests : B-1703 (six tests appellent un vrai modèle si des clés cloud sont dans
  l'environnement : lancer pytest avec `env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY …`
  en attendant).

## Contraintes de la maison (rappel)

- Jamais le port 17293 ni `~/.therese` (l'application réelle de Ludo). Pile
  jetable : moteur 17393 + Vite 1420, arbre `/tmp/therese-demo-c12` (worktree
  détaché), données `/tmp/therese-demo-c13-verif/data`.
- Jamais `rm` : `mv … ~/.Trash/`. Jamais `git stash` nu ni `git checkout -- fichier`.
- Aucune release sans GO explicite de Ludo (`/release-therese`).
- TDD : test rouge d'abord, correctif, vert, sabotage qui refait rougir.
  Un sujet = un commit, en français, poussé.
- Poser `.agents-sync-paused` avant un sabotage (le hook Stop du Mac commite
  sinon le défaut témoin). Deux vieux verrous `.agents-sync-paused 2` et `3`
  (juillet) ne sont pas à nous : ne pas y toucher sans demander.
- pytest : lire le XML JUnit, la console est tronquée par `os._exit`.
- Règle d'arrêt apprise au cycle 13 : une fois la liste de Ludo tenue, ne
  corriger qu'un constat grave ou une régression qui rend un scénario pire
  qu'avant ; le reste passe en `deferred` et s'annonce au changelog.

## Outils utiles laissés en place

- Ronde de plateau indépendante : `.cartography-work/prompts/ronde-b2-c13-grok.md`
  (adaptée à un moteur sans navigateur piloté, sondes Playwright en Node).
- Constructeur de ronde A : `.app-loop/cycles/13/zero-check/construire-ronde-a.py`
  + `portes-ronde-a.sh` (variables `JOURNAL_MOTEUR`, `RAPPORT_COUVERTURE`).
- Audit DA : `.cartography-work/validation/da-audit-c9/audit-da-c9.mjs`
  (libellé de palette et état vide e-mail mis à jour au cycle 13).
- Grok 4.7 (`grok --prompt-file … -m grok-4.7`) : `--permission-mode plan`
  s'arrête avant d'analyser ; utiliser `bypassPermissions` avec une consigne de
  lecture seule, puis vérifier `git status`. Il reprend parfois des numéros de
  bug déjà attribués : renuméroter avant fusion.
