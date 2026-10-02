# Dépendances du cycle 15 : décision de release

Décision technique de Codex, dans le périmètre de release délégué par Ludo
le 01/10/2026. Cette décision traite les six avis initiaux du gate Python,
puis les huit avis pypdf apparus dans l’audit de main.
Elle ne constitue pas un verdict de sécurité général ni une correction de
tous les avis historiques déjà documentés dans la CI.

## B1767 : huit avis pypdf et contrôle du lecteur

Les liens `.app-loop` ci-dessous désignent des archives locales ignorées par Git,
non téléversées sur GitHub. Le rapport de release porte aussi les liens publics CI.

Après l’intégration de la PR98 sur `main` `39ac49bd`, l’audit Python
échoue sur huit avis de pypdf 6.16.2. Les onze autres jobs des trois workflows CI réussissent.
Le [constat CI final](../.app-loop/cycles/15/reprise/release-go/ci-main-final-39ac49bd-20261001T163653Z/index.json) conserve les trois workflows et leurs
vrais SHA. Les portes vertes et le plateau 2/2 sur `92f72f3d` deviennent
historiques ; le compteur de nouvelles rondes est remis à zéro.

Les [sources primaires et leur chronologie](../.app-loop/cycles/15/reprise/release-go/pypdf-security/avis.md) indiquent
6.19.0 comme maximum des premières versions corrigées des huit avis.
L’identité des sources entre les deux CI et leurs dates étayent une
actualisation de la base de vulnérabilités. Cette causalité reste une
inférence : la réponse réseau utilisée par le premier audit n’a pas été
capturée. Elle ne traduit pas un nouveau changement applicatif entre ces CI.

La correction sélective relève le minimum à `pypdf>=6.19.0` et verrouille
pypdf 6.19.0. Aucune version d’un autre paquet n’est changée. Le workflow,
ses treize arguments d’exception et les versions modèles restent inchangés.
Aucun des huit avis pypdf n’est ajouté aux exceptions.

L’[audit réel en quatre états](../.app-loop/cycles/15/reprise/release-go/pypdf-b1767/audit-quatre-etats-20261001T164121.103494Z/receipt.json) utilise l’export production
`uv export --locked --no-hashes --no-dev` dans des copies, avec la garde
exacte des versions modèles. Les deux gardes sortent zéro :

| État audité | pypdf | Avis non exemptés | Code de sortie |
| --- | --- | --- | --- |
| Ancien export | 6.16.2 | 8 | 1 |
| Nouveau lock exporté | 6.19.0 | 0 | 0 |
| Sabotage, seul pypdf réintroduit dans l’export copié | 6.16.2 | 8 | 1 |
| Export restauré exact | 6.19.0 | 0 | 0 |

Les empreintes de pyproject/lock/CI sont conservées pendant ces quatre
audits. L’export contient 132 dépendances versionnées et une entrée
éditable non identifiable par pip-audit, explicitement ignorée.
Les 18 avis ignorés sont les dettes et alias déjà présents, associés aux
treize arguments inchangés. Zéro avis non exempté ne signifie pas zéro
risque, ni une inspection du modèle/cache natif ou de l’environnement installé.

La [qualification du lecteur et des PDF](../.app-loop/cycles/15/reprise/release-go/pypdf-b1767/tests-pdf-20261001T164532.712744Z/qualification.json) passe réellement
74/74 cas, sans échec, erreur ni skip, sous pypdf 6.19.0. Ses sept nouveaux
cas exercent le parseur produit et `read_file` sur de vrais PDF : ordre
des pages et accents, flux brut/compressé, borne de 100 pages avec
troncature signalée, PDF tronqué et périmètre de projet. Ces cas ne
reproduisent pas les huit CVE et ne qualifient pas un bundle natif.

B1767 est marqué `fixed` par le CLI canonique après ces preuves ciblées.
Le commit final `b73769f9e0d900075365f8cb2a57f18fd175ce98` porte seulement
`pyproject.toml`, `uv.lock` et les sept cas de `test_b1767_lecteur_pdf.py`.
Les versions réellement installées, les 33 cas PDF de la porte complète
fraîche et le delta B1765 sont liés dans la
[qualification actuelle B1767](../.app-loop/cycles/15/reprise/transitions/requalification-b1767-r1-b73769f9-final/b1767-qualification.json).
Les quatre états ciblés restent leurs vrais exports historiques, sans
réécriture ; les anciennes pages Apple ne sont pas annoncées comme rendus
nouveaux sous pypdf 6.19.

La [CI actuelle](../.app-loop/cycles/15/reprise/release-go/ci-pr99-all-pass-b73769f9-20261001T173643Z/index.json)
termine ses douze jobs avec succès. Le premier timeout Rust pendant apt
et le snapshot initial restent conservés ; ce rejeu ne change pas le code.
Les deux rondes fraîches sont acceptées par le CLI au même HEAD. Le
[rapport de release](releases/v0.77.0-alpha.md#mesures-actuelles-sur-b73769f9)
centralise les portes et les vraies acceptations. Aucun asset publié,
bundle natif, cache privé ou modèle configurable supplémentaire n’est
qualifié par ces résultats.

## Quatre avis initiaux traités par mise à jour

- `urllib3` passe de 2.7.0 à 2.8.0. Le correctif éditeur traite
  CVE-2026-97687, CVE-2026-97688 et CVE-2026-97689. Les contraintes requests
  et Qdrant autorisent cette version. Les trois risques concernent la
  séparation TLS proxy/destination et deux traitements de flux malveillants.
  Sources : [avis TLS](https://github.com/urllib3/urllib3/security/advisories/GHSA-8988-9cw3-xx77),
  [Deflate](https://github.com/urllib3/urllib3/security/advisories/GHSA-gh4c-6fx4-qh6g),
  [chunks](https://github.com/urllib3/urllib3/security/advisories/GHSA-vxq7-64xx-v4gw).
- `oauthlib` passe de 3.3.1 à 4.0.0, correctif de CVE-2026-49265.
  Le vérificateur PKCE serveur concerné n'est pas instancié dans les usages
  THÉRÈSE lus ; la mise à jour reste préférable à une exception. Les
  contraintes requests-oauthlib/Google l'autorisent. Le flux applicatif est
  un client PKCE qui échange ses requêtes avec HTTPX.
  Sources : [avis éditeur](https://github.com/oauthlib/oauthlib/security/advisories/GHSA-xpv3-w29h-x7cv),
  [changements 4.0.0](https://raw.githubusercontent.com/oauthlib/oauthlib/v4.0.0/CHANGELOG.rst).

Ces versions sont verrouillées dans `uv.lock`. Les portes finales et le
packaging restent requis ; une résolution de lock réussie ne prouve pas
leur compatibilité à l'exécution.

## Deux exceptions exactes, risque conservé

### Sentence-transformers 5.2.0, CVE-2026-68770

L'application autorise explicitement le code de son modèle d'embeddings
avec `trust_remote_code=True`. Elle n'utilise donc pas False comme frontière
de refus que cet avis permet de contourner sur un modèle local. Cette
exception accepte le chargement de code modèle déjà prévu par le produit.
Elle ne protège pas contre un modèle malveillant ni un cache altéré.

La version 5.6.0 indiquée par l'audit ajoute un avertissement, tout en
conservant la confiance implicite locale jusqu'à la future 6.0. Elle ne
supprime pas le comportement en cause et ne sécuriserait pas l'appel True
actuel. Elle n'est pas annoncée comme correction dans cette release.
Sources : [modification réelle](https://github.com/huggingface/sentence-transformers/commit/ae1acc3fb2aa2004577b297eb4a915ce7a03316a),
[release 5.6.0](https://github.com/huggingface/sentence-transformers/releases/tag/v5.6.0).

### Transformers 4.57.6, CVE-2026-80047

L'avis porte sur le chargement de `custom_generate` avant le contrôle de
confiance, sans version corrective indiquée par les sources consultées.
Le chemin transitif est lu jusqu'à `AutoModel.from_pretrained`, qui peut
l'activer quand `can_generate()` vaut True. L'absence d'appel direct à
`generate()` dans THÉRÈSE ne justifierait pas une exception.

La classe Nomic par défaut examinée ne possède aucune méthode de génération
et son chargeur est distinct. La déduction statique donne `can_generate=False`
pour les fichiers de modèle/code et les bases Transformers examinés. Les
révisions observées sont `e9b6763023c676ca8431644204f50c2b100d9aab` pour le modèle
et `7710840340a098cfb869c4f65e87cf2b1b70caca` pour son code. Ce sont des
références de l'audit, pas des révisions imposées par l'application.
Sources : [configuration Nomic](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5/blob/e9b6763023c676ca8431644204f50c2b100d9aab/config.json),
[garde AutoModel](https://raw.githubusercontent.com/huggingface/transformers/v4.57.6/src/transformers/models/auto/auto_factory.py),
[prédicat Transformers](https://raw.githubusercontent.com/huggingface/transformers/v4.57.6/src/transformers/modeling_utils.py),
[avis](https://github.com/advisories/GHSA-x9r9-c232-4q39).

Cette exception est bornée au modèle et à la pile examinés. Elle ne qualifie
pas un autre modèle configuré par ENV/.env, une autre révision ni un cache
modifié. L'instance native et son cache privé n'ont pas été inspectés.
Le code modèle demeure explicitement autorisé par True.

## Dette et conditions de réexamen

Les deux avis restent une dette de sécurité, sans prétendre être corrigés.
Un changement de modèle, de configuration locale, de code ou de cache,
ainsi que tout changement de Transformers/Sentence-transformers, impose de
réexaminer ces exceptions. Les textes à encoder ne deviennent pas un
identifiant de modèle dans le service actuel.

La CI vérifie les deux versions exactes du lock avant l'audit. Un changement
de version fait échouer ce garde et exige une nouvelle décision. Les
conditions portant sur la configuration native, le modèle et son cache
restent une obligation de réexamen ; ce garde de versions ne les mesure pas.

La migration groupée déjà différée doit revoir la provenance du modèle ET
de son code, le cache effectivement chargé et la compatibilité des poids,
dimensions et builds des trois systèmes. Épingler seulement `revision`
ne suffit pas : le chargeur Nomic ne propage pas ce paramètre à tous ses
chargements de poids. Le runtime natif n'impose pas les drapeaux offline
des tests ; offline ne neutralise pas un Python déjà local et pourrait
empêcher le premier chargement d'un modèle absent.

## Preuves canoniques de cette décision

- [Audit des six avis](../.app-loop/cycles/15/reprise/release-go/audit-dependances-six-alertes-20261001T123235.413888Z/rapport.md).
- [Complément Nomic et sources exactes](../.app-loop/cycles/15/reprise/release-go/complement-nomic-exemptions-20261001T130503.973222Z/rapport.md).
- [Lock et workflow avant correction](../.app-loop/cycles/15/reprise/release-go/securite-dependances-20261001T122645.695003Z/avant.json).
- [Audit exécuté, sabotage et restauration](../.app-loop/cycles/15/reprise/release-go/controle-b1765-20261001T132324.537527Z/execution-finale.json).

L'export de production local donne 133 entrées : 132 dépendances auditées et
l'entrée éditable du projet, que pip-audit ne peut identifier comme paquet.
Le témoin ancien retrouve six avis ; le courant et sa restauration sortent
avec le code zéro après les exceptions exactes. Réintroduire les anciennes
versions urllib3/oauthlib avec ces mêmes exceptions retrouve quatre avis.
Le garde refuse une version Transformers modifiée dans une copie, puis
accepte sa restauration. Les avis ignorés restent des dettes, y compris les
deux nouveaux avis modèles. Ce résultat local ne remplace pas la CI finale.

Les index liés donnent les empreintes et les limites de chaque lecture.
Les portes actuelles sont centralisées dans le
[rapport canonique 0.77.1](releases/v0.77.1-alpha.md). Les mesures et liens
antérieurs de cette décision conservent leurs HEAD historiques.
