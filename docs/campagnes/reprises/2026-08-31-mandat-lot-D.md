Tu corriges du code. Réponds en FRANÇAIS.

Dépôt : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE`. Tu es sur la
bonne branche, arbre propre. Backend Python/FastAPI (`src/backend/app`),
frontend React (`src/frontend/src`).

Les défauts ci-dessous viennent des revues du 30/08/2026, archivées dans
`docs/audits/2026-08-30-revue-fonctionnalites/`. Tu peux les lire pour le
détail : fichiers, lignes, reproduction.

## La règle qui prime

**Un échec franc vaut mieux qu'un livrable faux.** Si quelque chose ne peut
pas être fait correctement, l'application doit le DIRE et ne rien livrer. Un
utilisateur qui voit une erreur sait qu'il doit recommencer ; un utilisateur
qui reçoit un document vide croit que c'est fait.

## La discipline, non négociable

1. **TDD** : test d'abord, rouge d'abord, rouge pour la BONNE raison.
2. **Sabotage** : casse ton correctif, vérifie que le sabotage s'est appliqué,
   vérifie que le test rougit, restaure. Raconte-le.
3. **Les cinq portes**, chiffrées, avant de rendre :
   - `uv run ruff check src/backend/ tests/`
   - `THERESE_ENV=test TRANSFORMERS_OFFLINE=1 uv run pytest tests/ --ignore=tests/e2e -q --timeout=30 -p no:cacheprovider --junit-xml=/tmp/grok-<horodatage-NEUF>.xml`
     **Lis le XML, jamais la console** (tronquée par un `os._exit`). XML neuf
     à chaque exécution.
   - `cd src/frontend && npx tsc --noEmit && npx eslint src --max-warnings 27 && npx vitest run`
   - `rm -rf .mypy_cache && uv run mypy src/backend/app --ignore-missing-imports --no-error-summary | grep -c " error:"` — plafond **1001**.
4. **Commentaires en français** : le pourquoi et l'incident, pas le quoi.
5. **Aucun élargissement.** Tu ne refactores pas, tu ne renommes pas, tu ne
   reformates pas un fichier que ton correctif ne concerne pas.
6. Tu commites par défaut corrigé. **Tu ne pousses pas. Tu ne fusionnes pas.**

Si un défaut ne peut pas être corrigé sans changer la conception, **tu ne le
corriges pas** : tu le dis, tu passes au suivant. Mieux vaut cinq défauts
fermés proprement qu'un sixième bâclé.

## Ce que tu rends

Par défaut : ce que tu as changé, le test qui le couvre, le résultat du
sabotage. Puis les portes chiffrées. Puis **ce dont tu n'es pas sûr** — c'est
la partie que je lis en premier.

---


# Où tu travailles (lis ceci en premier)

Ton dépôt est **`/tmp/soso-lot-D`** (un arbre de travail git séparé), branche
**`soso/lot-D`**, arbre propre, environnement Python déjà installé.
Ne travaille PAS dans `~/Desktop/Dev Synoptia/Synoptia-THERESE` : une release
y est en cours au même moment, tu te marcherais dessus avec moi.

La base contient déjà cinq lots de correctifs fusionnés (B, C, E, F, G) issus
d'une autre passe. Si un défaut ci-dessous te semble déjà corrigé, vérifie
puis dis-le et passe au suivant : ce n'est pas une erreur de ta part.

Un premier agent avait commencé le point 8 (les horloges) avant de tomber en
panne de crédits. Son travail inachevé et **non vérifié** est dans
`/tmp/grok-lot-D-inacheve.patch`. Tu peux le lire pour gagner du temps, mais
tu ne l'appliques pas tel quel : tu refais la démarche complète (test rouge
d'abord, sabotage). Un correctif dont personne n'a vu le test rougir ne vaut
rien.

# LOT D — la donnée dans la durée

Source : `docs/audits/2026-08-30-revue-fonctionnalites/grok-donnee-dans-la-duree.md`.

**C'est le lot le plus délicat : il touche au schéma et à des documents
comptables.** Quand un choix engage la forme des données ou la valeur légale
d'une pièce, **prends l'option la plus conservatrice**, et dis-le dans « ce
dont je ne suis pas sûr ». Une migration qui perd une donnée est
irrattrapable.

1. **Les prestations n'existent ni pour l'export RGPD, ni pour
   l'anonymisation, ni pour « effacer toutes mes données ».** Un client
   exerce son droit à l'oubli et l'intitulé, le montant HT et le financeur
   restent en base. C'est une non-conformité, pas un confort.
2. **Une facture n'a pas de copie de son client.** Elle pointe le contact.
   Supprimer la personne rend le PDF 404 alors que la pièce existe, la fait
   disparaître du chat tout en la comptant dans l'encours, et **changer
   l'adresse d'un contact réécrit rétroactivement toutes les pièces
   passées**. Une facture émise est censée être figée. Si tu ajoutes des
   colonnes de snapshot, **les factures existantes doivent être remplies
   depuis leur contact actuel à la migration**, pas laissées vides.
3. **Supprimer un dossier laisse fichiers, rendez-vous et documents sur un
   identifiant mort.** L'interface n'envoie jamais `cascade`.
4. **Supprimer un contact en cascade contourne le ménage de
   `delete_project`.**
5. **Une sauvegarde restaurée promet des fichiers Office que le disque n'a
   plus.**
6. **La barre latérale n'a plus que 50 conversations après redémarrage.**
7. **L'aller-retour export puis import ne redonne pas le même état.**
8. **« Aujourd'hui » n'est pas la même horloge partout** : deux relances
   persistées, deux horloges, et le brief du 30 n'est pas celui du 29.

Deux causes de fond nommées par la revue, qui expliquent la moitié de cette
liste : **deux systèmes de schéma coexistent** (Alembic et des `ALTER TABLE`
ad hoc dans `database.py`), et **les clés étrangères SQLite ne sont jamais
activées**. Si tu poses `PRAGMA foreign_keys`, mesure d'abord ce que ça
casse : c'est le genre de bascule qui transforme un orphelin silencieux en
erreur au démarrage. Si la mesure te dit que c'est trop large pour ce lot,
**ne le fais pas** et écris-le.
