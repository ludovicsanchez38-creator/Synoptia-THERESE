"""Garde locale v1, partagée avec le journal. Corpus explicite, refus sans payload.

Ce garde ne prétend pas détecter toute inférence dans toute langue. Il ferme les
catégories connues, les valeurs de secrets et les obfuscations du corpus v1.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.services.preference_security import est_cle_secrete_de_preference

MESSAGE_REFUS = 'Cette donnée sensible ne peut pas devenir une fiche mémoire.'


def _normaliser(texte: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', unicodedata.normalize('NFKC', texte).casefold())
                   if unicodedata.category(c) not in ('Mn', 'Cf'))


# Noms, catégories et inférences formulées dans le corpus professionnel v1.
MOTIFS = tuple(re.compile(m) for m in (
    r'pass(?:word|phrase)|mot\W*de\W*passe|cle\W*(?:api|secrete|privee)|api[\W_]*key',
    r'access\W*token|refresh\W*token|bearer\W|jeton\W|secret\W|\biban\b',
    r'\bakia[a-z0-9]{16}\b|\baiza[a-z0-9_-]{20,}|\beyj[a-z0-9_-]{6,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}',
    r'\b(?:sk|pk)[-_][\w-]{8,}|\bgh[pousr]_[\w]{12,}|\bxox[baprs]-[\w-]+',
    r'\b(?:sante|medical\w*|medic\w*|diabet\w*|cancer\w*|oncolog\w*|anxiolyti\w*|diagnostic\w*|traitement\w*|maladie\w*|patholog\w*|hospital\w*|handicap\w*|vih|enceinte|grossesse)\b',
    r'ethni\w*|\brac(?:e|ial\w*)\b|\borigine\W+(?:raciale|ethnique)',
    r'politi\w*|electora\w*|\bvote\b|\bparti\b',
    r'religi\w*|\bprie\b|\bmesse\b|philosoph\w*|\bconviction\w*\b',
    r'syndi[cq]\w*|\b(?:cgt|cfdt|fo|cftc)\b',
    r'geneti\w*|\badn\b|biometri\w*|reconnaissance\W+faciale|empreinte\W+digitale',
    r'sexu\w*|homosex\w*|heterosex\w*|bisex\w*|\bintim\w*\b',
))


def contient_sensible(valeur: Any) -> bool:
    if isinstance(valeur, dict):
        return any(contient_sensible(k) or contient_sensible(v) for k, v in valeur.items())
    if isinstance(valeur, (list, tuple)):
        return any(contient_sensible(v) for v in valeur)
    if not isinstance(valeur, str):
        return False
    texte = _normaliser(valeur)
    if any(est_cle_secrete_de_preference(nom) for nom in re.findall(r'\b[a-z][a-z0-9_]*\b', texte)):
        return True
    if any(m.search(texte) for m in MOTIFS):
        return True
    compact = re.sub(r'[^a-z0-9]', '', texte)
    # IBAN complet, y compris épelé avec des séparateurs.
    if re.search(r'(?:fr\d{25}|(?:de|gb|be|es|it|nl|ch|lu|pt)\d{2}[a-z0-9]{11,30})', compact):
        return True
    # Cartes : Luhn, pas les identifiants métier (SIRET) admis par le corpus.
    for suite in re.findall(r'(?<!\d)(?:\d[ .-]?){13,19}(?!\d)', texte):
        chiffres = re.sub(r'\D', '', suite)
        if not 13 <= len(chiffres) <= 19:
            continue
        if len(chiffres) == 14 and re.search(r'\bsiret\b', texte):
            continue
        valeurs = [int(c) for c in chiffres[::-1]]
        somme = sum((n * 2 - 9 if n * 2 > 9 else n * 2) if i % 2 else n
                    for i, n in enumerate(valeurs))
        if somme % 10 == 0:
            return True
    # Valeurs isolées de jetons : alphabets mixtes longs. Pas les mots métier.
    return bool(re.search(r'\b(?=[a-z0-9_/-]{24,}\b)(?=(?:[a-z_/-]*\d){4})(?=[a-z0-9_/-]*[a-z])[a-z0-9_/-]+\b', texte))
