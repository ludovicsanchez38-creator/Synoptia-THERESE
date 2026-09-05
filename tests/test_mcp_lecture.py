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
import json

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


#: Ce qui vaut AVERTISSEMENT de troncature dans une description d'outil.
#: B-083 : le critère contenait « tout », satisfait par « toutes » — donc par
#: « renvoie toutes les colonnes », qui promet l'EXHAUSTIVITÉ, le contraire
#: exact de l'avertissement recherché. Il ne reste que des racines dont
#: aucune ne s'obtient par un mot de sens inverse.
_RACINES_D_AVERTISSEMENT = ("tronqu", "partiel", "incomplet", "peut manquer")


def _avertit_de_la_troncature(description: str) -> bool:
    """La description prévient-elle que la liste peut être incomplète ?"""
    minuscules = description.lower()
    return any(racine in minuscules for racine in _RACINES_D_AVERTISSEMENT)


def test_la_limite_de_pagination_est_ecrite_dans_l_outil():
    """Une troncature silencieuse fait dire à l'agent « tu as N contacts »
    avec N faux. C'est le piège déjà documenté côté Twenty : un `limit=300`
    qui rend 200 en HTTP 200 avait masqué 78 opportunités.

    On ne peut pas empêcher la troncature ici (la route est partagée avec
    l'interface) : on la DIT, dans la description que le modèle lit.
    """
    outil = next(t for t in TOOLS if t["name"] == "list_contacts")

    description = outil["description"].lower()
    # « limite » contient déjà « limit » : la seconde branche du `or` d'avant
    # était morte, et une branche morte ne garde rien.
    assert "limit" in description
    assert _avertit_de_la_troncature(description), (
        "la description doit avertir que la liste peut être incomplète"
    )


@pytest.mark.parametrize(
    "description",
    [
        # Le contre-exemple de B-083 : passait l'ancien critère par « toutes ».
        "Liste les contacts. Utilise limit pour paginer. Renvoie toutes les colonnes.",
        "Liste les contacts avec un paramètre limit.",
    ],
)
def test_une_description_sans_avertissement_est_refusee(description):
    """Le critère doit pouvoir dire NON, sinon il ne garde rien."""
    assert not _avertit_de_la_troncature(description), (
        "une description qui n'avertit pas de la troncature doit être refusée"
    )


# ============================================================
# B-022 : le garde-fou de lecture ne jugeait que le NOM de l'outil
# ============================================================


@pytest.mark.asyncio
async def test_le_parametre_de_chemin_ne_sort_pas_de_la_route(monkeypatch):
    """Un identifiant hostile ne doit pas atteindre une autre route de l'API.

    Trouvé le 02/09/2026 : le paramètre de chemin était collé par un
    `str.replace` sans encodage. Un `contact_id` valant `../../config/llm?x=`
    faisait deux choses à la fois : le `?` avalait le suffixe `/fiche` du
    gabarit, et httpx normalisait les `../` - l'agent atteignait n'importe
    quelle route GET de THÉRÈSE, liste blanche contournée.

    On intercepte l'appel HTTP : le test doit prouver la forme du chemin,
    jamais joindre un backend.
    """
    import app.services.mcp_therese_server as serveur

    captures: list[tuple[str, str]] = []

    async def _faux_appel(method, path, params=None, body=None):
        captures.append((method, path))
        return {}

    monkeypatch.setattr(serveur, "_call_therese_api", _faux_appel)

    evasions = [
        "../../config/llm?x=",
        "..%2f..%2fconfig/llm",
        "42?x=1",
        "../../data/backups#",
        "a/b",
    ]
    for outil, cle in (("get_contact", "contact_id"), ("get_project", "project_id")):
        _, gabarit = TOOL_ROUTES[outil]
        prefixe, suffixe = gabarit.split("{" + cle + "}")
        for valeur in evasions:
            captures.clear()
            await serveur.execute_tool(outil, {cle: valeur})
            assert len(captures) == 1
            methode, chemin = captures[0]
            assert methode == "GET"
            assert chemin.startswith(prefixe), (
                f"{outil}({valeur!r}) est sorti de la route : {chemin}"
            )
            assert chemin.endswith(suffixe), (
                f"{outil}({valeur!r}) a perdu le suffixe du gabarit : {chemin}"
            )
            segment = chemin[len(prefixe): len(chemin) - len(suffixe) or None]
            assert not any(caractere in segment for caractere in "/?#"), (
                f"{outil}({valeur!r}) a laissé un séparateur brut : {segment!r}"
            )


@pytest.mark.asyncio
async def test_le_parametre_de_chemin_ordinaire_reste_lisible(monkeypatch):
    """Aucun sur-blocage : un identifiant normal traverse tel quel."""
    import app.services.mcp_therese_server as serveur

    captures: list[str] = []

    async def _faux_appel(method, path, params=None, body=None):
        captures.append(path)
        return {}

    monkeypatch.setattr(serveur, "_call_therese_api", _faux_appel)

    await serveur.execute_tool(
        "get_contact", {"contact_id": "8a03f8ea-9679-49b1-86be-4802be6ed95e"}
    )
    assert captures == [
        "/api/memory/contacts/8a03f8ea-9679-49b1-86be-4802be6ed95e/fiche"
    ]


# ============================================================
# B-487 (05/09/2026) : un refus de l'API passait pour un résultat
# ============================================================


class _ReponseHTTP:
    def __init__(self, status: int, corps: dict):
        self.status_code = status
        self.is_success = 200 <= status < 300
        self._corps = corps
        self.text = json.dumps(corps)

    def json(self):
        return self._corps


class _ClientQuiRefuse:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, params=None, headers=None):
        return _ReponseHTTP(401, {"code": "UNAUTHORIZED", "message": "Jeton absent"})


@pytest.mark.asyncio
async def test_un_refus_de_l_api_est_rendu_comme_une_erreur(monkeypatch):
    """_call_therese_api rendait resp.json() sans regarder le code HTTP :
    un 401 « Jeton absent » arrivait à l'agent comme s'il s'agissait de la
    liste des contacts, et handle_request ne posait isError que sur une
    exception Python."""
    import app.services.mcp_therese_server as serveur

    monkeypatch.setattr(serveur.httpx, "AsyncClient", _ClientQuiRefuse)

    resultat = await serveur._call_therese_api("GET", "/api/memory/contacts")
    assert resultat.get("status") == 401
    assert "error" in resultat, resultat

    reponse = await serveur.handle_request(
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "list_contacts", "arguments": {}}}
    )
    assert reponse["result"].get("isError") is True, reponse
