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

from pathlib import Path

PROVIDERS = Path(__file__).resolve().parents[1] / "src/backend/app/services/providers"


def test_les_fournisseurs_lisent_le_corps_avant_de_le_journaliser():
    fautifs: list[str] = []
    for fichier in sorted(PROVIDERS.glob("*.py")):
        lignes = fichier.read_text(encoding="utf-8").split("\n")
        for i, ligne in enumerate(lignes):
            if "response.text" not in ligne:
                continue
            avant = "\n".join(lignes[max(0, i - 6) : i])
            if "aread()" not in avant:
                fautifs.append(f"{fichier.name}:{i + 1}")
    assert fautifs == [], (
        f"détail d'erreur lu sans aread() : {fautifs}. Sur une réponse en flux, "
        "le détail restera vide et le refus du fournisseur sera indiagnosticable."
    )
