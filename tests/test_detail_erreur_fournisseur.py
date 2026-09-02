"""Le corps d'une erreur HTTP doit arriver dans les journaux.

Le 28/08/2026, un 400 d'OpenAI a coûté un aller-retour de diagnostic parce que
le log ne portait que le code. Un correctif a ajouté `e.response.text[:500]`.

Il n'a JAMAIS fonctionné. Les réponses sont demandées en FLUX
(`client.stream(...)`), et sur une réponse en flux non lue, `.text` lève
`httpx.ResponseNotRead`. Le `contextlib.suppress(Exception)` avalait
l'exception et laissait le détail vide. Le 30/08, un 400 déclenché en joignant
un tableur au chat a produit exactement le même log muet, deux jours après le
« correctif » censé l'éviter.

Vérifié à la main contre un vrai serveur :

    async with client.stream('GET', '.../status/400') as r:
        r.raise_for_status()          # lève HTTPStatusError
        e.response.text               # -> ResponseNotRead
        await e.response.aread()      # puis .text porte le corps

`httpx.MockTransport` ne reproduit PAS ce comportement : il rend une réponse
déjà lue, donc un test bâti dessus passe quoi qu'on fasse. D'où une garantie
STATIQUE, qui elle mord.
"""

import ast
from pathlib import Path

PROVIDERS = Path(__file__).resolve().parents[1] / "src/backend/app/services/providers"


def _lignes_d_appel_aread(source: str) -> set[int]:
    """Numéros de ligne portant un VRAI appel `.aread()`.

    B-045 : le mot ne suffit pas. Le commentaire d'openrouter.py contient
    « sans aread() », juste au-dessus de l'appel qu'il explique — une garde
    textuelle restait donc verte si l'appel disparaissait et que le commentaire
    survivait. On demande à l'AST où l'appel a lieu réellement.
    """
    try:
        arbre = ast.parse(source)
    except SyntaxError:  # pragma: no cover - un provider illisible se voit ailleurs
        return set()
    lignes: set[int] = set()
    for noeud in ast.walk(arbre):
        if (
            isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Attribute)
            and noeud.func.attr == "aread"
        ):
            lignes.update(range(noeud.lineno, (noeud.end_lineno or noeud.lineno) + 1))
    return lignes


def _detail_lu_sans_aread(source: str, nom: str) -> list[str]:
    """Lectures de `response.text` sans appel `aread()` dans les six lignes du dessus."""
    fautifs: list[str] = []
    appels = _lignes_d_appel_aread(source)
    for i, ligne in enumerate(source.split("\n")):
        if "response.text" not in ligne:
            continue
        # Les six lignes qui précèdent, en numérotation 1-based.
        if not appels.intersection(range(max(1, i - 5), i + 1)):
            fautifs.append(f"{nom}:{i + 1}")
    return fautifs


def test_le_gate_exige_l_appel_et_non_le_mot():
    """B-045 : le commentaire qui explique `aread()` contenait le mot.

    Dans openrouter.py, le commentaire posé juste au-dessus de l'appel dit
    littéralement « sans aread(), .text lève ResponseNotRead ». Une garde qui
    cherche cette chaîne dans les lignes précédentes est donc satisfaite par le
    seul commentaire : l'appel peut disparaître sans que rien ne rougisse.
    """
    sans_appel = (
        "async def stream(self):\n"
        "    try:\n"
        "        pass\n"
        "    except httpx.HTTPStatusError as erreur:\n"
        "        response = erreur.response\n"
        "        # Reponse en FLUX : sans aread(), .text leve ResponseNotRead\n"
        "        # et le detail du refus reste vide.\n"
        "        error_body = response.text\n"
    )
    assert _detail_lu_sans_aread(sans_appel, "faux.py") != [], (
        "un commentaire qui NOMME aread() suffisait à satisfaire la garde : "
        "l'appel réel peut disparaître sans que le gate rougisse"
    )

    avec_appel = sans_appel.replace(
        "        error_body = response.text\n",
        "        await response.aread()\n        error_body = response.text\n",
    )
    assert _detail_lu_sans_aread(avec_appel, "faux.py") == [], (
        "un vrai appel `await response.aread()` doit satisfaire la garde"
    )


def test_les_fournisseurs_lisent_le_corps_avant_de_le_journaliser():
    fautifs: list[str] = []
    for fichier in sorted(PROVIDERS.glob("*.py")):
        fautifs += _detail_lu_sans_aread(
            fichier.read_text(encoding="utf-8"), fichier.name
        )
    assert fautifs == [], (
        f"détail d'erreur lu sans aread() : {fautifs}. Sur une réponse en flux, "
        "le détail restera vide et le refus du fournisseur sera indiagnosticable."
    )
