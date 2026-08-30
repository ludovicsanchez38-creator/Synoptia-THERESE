# Séquence arrêtée avec Ludo, 30/08/2026 au soir

## 1. Les revues, jusqu'à épuisement

Grok relancé avec un angle NEUF **tant qu'une passe rapporte plus de trois
findings**. Un angle = une question que les passes précédentes ne pouvaient
pas poser, pas une reformulation.

| Passe | Angle | Rendu |
|---|---|---|
| 1 | Chemin nominal (Grok) | NO-GO, ~15 findings |
| 1 bis | Chemins d'échec (Soso) | NO-GO, 19 findings |
| 2 | La donnée dans la durée (Grok) | NO-GO, 11 findings |
| 3 | Concurrence, ordre, bords (Grok) | en cours |
| 4 | La frontière de confiance | prêt, `/tmp/revue2f/angles/4-confiance.md` |
| 5 | La véracité de l'affichage | prêt |
| 6 | Le pluriel (deux comptes, deux devises, deux fuseaux) | prêt |

Soso est **à court de crédits** depuis le 30/08 au soir (« Your workspace is
out of credits »). Son angle a été repris par Grok, conformément à la règle
déjà écrite dans `memory/feedback_grok_remplace_codex_second_regard.md`.

## 2. Grok corrige, je vérifie

Ludo veut voir ce que Grok vaut en écriture de code, pas seulement en lecture.

Cadre : branche dédiée, mandat borné à trois défauts de la même famille (les
replis Office qui livrent un faux), discipline du dépôt imposée (TDD avec
test rouge d'abord, sabotage vérifié, les cinq portes, commentaires en
français, aucun élargissement).

Vérification par moi : lecture du diff entier, les cinq portes rejouées, et
sabotage de ses propres tests. Un test qu'il a écrit et que je peux casser
sans le faire rougir ne compte pas.

## 3. Les personas

**Après** les correctifs, jamais avant : lancer cinq agents sur un code qu'on
s'apprête à modifier produit cinq rapports périmés.

Instance de campagne prête (port 17941, isolée, Luna effort bas, conversation
vérifiée). Protocole et cinq briefs écrits, contrainte de persistance encodée
dans chacun.

## 4. La release, et son changelog

**Consigne explicite de Ludo, 30/08/2026 au soir :**

> « Le changelog sera long, je te prie de ne pas le réduire. On va être sur un
> des bumps les plus utiles depuis le début, puisqu'il va faire que
> l'application marchera. »

Donc : **on ne condense pas.** Les changelogs précédents tenaient en quatre
puces pour ménager les testeurs Discord. Celui-ci ne le fera pas.

La raison est juste : les bumps précédents ajoutaient des fonctionnalités ou
soignaient l'apparence. Celui-ci répare ce qui empêchait l'application de
fonctionner — les cinq modèles OpenAI qui ne répondaient sur aucun écran, les
replis Office qui livraient de faux documents, les états qui affirmaient
« Envoyé » sans l'être. Un utilisateur qui lit ce changelog doit comprendre
que ce qui ne marchait pas chez lui est nommé, et corrigé.

Le format des puces reste (émoji, titre gras, `•`, langage non technique,
lien de téléchargement), mais la LONGUEUR n'est plus une contrainte. Une
section par famille de défaut, et chaque défaut nommé en clair.
