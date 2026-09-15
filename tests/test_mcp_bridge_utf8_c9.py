"""B-818 (cycle 9) : le pont MCP décodait chaque bloc de 4096 octets seul ; un
caractère multi-octets coupé à la frontière levait UnicodeDecodeError sous
l'except qui fait break, et arrêtait le pont."""
from __future__ import annotations

from app.services.mcp_therese_server import DecodeurDeLignes


def test_un_accent_coupe_entre_deux_blocs_se_decode() -> None:
    ligne = '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"q":"été"}}\n'.encode()
    coupure = ligne.index("é".encode()) + 1  # au milieu des deux octets de « é »
    decodeur = DecodeurDeLignes()
    assert decodeur.ajouter(ligne[:coupure]) == []
    lignes = decodeur.ajouter(ligne[coupure:])
    assert lignes == [ligne.decode().strip()]


def test_les_lignes_vides_sont_ignorees_et_le_reste_attend() -> None:
    decodeur = DecodeurDeLignes()
    assert decodeur.ajouter(b"\n\n{\"a\":1}\n{\"b\"") == ['{"a":1}']
    assert decodeur.ajouter(b":2}\n") == ['{"b":2}']
