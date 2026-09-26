"""B-1496 : l'outil search_memory du pont MCP appelait en GET une route qui
n'existe qu'en POST (`POST /api/memory/search`) : il échouait à chaque appel.
Chaque outil exposé doit viser une route que l'application sert avec cette
méthode."""

import re


def _gabarit(chemin: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", chemin)


def test_chaque_outil_du_pont_vise_une_route_servie():
    from app.main import app
    from app.services.mcp_therese_server import TOOL_ROUTES

    servies = {
        (methode, _gabarit(route.path))
        for route in app.routes
        for methode in (getattr(route, "methods", None) or ())
    }
    manquantes = {
        outil: (methode, chemin)
        for outil, (methode, chemin) in TOOL_ROUTES.items()
        if (methode, _gabarit(chemin)) not in servies
    }
    assert manquantes == {}
