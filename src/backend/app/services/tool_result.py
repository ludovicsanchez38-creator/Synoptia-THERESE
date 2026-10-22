"""Texte compatible avec les anciens appelants, issue native distincte de la prose."""
from typing import Any


class ResultatOutil(str):
    issue: dict[str, Any]

    def __new__(cls, texte: str, issue: dict[str, Any]) -> 'ResultatOutil':
        resultat = super().__new__(cls, texte)
        resultat.issue = issue
        return resultat
