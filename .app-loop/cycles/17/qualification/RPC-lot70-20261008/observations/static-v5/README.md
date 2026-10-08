# MAIN11 : trois origines historiques exactes du même IPS

Statut : v5 préparé seulement, non exécuté. La préimage v4, ses refus MAIN et les reçus de tests 71 verts/rouges restent inchangés. Le script ne lance ni G1, ni Chrome, ni service.

Le collecteur accepte une résolution archivale du rapport IPS uniquement depuis trois paires origine/pointeur épinglées :

1. INDEX Chrome RootDomain `c0f542c3…` (2 605 octets), `/origin_refs/4` ; EVIDENCE `57253794…` (803 octets), diagnostic_only et PID 25577 obligatoires.
2. Reçu 71 tests v3 `c0864b43…` (68 793 octets), `/source_refs/267`, 307 refs, passed=true et errors=0.
3. Reçu 71 tests v2 `1955d363…` (66 947 octets), `/source_refs/267`, 303 refs, **passed=false et errors=3**. Le v3 référence ce rouge exact.

Chaque entrée doit porter le même ancien chemin/SHA-256/taille (31 835 octets). L'ancien chemin doit répondre ENOENT. La copie archivée close6 est relue et rehashée, régulière/canonique, UID 501, GID 0, mode 100600, nlink 1. Seul son chemin réel entre dans `refs` et `pending`. L'observation de sortie précise pour chaque origine si le reçu de tests était vert ou rouge, la mesure fraîche et l'absence de lien de provenance prétendu avec le reçu close6. Toute autre origine, position, mutation ou référence manquante reste bloquante.

Préimage : `preimages/verify-prepared-wrapper-v4.mjs`. Diffs direct et inverse comparés byte-exacts aux deux fichiers. Contrôles préparatoires read-only : hash/taille des trois origines et de la copie, champs JSON ciblés, stat du chemin original et de l'archive. Aucun contrôle MAIN11 n'a été lancé avec v5 ; aucune qualification native, FULL ou release n'en découle.
