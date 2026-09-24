"""B-1184 : les tests du filtre vectoriel de test_scope_contacts.py rétablissent
`app.services.qdrant.embed_text` (règle B-597 : une substitution d'attribut de
module passe par monkeypatch).

On joue chaque méthode telle quelle, avec son propre monkeypatch défait
ensuite comme le ferait pytest, puis on lit l'attribut du module.
"""

import inspect

import pytest
from _pytest.monkeypatch import MonkeyPatch


def _classe_qui_porte(methode: str) -> type:
    import tests.test_scope_contacts as module_de_test

    for valeur in vars(module_de_test).values():
        if isinstance(valeur, type) and hasattr(valeur, methode):
            return valeur
    raise AssertionError(f"{methode} introuvable dans test_scope_contacts.py")


@pytest.mark.parametrize(
    "methode",
    [
        "test_le_filtre_accepte_le_perimetre_de_conversation",
        "test_le_filtre_vectoriel_cloisonne_aussi_le_mode_transversal",
    ],
)
def test_embed_text_retabli_apres_le_test(monkeypatch, methode):
    from app.services import qdrant as module

    original = module.embed_text
    monkeypatch.setattr(module, "embed_text", original)  # filet pour ce test-ci
    fonction = getattr(_classe_qui_porte(methode)(), methode)
    patch_du_test = MonkeyPatch()
    try:
        if "monkeypatch" in inspect.signature(fonction).parameters:
            fonction(monkeypatch=patch_du_test)
        else:
            fonction()
    finally:
        patch_du_test.undo()
    assert module.embed_text is original, f"{methode} laisse embed_text remplacé"
