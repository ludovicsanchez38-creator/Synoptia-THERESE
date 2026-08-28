"""
Aucune lecture de fichier ne doit dépendre de l'encodage de la machine.

Trouvé à la release 0.54.0, sur un workflow que je n'avais jamais regardé :
`tests-windows.yml` était ROUGE sur chacun de mes commits de la journée, et
l'était déjà avant. La cause tient en une ligne :

    SOURCE = Path("src/backend/app/routers/chat.py").read_text()

Sans `encoding`, Python retient l'encodage par défaut de la plateforme :
UTF-8 sur macOS et Linux, cp1252 sur Windows. Le fichier lu contient un
emoji (⚠️, octet 0x8f en dernière position UTF-8), indécodable en cp1252 -
donc une erreur de COLLECTE, pas un test qui échoue : toute la suite Windows
tombait d'un coup.

Deux leçons :
- un test vert sur ma machine ne dit rien de la plateforme d'en face ;
- surtout : « mes six gates locaux sont verts » n'est pas « la CI est verte ».
  J'ai livré la 0.53.0 avec ce workflow rouge, sans le voir.
"""

from pathlib import Path

RACINE = Path(__file__).parent


class TestAucuneLectureNeDependDeLaPlateforme:
    def test_aucun_read_text_sans_encodage(self):
        fautes = []
        for fichier in sorted(RACINE.rglob("test_*.py")):
            if fichier.name == Path(__file__).name:
                continue
            for numero, ligne in enumerate(
                fichier.read_text(encoding="utf-8").splitlines(), 1
            ):
                if ".read_text()" in ligne:
                    fautes.append(f"{fichier.name}:{numero}")
        assert fautes == [], (
            "read_text() sans encodage retient cp1252 sous Windows et casse "
            f"la collecte entière : {fautes}"
        )

    def test_aucun_open_sans_encodage(self):
        fautes = []
        for fichier in sorted(RACINE.rglob("test_*.py")):
            if fichier.name == Path(__file__).name:
                continue
            texte = fichier.read_text(encoding="utf-8")
            for numero, ligne in enumerate(texte.splitlines(), 1):
                nu = ligne.strip()
                if nu.startswith("#") or "encoding" in ligne:
                    continue
                # `open(x)` et `open(x, "r")` en lecture texte, pas `open(x, "rb")`
                # Une ouverture BINAIRE n'a pas d'encodage : "rb", "wb", "ab"…
                binaire = any(f'{q}{m}{q}' in ligne for q in "\"'" for m in ("rb", "wb", "ab", "r+b", "w+b"))
                if "open(" in ligne and not binaire:
                    if "io.open(" in ligne or "= open(" in ligne or "with open(" in ligne:
                        fautes.append(f"{fichier.name}:{numero}")
        assert fautes == [], f"ouverture texte sans encodage explicite : {fautes}"
