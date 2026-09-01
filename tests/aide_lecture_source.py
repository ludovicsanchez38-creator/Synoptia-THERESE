"""Mesurer un ordre dans du code, sans se laisser tromper par un commentaire.

01/09/2026. Deux tests garantissaient un ordre d'exécution avec
`source.index(A) < source.index(B)`. Or `str.index` rend la PREMIÈRE
occurrence, commentaires compris : un commentaire citant le verrou en tête de
fonction inversait la mesure sans qu'une ligne de code ne bouge, et un code
correct qui documente son verrou en préambule aurait fait échouer le test.

L'invariant protégé est un effacement RGPD — un profil supprimé que réécrirait
une indexation restée en attente. Une mesure qu'un commentaire renverse n'est
pas une garantie.

`ast.unparse(ast.parse(...))` reconstruit la source à partir de l'arbre : les
commentaires n'y survivent pas, le code oui.
"""

from __future__ import annotations

import ast
import textwrap


def code_sans_commentaires(source: str) -> str:
    """Le code seul, tel que l'interpréteur le voit."""
    return ast.unparse(ast.parse(textwrap.dedent(source)))


def ordre_dans_le_code(source: str, premier: str, second: str) -> bool:
    """Vrai si `premier` apparaît avant `second` dans le CODE, commentaires exclus.

    Lève si l'un des deux motifs est absent : un ordre entre deux choses dont
    l'une n'existe pas serait vrai par accident.
    """
    code = code_sans_commentaires(source)
    for motif in (premier, second):
        if motif not in code:
            raise AssertionError(
                f"motif absent du code (commentaires exclus) : {motif!r}"
            )
    return code.index(premier) < code.index(second)
