"""
J2 (31/07/2026) - Filtrer par périmètre ne doit pas effacer l'existant.

Le filtre de `QdrantService.search` compare `scope` à une valeur littérale.
Or tous les documents indexés AVANT cette version n'ont aucune clé `scope`
dans leur payload : elle n'était écrite nulle part.

Conséquence si on branche le filtre naïvement : dès qu'une recherche est
cloisonnée, la totalité de l'index existant devient invisible. L'utilisateur
verrait sa mémoire documentaire disparaître d'un coup, sans rien avoir
supprimé — et le plan 0.42 interdit explicitement toute purge ou
réindexation silencieuse.

Un payload sans périmètre doit donc être traité comme global.
"""
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def service(monkeypatch):
    """Un service branché sur un client factice, pour inspecter le filtre émis."""
    from app.services import qdrant as module

    monkeypatch.setattr(module, "embed_text", lambda _t: [0.0] * 768)

    service = module.QdrantService.__new__(module.QdrantService)
    # `client` est une propriété en lecture seule qui instancie le vrai client :
    # on alimente l'attribut privé sur lequel elle s'appuie.
    faux_client = MagicMock()
    faux_client.query_points.return_value = MagicMock(points=[])
    service._client = faux_client
    service._initialized = True
    return service


def _filtre_emis(service) -> dict:
    """Le filtre passé à Qdrant, en structure — surtout PAS son `repr`.

    Piège rencontré en écrivant ces tests : chercher « IsEmpty » dans le `repr`
    d'un modèle pydantic passe TOUJOURS, parce que la représentation liste aussi
    les champs laissés à `None`. Le test était vert avec le code non corrigé.
    """
    appel = service.client.query_points.call_args
    filtre = appel.kwargs.get("query_filter")
    return {} if filtre is None else filtre.model_dump(exclude_none=True)


def _branches_de_perimetre(filtre: dict) -> list[dict]:
    """Les alternatives acceptées par la cloison de périmètre."""
    for condition in filtre.get("must", []):
        if "should" in condition:
            return condition["should"]
    return []


class TestUnPayloadSansPerimetreResteVisible:
    def test_la_recherche_cloisonnee_accepte_les_documents_sans_perimetre(self, service):
        service.search(query="rapport", scope="project", scope_id="projet-alpha")

        branches = _branches_de_perimetre(_filtre_emis(service))
        assert any("is_empty" in branche for branche in branches), (
            "le filtre ne prévoit aucune branche pour les payloads sans clé "
            "`scope` : tous les documents indexés avant cette version "
            "deviendraient invisibles dès qu'une recherche est cloisonnée"
        )

    def test_le_perimetre_demande_est_bien_transmis(self, service):
        service.search(query="rapport", scope="project", scope_id="projet-alpha")

        branches = _branches_de_perimetre(_filtre_emis(service))
        attendues = {
            ("scope", "project"),
            ("scope_id", "projet-alpha"),
            ("scope", "global"),
        }
        trouvees = set()
        for branche in branches:
            for condition in branche.get("must", [branche]):
                cle = condition.get("key")
                valeur = (condition.get("match") or {}).get("value")
                if cle is not None:
                    trouvees.add((cle, valeur))

        assert attendues <= trouvees, f"cloison incomplète, trouvé : {trouvees}"

    def test_sans_perimetre_demande_aucun_filtre_de_perimetre(self, service):
        """Ne pas cloisonner par accident une recherche qui ne l'a pas demandé."""
        service.search(query="rapport")

        assert _branches_de_perimetre(_filtre_emis(service)) == [], (
            "une recherche sans périmètre demandé ne doit poser aucune cloison"
        )
