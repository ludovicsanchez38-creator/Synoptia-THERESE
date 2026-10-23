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
    r'\b(?:sante|medical\w*|medic\w*|diabet\w*|cancer\w*|oncolog\w*|anxiolyti\w*|maladie\w*|patholog\w*|hospital\w*|handicap\w*|vih|enceinte|grossesse|psychiatri\w*|antidepresseur\w*|chimiotherapi\w*|neurolog\w*)\b',
    r'ethni\w*|\brac(?:e|ial\w*)\b|\borigine\W+(?:raciale|ethnique)',
    r'politi\w*|electora\w*|\bvote\b|\bparti\b',
    r'religi\w*|\bprie\b|\bmesse\b|philosoph\w*|\bconviction\w*\b',
    r'syndi[cq]\w*',
    r'geneti\w*|\badn\b|biometri\w*|reconnaissance\W+faciale|empreinte\W+digitale',
    r'sexu\w*|homosex\w*|heterosex\w*|bisex\w*|\bintim\w*\b',
))


# ISO 13616, registre SWIFT, version 103 (septembre 2026), longueurs compactes.
# https://www.swift.com/swift-resource/9606/download
_LONGUEURS_IBAN = {
    'AD': 24, 'AE': 23, 'AL': 28, 'AT': 20, 'AZ': 28, 'BA': 20, 'BE': 16,
    'BG': 22, 'BH': 22, 'BI': 27, 'BR': 29, 'BY': 28, 'CH': 21, 'CR': 22,
    'CY': 28, 'CZ': 24, 'DE': 22, 'DJ': 27, 'DK': 18, 'DO': 28, 'EE': 20,
    'EG': 29, 'ES': 24, 'FI': 18, 'FK': 18, 'FO': 18, 'FR': 27, 'GB': 22,
    'GE': 22, 'GI': 23, 'GL': 18, 'GR': 27, 'GT': 28, 'HN': 28, 'HR': 21,
    'HU': 28, 'IE': 22, 'IL': 23, 'IQ': 23, 'IS': 26, 'IT': 27, 'JO': 30,
    'KW': 30, 'KZ': 20, 'LB': 28, 'LC': 32, 'LI': 21, 'LT': 20, 'LU': 20,
    'LV': 21, 'LY': 25, 'MC': 27, 'MD': 24, 'ME': 22, 'MK': 19, 'MN': 20,
    'MR': 27, 'MT': 31, 'MU': 30, 'NI': 28, 'NL': 18, 'NO': 15, 'OM': 23,
    'PK': 24, 'PL': 28, 'PS': 29, 'PT': 25, 'QA': 29, 'RO': 24, 'RS': 22,
    'RU': 33, 'SA': 24, 'SC': 31, 'SD': 18, 'SE': 24, 'SI': 19, 'SK': 24,
    'SM': 27, 'SO': 23, 'ST': 25, 'SV': 28, 'TL': 23, 'TN': 24, 'TR': 26,
    'UA': 29, 'VA': 22, 'VG': 24, 'XK': 20, 'YE': 30,
}
# Le lookahead ne consomme rien : un début invalide ne masque pas le suivant.
_DEBUT_IBAN = re.compile(r'(?<![A-Za-z0-9])(?=([A-Z][\W_]*[A-Z][\W_]*[0-9][\W_]*[0-9]))')
_SUITES_IBAN = {longueur: re.compile(
    r'(?:[\W_]*[A-Za-z0-9]){' + str(longueur - 4) + r'}(?![A-Za-z0-9])'
) for longueur in set(_LONGUEURS_IBAN.values())}


def _contient_iban(texte: str) -> bool:
    # Conserver la casse du pays, y compris après normalisation Unicode.
    texte = ''.join(c for c in unicodedata.normalize('NFKC', texte)
                    if unicodedata.category(c) != 'Cf')
    for debut in _DEBUT_IBAN.finditer(texte):
        entete = re.sub(r'[^A-Z0-9]', '', debut.group(1))
        longueur = _LONGUEURS_IBAN.get(entete[:2])
        if longueur is None:
            continue
        suite = _SUITES_IBAN[longueur].match(texte, debut.start() + len(debut.group(1)))
        if suite is None:
            continue
        compact = entete + re.sub(r'[^A-Za-z0-9]', '', suite.group()).upper()
        rearrange = compact[4:] + compact[:4]
        chiffres = ''.join(c if c.isdigit() else str(ord(c) - ord('A') + 10) for c in rearrange)
        if int(chiffres) % 97 == 1:
            return True
    return False


_SYNDICAT = re.compile(r'\b(?:cgt|cfdt|fo|cfe[\W_]*cgc|cftc|unsa|sud|solidaires|fsu|force\s+ouvriere)\b')
_APPARTENANCE = re.compile(r'\b(?:adher\w*|adhesion\w*|syndiqu\w*|membres?|cartes?|encart\w*|militant\w*|delegu\w*|cotis\w*)\b')


def _appartenance_syndicale(texte: str) -> bool:
    # Même proposition, au plus six mots intercalés, dans les deux sens.
    for proposition in re.split(r'[.;!?\n]', texte):
        for syndicat in _SYNDICAT.finditer(proposition):
            for appartenance in _APPARTENANCE.finditer(proposition):
                gauche, droite = sorted([syndicat, appartenance], key=lambda m: m.start())
                if len(re.findall(r'\w+', proposition[gauche.end():droite.start()])) <= 6:
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
    # « Traitement » et « diagnostic » sont ambigus ; les termes médicaux,
    # au singulier comme au pluriel, portent la catégorie de santé.
    if MOTIFS[4].search(texte):
        return 'une information de santé'
    # « prie de » suivi d'un infinitif est une formule de politesse.
    contexte = re.sub(
        r'\bprie\s+de\s+(?:(?:bien|ne|pas|vous|nous|le|la|les|lui|leur|me|te|se)\s+)*'
        r'[a-z]+(?:er|ir|re)\b', '', texte
    )
    contexte = re.sub(r'\bparti(?:e|s|es)?\s+(?=en\b)', '', contexte)
    categories = ('une origine ethnique ou raciale', 'une opinion politique',
                  'une conviction religieuse ou philosophique', 'une appartenance syndicale',
                  'une donnée génétique ou biométrique', 'une information de vie sexuelle')
    for motif_categorie, categorie in zip(MOTIFS[5:], categories, strict=True):
        if motif_categorie.search(contexte):
            return categorie
    if _appartenance_syndicale(texte):
        return 'une appartenance syndicale'
    if _contient_iban(valeur):
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
