"""Garde locale v1, partagée avec le journal. Corpus explicite, refus sans payload.

Ce garde ne prétend pas détecter toute inférence dans toute langue. Il ferme les
catégories connues, les valeurs de secrets et les obfuscations du corpus v1.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

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
    r'\b(?:sante|medical\w*|medic\w*|diabet\w*|cancer\w*|oncolog\w*|anxiolyti\w*|maladie\w*|patholog\w*|hospital\w*|handicap\w*|vih|enceinte|grossesse)\b',
    r'ethni\w*|\brac(?:e|ial\w*)\b|\borigine\W+(?:raciale|ethnique)',
    r'politi\w*|electora\w*|\bvote\b|\bparti\W+(?:politique|socialiste|communiste|republicain|conservateur)\b',
    r'religi\w*|\bprie\W+(?:dieu|allah|le\W+seigneur)\b|\bmesse\b|philosoph\w*|\bconviction\w*\b',
    r'syndi[cq]\w*|\b(?:cgt|cfdt|cftc)\b',
    r'geneti\w*|\badn\b|biometri\w*|reconnaissance\W+faciale|empreinte\W+digitale',
    r'sexu\w*|homosex\w*|heterosex\w*|bisex\w*|\bintim\w*\b',
))


# Alphabet et longueur du BBAN (chiffres de contrôle compris), par pays.
# Décrire les groupes directement évite d'interpréter une expression régulière
# avec une seconde expression régulière (cas italien : lettre isolée).
_FORMATS_IBAN = {
    'fr': ((r'\d', 12), ('[a-z0-9]', 11), (r'\d', 2)),
    'de': ((r'\d', 20),),
    'gb': ((r'\d', 2), ('[a-z]', 4), (r'\d', 14)),
    'be': ((r'\d', 14),),
    'es': ((r'\d', 22),),
    'it': ((r'\d', 2), ('[a-z]', 1), (r'\d', 10), ('[a-z0-9]', 12)),
    'nl': ((r'\d', 2), ('[a-z]', 4), (r'\d', 10)),
    'ch': ((r'\d', 7), ('[a-z0-9]', 12)),
    'lu': ((r'\d', 5), ('[a-z0-9]', 13)),
    'pt': ((r'\d', 23),),
}
_MOTIFS_IBAN = tuple(
    re.compile(r'(?<![a-z0-9])' + r'[\W_]*'.join(
        [*pays, *(alphabet for alphabet, longueur in groupes for _ in range(longueur))]
    ) + r'(?![a-z0-9])')
    for pays, groupes in _FORMATS_IBAN.items()
)
_IDENTIFIANT_SECRET = re.compile(
    r'\b(?:(?:[a-z][a-z0-9]*_)*(?:api_key|apikey|secret|token|password|passwd|mot_de_passe)(?:_[a-z0-9]+)*'
    r'|[a-z][a-z0-9]*(?:secret|token|apikey)(?:_[a-z0-9]+)*)\b'
)


def _contient_identifiant_secret(valeur: str) -> bool:
    # Préserver les frontières camelCase avant de normaliser la casse.
    identifiants = ''.join(
        c for c in unicodedata.normalize('NFD', unicodedata.normalize('NFKC', valeur))
        if unicodedata.category(c) not in ('Mn', 'Cf')
    )
    identifiants = re.sub(r'([a-z])([A-Z])', r'\1_\2', identifiants)
    identifiants = re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2', identifiants).casefold()
    return any(m.group() != 'token_limits' for m in _IDENTIFIANT_SECRET.finditer(identifiants))


def motif_sensible(valeur: Any) -> str | None:
    if isinstance(valeur, dict):
        return next((motif for k, v in valeur.items() if (motif := motif_sensible([k, v]))), None)
    if isinstance(valeur, (list, tuple)):
        return next((motif for v in valeur if (motif := motif_sensible(v))), None)
    if not isinstance(valeur, str):
        return None
    texte = _normaliser(valeur)
    # Une clé de préférence est un identifiant entier, pas un fragment de mot
    # (« secrétaire » ne contient pas de secret). Les valeurs restent filtrées.
    if _contient_identifiant_secret(valeur):
        return 'une clé ou un jeton secret'
    if MOTIFS[0].search(texte):
        return 'un mot de passe ou une clé secrète'
    if any(m.search(texte) for m in MOTIFS[1:4]):
        return 'une coordonnée bancaire ou un jeton secret'
    # Les mots métier ambigus ne deviennent sensibles qu'en contexte médical
    # ou syndical ; les catégories explicites du corpus restent refusées.
    contexte = re.sub(r'\bdiagnostic de performance energetique\b|\btraitement de (?:la |une )?commande\b', '', texte)
    if any(m.search(texte) for m in MOTIFS[4:]) or re.search(
        r'\b(?:diagnostic|traitement)\b|\b(?:adherent|membre|syndicat)\W+(?:de\W+)?fo\b', contexte
    ):
        return 'une information personnelle sensible'
    # Examiner les coordonnées seules : compacter une phrase entière faisait
    # de « de 14h avec Paul Martin » un faux IBAN allemand. Respecter le BBAN
    # du pays et ses bornes, même avec une ponctuation entre caractères.
    if any(motif.search(texte) for motif in _MOTIFS_IBAN):
        return 'une coordonnée bancaire (IBAN)'
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
            return 'une coordonnée bancaire (carte)'
    # Valeurs isolées de jetons : alphabets mixtes longs. Pas les mots métier.
    return 'un jeton secret' if re.search(r'\b(?=[a-z0-9_/-]{24,}\b)(?=(?:[a-z_/-]*\d){4})(?=[a-z0-9_/-]*[a-z])[a-z0-9_/-]+\b', texte) else None


def contient_sensible(valeur: Any) -> bool:
    return motif_sensible(valeur) is not None


def message_refus(valeur: Any) -> str | None:
    motif = motif_sensible(valeur)
    return f'{MESSAGE_REFUS} Motif : {motif}.' if motif else None
