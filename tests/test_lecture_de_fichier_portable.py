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

import ast
from pathlib import Path

RACINE = Path(__file__).parent


class TestAucuneLectureNeDependDeLaPlateforme:
    """
    Les deux gates lisent l'ARBRE SYNTAXIQUE, pas le texte.

    Premier jet : une recherche de sous-chaîne. Elle signalait la prose de sa
    propre docstring et celle du gate voisin, qui citent les motifs qu'ils
    traquent. Un gate qui confond un mot et un appel finit par être désarmé
    pour avoir crié à tort.
    """

    # `tarfile.open`, `zipfile.open`, `gzip.open` s'appellent aussi « open »
    # et n'ont pas d'encodage TEXTE : les viser ferait crier le gate à tort,
    # et un gate qui crie à tort finit désarmé.
    OUVREURS_DARCHIVE = {"tarfile", "zipfile", "gzip", "bz2", "lzma", "shutil"}

    @classmethod
    def _appels(cls, fichier: Path, nom: str) -> list[ast.Call]:
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
        trouves = []
        for n in ast.walk(arbre):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Name) and n.func.id == nom:
                trouves.append(n)
            elif isinstance(n.func, ast.Attribute) and n.func.attr == nom:
                recepteur = n.func.value
                if (
                    isinstance(recepteur, ast.Name)
                    and recepteur.id in cls.OUVREURS_DARCHIVE
                ):
                    continue
                trouves.append(n)
        return trouves

    def test_aucun_read_text_sans_encodage(self):
        fautes = []
        for fichier in sorted(RACINE.rglob("test_*.py")):
            for appel in self._appels(fichier, "read_text"):
                if not any(kw.arg == "encoding" for kw in appel.keywords):
                    fautes.append(f"{fichier.name}:{appel.lineno}")
        assert fautes == [], (
            "read_text() sans encodage retient cp1252 sous Windows et casse "
            f"la collecte entière : {fautes}"
        )

    def test_aucun_open_sans_encodage(self):
        binaire = {"rb", "wb", "ab", "r+b", "w+b", "rb+", "wb+"}
        fautes = []
        for fichier in sorted(RACINE.rglob("test_*.py")):
            for appel in self._appels(fichier, "open"):
                mode = ""
                if len(appel.args) > 1 and isinstance(appel.args[1], ast.Constant):
                    mode = str(appel.args[1].value)
                for kw in appel.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if mode in binaire:
                    continue  # une ouverture binaire n'a pas d'encodage
                if not any(kw.arg == "encoding" for kw in appel.keywords):
                    fautes.append(f"{fichier.name}:{appel.lineno}")
        assert fautes == [], f"ouverture texte sans encodage explicite : {fautes}"
