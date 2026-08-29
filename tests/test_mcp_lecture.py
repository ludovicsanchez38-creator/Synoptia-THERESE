"""
La porte MCP, en lecture seule et sans jumeau (tranche D du 29/08).

Deux défauts mesurés avant ce lot :

1. `get_contact` (MCP) passait par `GET /api/memory/contacts/{id}` et rendait
   `ContactResponse` — donc le bloc `notes`, SANS les activités. Le chat voyait
   les traces, l'agent MCP ne voyait que le résumé périmé. Deux portes, deux
   vérités, et c'est la porte la plus pauvre qui affirmait le plus fort.
2. `list_contacts` pagine à 50 en HTTP 200. Sur les 74 contacts de Ludo, 24
   disparaissaient sans que rien ne le dise.

L'écriture reste refusée. Piloter, c'est écrire ; écrire, c'est décider qui de
Twenty ou de THÉRÈSE fait foi. Ce n'est pas une route, c'est une décision.
"""
import pytest
from app.services.mcp_therese_server import (
    MUTATING_TOOLS,
    TOOL_ROUTES,
    TOOLS,
    execute_tool,
)


def test_seuls_des_outils_de_lecture_sont_exposes():
    exposes = {t["name"] for t in TOOLS}
    assert exposes & MUTATING_TOOLS == set(), (
        "aucun outil d'écriture ne doit apparaître dans tools/list"
    )
    assert "get_contact" in exposes


@pytest.mark.asyncio
async def test_l_ecriture_est_refusee_avec_son_motif():
    for outil in sorted(MUTATING_TOOLS):
        reponse = await execute_tool(outil, {})
        assert "error" in reponse, f"{outil} ne doit pas s'exécuter"
        assert "lecture" in reponse["error"].lower()


def test_get_contact_pointe_sur_la_route_du_contrat():
    """Le jumeau se ferme ici : l'agent et le chat lisent la MÊME route.

    LIMITE de ce test : `execute_tool` fait un vrai appel HTTP vers le backend
    local, donc on ne peut pas l'exécuter en test unitaire. On vérifie ce qui
    est vérifiable — la cible — et le contrat lui-même est testé sur la route,
    juste en dessous.
    """
    methode, chemin = TOOL_ROUTES["get_contact"]

    assert methode == "GET"
    assert chemin.endswith("/fiche"), (
        "get_contact doit lire la fiche selon le contrat, pas ContactResponse"
    )


@pytest.mark.asyncio
async def test_la_route_du_contrat_rend_l_etat_les_traces_et_la_consigne(client):
    """Ce que l'agent recevra réellement.

    Sans ça, le MCP rendait le résumé manuscrit seul, sans les traces qui le
    contredisent ni la consigne qui interdit de trancher : la porte la plus
    pauvre affirmait le plus fort.
    """
    fiche = (await client.post("/api/memory/contacts", json={
        "first_name": "Nathalie", "last_name": "Esmieu", "notes": "FORGER 490 EUR",
    })).json()

    reponse = await client.get(f"/api/memory/contacts/{fiche['id']}/fiche")
    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()

    assert charge["etat_courant"] is None, "aucune prestation posée : pas d'état"
    assert "traces" in charge and "consigne" in charge
    assert "notes" not in charge, "le résumé manuscrit ne doit pas voyager comme un fait"
    assert any("FORGER" in (t.get("texte") or "") for t in charge["traces"]), (
        "il reste lisible, comme une trace"
    )


@pytest.mark.asyncio
async def test_la_route_du_contrat_refuse_un_contact_inconnu(client):
    assert (await client.get("/api/memory/contacts/inconnu-42/fiche")).status_code == 404


def test_la_limite_de_pagination_est_ecrite_dans_l_outil():
    """Une troncature silencieuse fait dire à l'agent « tu as N contacts »
    avec N faux. C'est le piège déjà documenté côté Twenty : un `limit=300`
    qui rend 200 en HTTP 200 avait masqué 78 opportunités.

    On ne peut pas empêcher la troncature ici (la route est partagée avec
    l'interface) : on la DIT, dans la description que le modèle lit.
    """
    outil = next(t for t in TOOLS if t["name"] == "list_contacts")

    description = outil["description"].lower()
    assert "limit" in description or "limite" in description
    assert any(mot in description for mot in ("tronqu", "partiel", "tout")), (
        "la description doit avertir que la liste peut être incomplète"
    )
