"""B-086 — la sonde /health juge Qdrant sur une mesure fraîche.

`/health` ne sondait que la base et lisait Qdrant dans le singleton
`ServiceStatus`, dont la valeur peut dater de n'importe quand (ou ne jamais
avoir été écrite). Sa voisine `/health/services` interroge Qdrant en direct :
les deux routes pouvaient donc se contredire, et le commentaire du fichier
annonçait pourtant que le verdict reposait sur une mesure réelle.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def statuts_isoles():
    """`ServiceStatus._statuses` est un dictionnaire de CLASSE, partagé par tout
    le processus : sans restauration, l'état semé ici fuirait dans les autres
    fichiers de tests."""
    from app.services.error_handler import get_service_status

    statuts = get_service_status()
    memoire = dict(statuts._statuses)
    yield statuts
    statuts._statuses.clear()
    statuts._statuses.update(memoire)


def _service_qdrant(en_panne: bool) -> MagicMock:
    faux = MagicMock()
    if en_panne:
        faux.get_stats.side_effect = RuntimeError("Qdrant injoignable")
    else:
        faux.get_stats.return_value = {"points_count": 0, "status": "green"}
    return faux


@pytest.mark.asyncio
async def test_health_ne_croit_pas_un_qdrant_disponible_perime(client, statuts_isoles):
    """Qdrant marqué disponible dans le singleton, mais réellement en panne."""
    statuts_isoles.set_available("qdrant", True)

    with patch(
        "app.services.qdrant.get_qdrant_service", return_value=_service_qdrant(en_panne=True)
    ):
        reponse = await client.get("/health")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["services"]["qdrant"] is False, (
        "/health a rendu l'état mémorisé au lieu de sonder Qdrant"
    )
    assert corps["status"] == "degraded"


@pytest.mark.asyncio
async def test_health_ne_croit_pas_un_qdrant_indisponible_perime(client, statuts_isoles):
    """Le sens inverse : un échec ancien ne condamne pas un Qdrant revenu.

    C'est la direction coûteuse — une panne passagère laissait `/health` sur
    « degraded » jusqu'au prochain appel de `/health/services`.
    """
    statuts_isoles.set_available("qdrant", False)

    with patch(
        "app.services.qdrant.get_qdrant_service", return_value=_service_qdrant(en_panne=False)
    ):
        reponse = await client.get("/health")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["services"]["qdrant"] is True, (
        "/health a rendu l'échec mémorisé au lieu de sonder Qdrant"
    )


@pytest.mark.asyncio
async def test_les_deux_sondes_saccordent_sur_qdrant(client, statuts_isoles):
    """/health et /health/services rendent le même verdict au même instant."""
    statuts_isoles.set_available("qdrant", True)

    with patch(
        "app.services.qdrant.get_qdrant_service", return_value=_service_qdrant(en_panne=True)
    ):
        globale = (await client.get("/health")).json()
        detaillee = (await client.get("/health/services")).json()

    assert globale["services"]["qdrant"] == detaillee["services"]["qdrant"]["available"]
