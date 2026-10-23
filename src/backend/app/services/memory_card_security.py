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
    r'politi\w*|electora\w*|\bvote\b|\bparti\b',
    r'religi\w*|\bprie\b|\bmesse\b|philosoph\w*|\bconviction\w*\b',
    r'syndi[cq]\w*|\b(?:cgt|cfdt|cftc)\b',
    r'geneti\w*|\badn\b|biometri\w*|reconnaissance\W+faciale|empreinte\W+digitale',
    r'sexu\w*|homosex\w*|heterosex\w*|bisex\w*|\bintim\w*\b',
))


# Une coordonnée de 15 à 34 caractères (ISO 13616), sans table nationale.
# Les bornes restent celles du texte d'origine ; seule la coordonnée candidate
# est compactée. La clé modulo 97 distingue les phrases telles que « de 14h ».
_MOTIFS_IBAN = tuple(re.compile(
    r'(?<![a-z0-9])([a-z][\W_]*[a-z][\W_]*\d[\W_]*\d'
    + r'(?:[\W_]*[a-z0-9]){' + str(longueur - 4) + r'})(?![a-z0-9])'
) for longueur in range(15, 35))


def _contient_iban(texte: str) -> bool:
    for motif in _MOTIFS_IBAN:
        for candidat in motif.finditer(texte):
            compact = re.sub(r'[^a-z0-9]', '', candidat.group(1))
            rearrange = compact[4:] + compact[:4]
            chiffres = ''.join(c if c.isdigit() else str(ord(c) - ord('a') + 10) for c in rearrange)
            if int(chiffres) % 97 == 1:
                return True
    return False


_IDENTIFIANT_SECRET = re.compile(
    r'\b[a-z][a-z0-9_]*(?:api_key|apikey|secret|token|password|passwd|mot_de_passe)[a-z0-9_]*\b'
    r'|\b(?:api_key|apikey|secret|token|password|passwd|mot_de_passe)[a-z0-9_]*\b'
)


def _contient_identifiant_secret(valeur: str) -> bool:
    # Préserver les frontières camelCase avant de normaliser la casse.
    identifiants = ''.join(
        c for c in unicodedata.normalize('NFD', unicodedata.normalize('NFKC', valeur))
        if unicodedata.category(c) not in ('Mn', 'Cf')
    )
    identifiants = re.sub(r'([a-z])([A-Z])', r'\1_\2', identifiants)
    identifiants = re.sub(r'([A-Z])([A-Z][a-z])', r'\1_\2', identifiants).casefold()
    return any(m.group() not in {'token_limits', 'secretaire', 'secretaires', 'secretariat', 'secretariats'}
               for m in _IDENTIFIANT_SECRET.finditer(identifiants))


def motif_sensible(valeur: Any) -> str | None:
    if isinstance(valeur, dict):
        return next((motif for k, v in valeur.items() if (motif := motif_sensible([k, v]))), None)
    if isinstance(valeur, (list, tuple)):
        return next((motif for v in valeur if (motif := motif_sensible(v))), None)
    if not isinstance(valeur, str):
        return None
    texte = _normaliser(valeur)
    # Garder les racines de secrets dans les identifiants concaténés. Seuls
    # les noms professionnels explicites (« secrétaire ») sont exceptés.
    if _contient_identifiant_secret(valeur):
        return 'une clé ou un jeton secret'
    if MOTIFS[0].search(texte):
        return 'un mot de passe ou une clé secrète'
    if any(m.search(texte) for m in MOTIFS[1:4]):
        return 'une coordonnée bancaire ou un jeton secret'
    # Exceptions métier ciblées : on retire seulement le groupe ambigu, puis
    # on cherche encore les catégories sensibles dans le reste de la phrase.
    contexte = re.sub(
        r'\bdiagnostics? (?:de performance energetique|reseau|comptable|structurel|de toiture'
        r'|des besoins de formation|du serveur informatique)\b'
        r'|\btraitements? (?:de (?:la |une )?commande|des commandes|des factures fournisseurs'
        r'|des ecritures comptables|des eaux du chantier|des inscriptions en formation'
        r'|des donnees informatiques)\b', '', texte
    )
    if MOTIFS[4].search(texte) or re.search(r'\b(?:diagnostic\w*|traitement\w*|psychiatri\w*)\b', contexte):
        return 'une information de santé'
    contexte = re.sub(r'\bparti en conges\b|\bje vous prie\b', '', contexte)
    categories = ('une origine ethnique ou raciale', 'une opinion politique',
                  'une conviction religieuse ou philosophique', 'une appartenance syndicale',
                  'une donnée génétique ou biométrique', 'une information de vie sexuelle')
    for motif_categorie, categorie in zip(MOTIFS[5:], categories, strict=True):
        if motif_categorie.search(contexte):
            return categorie
    if re.search(r'\b(?:adherent(?:e|s|es)?|membres?|syndique(?:e|s|es)?|syndicat)\W+(?:(?:a|de|du)\W+)?fo\b', texte):
        return 'une appartenance syndicale'
    if _contient_iban(texte):
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
