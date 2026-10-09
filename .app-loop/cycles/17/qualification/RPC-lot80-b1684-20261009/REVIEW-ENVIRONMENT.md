# B-1684 : revue préparatoire indépendante

Rédigé le 9 octobre 2026 à 06:44 UTC. L'analyse du backlog, du code et du test mémoire a été faite **avant les exécutions de tests par MAIN** ; son heure précise n'a pas été enregistrée. La relecture du diff et des reçus ci-dessous est postérieure. Je n'ai exécuté aucun test, importé aucun module produit, accédé à aucune DB ou UI, ni modifié le produit ou le backlog.

## Constat préalable

- `.app-loop/bugs.json`, entrée B-1684 vers les lignes 36891–36905 : statut historique `deferred`, sévérité historique `low`, observation d'un retour `True` sur exception. Ce classement ne prouve pas l'état actuel du code.
- Préimage produit `rgpd_auto-before.py`, SHA-256 `698c3501064039594c6743a2e463188921180ec9f2cca75fe6eb0df6b7009042` : `_is_purge_enabled()` absorbe `Exception` pendant la lecture de `rgpd_purge_enabled`, puis retourne `True`. `auto_purge_expired_contacts()` ne s'arrête que si cette fonction retourne `False` ; sinon elle poursuit vers la durée de rétention et les contacts.
- `src/backend/app/main.py`, lignes 375–392 : si les services ne sont pas désactivés, la purge est appelée au démarrage puis toutes les 24 heures. L'impact est conditionnel : une lecture du réglage peut échouer alors que les lectures suivantes réussissent. Aucune anonymisation physique n'est constatée dans cette revue.
- `src/backend/app/routers/rgpd.py`, lignes 416–435, SHA-256 `cf5b0935b5a0d31dd4646686833cdcc8d744454955cbe30ea129747b6af1a1e8` : la route conserve `enabled=True` si la préférence n'existe pas. Dans le service, une valeur vide garde aussi le retour final `True` ; la route ne confirme pas ce cas (une préférence présente et vide y donne `False`). La correction visée distingue ces valeurs d'une **erreur** de lecture, sans changer le défaut ni les durées.

Le correctif minimal proposé avant les tests était de retourner `False` uniquement dans `except Exception`, tout en laissant le `return True` final pour l'absence réelle de préférence.

## Portée du test préparé, lue avant exécution

`tests/test_b1684_purge_reglage_illisible_memoire.py`, SHA-256 `c755e7e1abebce3b569ca69f80a5d297da21b56989488965a830cf221f50c70b`, extrait intégralement par AST les deux fonctions async du fichier source ; il ne charge pas `app.main`. La session, la sélection et le seul import `Preference` sont simulés. Le témoin positif interrompt `auto_purge_expired_contacts()` à `_get_purge_retention_months`, avant toute lecture des contacts. Les 14 méthodes couvrent construction, entrée, requête, résultat, sortie du contexte, valeur illisible, valeur absente/vide, valeur activée/désactivée, annulation et témoin positif. Aucun bloqueur déterministe n'a été relevé à la lecture.

Le runner privé `runner.py` charge ce test par chemin et écrit un reçu exclusif. Ses champs `DB=false`, `Chrome=false` et `FULL=false` décrivent le périmètre ; il n'installe pas de hook d'audit. Ces tests ne prouvent ni session SQL physique, ni UI, ni purge réelle, ni qualification FULL.

## Relecture ultérieure, sans exécution par moi

Le diff produit actuellement lu change la docstring et place `return False` dans le seul `except`, en préservant le retour final `True`. Source actuelle SHA-256 `c5fdf5c4ee1fbbf6eb854e7a7e631818cd94a97160127f80fe9a506e0dea2892` ; préimage ci-dessus inchangée.

Reçus de MAIN relus comme **résultats de MAIN**, pas comme des tests rejoués ici : `red-result.json` (`154adeab…`) rapporte 14 tests dont 11 échecs sur l'ancienne source ; `final-green-result.json` (`52515df2…`) rapporte 14/14 verts sur la source corrigée ; `sabotage-result.json` (`f0314658…`) rapporte 11 échecs après réintroduction privée du comportement fautif. Gate conduit la revue indépendante de ces reçus. Aucun de ces résultats ne transforme le test mémoire en preuve d'exécution DB/UI ou de ronde FULL.
