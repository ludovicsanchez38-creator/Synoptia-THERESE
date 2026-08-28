# O7 - Le « score de confiance » récompense l'aplomb, et il est aveugle aux accents

**Parti du persona 04 (l'avocat)** : sur le délai de saisine des prud'hommes,
THÉRÈSE cite un article qui n'existe pas (L.1252-20), annonce un mois au lieu de
douze — et affiche `confidence_score: 100`, `should_verify: false`.

- **Gravité** : majeur
- **Nature** : defaut_app (deux défauts distincts, cumulés)
- **Source** : `services/token_tracker.py:428-449` et `:452-486`

## Défaut 1 - le score mesure le ton, pas la fiabilité

```python
base_confidence = 100
penalty_per_phrase = 15
confidence_score = max(0, base_confidence - (len(detected_phrases) * penalty_per_phrase))
```

Le score part de 100 et **descend** à chaque formule de doute trouvée dans le
texte. Autrement dit : une réponse qui n'exprime aucune réserve obtient 100 %.

**Plus le modèle est péremptoire, plus il paraît fiable.** C'est exactement
l'inverse de ce qu'un indicateur de confiance doit faire, et c'est le pire cas
possible pour une hallucination : une invention assénée sans nuance obtient le
score maximum.

`should_verify` aggrave : il exige `confidence_level in ["low","medium"]` **et**
`len(detected_phrases) > 1`. Une réponse entièrement fausse mais affirmative ne
déclenche donc **jamais** d'invitation à vérifier.

## Défaut 2 - les formules françaises sont écrites sans accents

La liste contient bien 11 formules françaises. Cinq sont inertes :

```python
"je ne suis pas sur",        # « sûr »
"peut-etre",                 # « peut-être »
"d'apres ce que je sais",    # « d'après »
"sous reserve",              # « réserve »
"a ma connaissance",         # « à ma connaissance »
```

La comparaison est un simple `response.lower()`, sans dé-accentuation. Le
produit possède pourtant un `_fold` (BUG-146, recherche de contacts insensible
aux accents) : il n'est pas utilisé ici.

## Preuve, exécutée sur le code du dépôt

```
accents corrects       -> score 100 | niveau high   | verifier: False | detecte: 0
sans accents           -> score  25 | niveau low    | verifier: True  | detecte: 5
hallucination nette    -> score 100 | niveau high   | verifier: False | detecte: 0
```

Les deux premières lignes sont **la même phrase**, une fois bien orthographiée,
une fois sans accents. Une assistante française qui écrit correctement sa langue
est classée « confiance élevée » ; la même prudence mal orthographiée est
classée « faible ».

## Correctifs

1. **Dé-accentuer avant comparaison** (`_fold`, déjà écrit ailleurs). Cinq
   lignes, ça répare le défaut 2 immédiatement.
2. **Renommer, ou retirer.** Tant que le calcul est ce qu'il est, l'appeler
   « confiance » est une promesse fausse. C'est un détecteur de formules de
   réserve : soit on le nomme ainsi et on cesse d'en faire un pourcentage, soit
   on ne l'affiche pas. Un chiffre faux sur un point de droit est pire
   qu'aucun chiffre — le persona 04 : « une erreur de délai affirmée avec
   aplomb, je la recopie, je rate la prescription ».
3. Si un vrai indicateur est voulu, il ne peut pas venir du texte de la réponse :
   il faut le rattacher aux sources (le corpus juridique interne n'a **aucune**
   entrée sur le licenciement, ce qui aurait dû se voir).

## Le test qui manque

Un test qui donne au détecteur la même phrase avec et sans accents et exige le
même score. Il serait rouge aujourd'hui.
