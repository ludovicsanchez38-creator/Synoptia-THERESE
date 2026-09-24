"""Neutralisation des formules de tableur, la même à l'import et à l'export.

B-1120 (arbitrage du 24/09/2026, docs/plans/2026-09-24-arbitrages-par-delegation.md) :
l'import désamorçait tout « + » ou « - » en tête, et abîmait « +33 6 12 34 56 78 »
ou un budget « -500 » ; l'export laissait passer « +1+cmd|' /C calc'!A0 », parce
qu'un chiffre suit le « + ». Une seule règle désormais : « = », « @ »,
tabulation, retour chariot ou saut de ligne en tête sont toujours désamorcés ;
« + » et « - » ne le sont que si la valeur n'a pas la forme d'un nombre ou d'un
téléphone (chiffres, espaces, points, tirets, barres obliques, parenthèses).
Le désamorçage est l'apostrophe en tête, convention des tableurs.
"""

import re

_TOUJOURS_UNE_FORMULE = frozenset("=@\t\r\n")
_NOMBRE_OU_TELEPHONE = re.compile(r"[+\-][\d\s().\-/]*")


def est_une_formule(texte: str) -> bool:
    """Vrai si un tableur pourrait interpréter `texte` comme une formule."""
    if not texte:
        return False
    if texte[0] in _TOUJOURS_UNE_FORMULE:
        return True
    if texte[0] in "+-":
        return _NOMBRE_OU_TELEPHONE.fullmatch(texte) is None
    return False


def neutraliser_formule(texte: str) -> str:
    """Préfixe `texte` d'une apostrophe s'il pourrait être lu comme une formule."""
    return "'" + texte if est_une_formule(texte) else texte
