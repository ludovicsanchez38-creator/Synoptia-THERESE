"""B-019 : la clé Gemini part dans un en-tête, jamais dans la chaîne de requête.

Trouvé le 02/09/2026. Gemini était le SEUL fournisseur dont la clé voyageait
en paramètre d'URL, sur deux sites : le flux de chat
(`params={"key": ..., "alt": "sse"}`) et la sonde de dérive du catalogue du
Board, dont le mode s'appelait même « query-key ». Les quatre autres
fournisseurs passent par un en-tête (`Authorization: Bearer` ou `x-api-key`).

Le filtre de journalisation masque bien `key=` : le risque n'est donc pas
dans les journaux de THÉRÈSE, mais partout où une URL circule sans être
filtrée - proxys, terminaisons TLS d'entreprise, outillage HTTP, rapports de
plantage. L'en-tête documenté par Google est `x-goog-api-key`.
"""

import json

import pytest


class _ReponseFluxFactice:
    def __init__(self, lignes: list[str], status: int = 200):
        self.status_code = status
        self._lignes = lignes

    def raise_for_status(self) -> None:
        pass

    async def aiter_lines(self):
        for ligne in self._lignes:
            yield ligne


class _ClientFluxFactice:
    """Capture la requête au lieu de la faire partir."""

    def __init__(self, lignes: list[str]):
        self._reponse = _ReponseFluxFactice(lignes)
        self.requetes: list[dict] = []

    def stream(self, method, url, **kwargs):
        self.requetes.append({"method": method, "url": url, **kwargs})
        reponse = self._reponse

        class _CM:
            async def __aenter__(_s):
                return reponse

            async def __aexit__(_s, *a):
                return False

        return _CM()


def _fournisseur_gemini(client, cle="AIzaSy-CLE-DE-TEST"):
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.gemini import GeminiProvider

    return GeminiProvider(
        LLMConfig(provider=LLMProvider.GEMINI, model="gemini-3.7-flash", api_key=cle),
        client=client,
    )


@pytest.mark.asyncio
async def test_le_flux_de_chat_envoie_la_cle_en_entete():
    corps = {
        "candidates": [{"content": {"parts": [{"text": "bonjour"}]}}],
        "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 2},
    }
    client = _ClientFluxFactice([f"data: {json.dumps(corps)}", ""])

    evenements = [
        evenement
        async for evenement in _fournisseur_gemini(client).stream(
            None, [{"role": "user", "parts": [{"text": "salut"}]}]
        )
    ]
    assert any(e.type == "done" for e in evenements)

    requete = client.requetes[-1]
    entetes = requete.get("headers") or {}
    parametres = requete.get("params") or {}

    assert entetes.get("x-goog-api-key") == "AIzaSy-CLE-DE-TEST", (
        "la clé doit voyager dans l'en-tête documenté par Google"
    )
    assert "key" not in parametres, (
        f"la clé est revenue dans la chaîne de requête : {parametres}"
    )
    assert "AIzaSy-CLE-DE-TEST" not in str(requete["url"]), (
        "la clé ne doit apparaître nulle part dans l'URL"
    )
    # Le reste du contrat de la requête ne bouge pas.
    assert parametres.get("alt") == "sse"


class _ClientSondeFactice:
    """Client de la sonde du Board : enregistre en-têtes ET paramètres."""

    def __init__(self, payload):
        self.payload = payload
        self.appels: list[dict] = []

    async def get(self, url, headers=None, timeout=None, params=None):
        self.appels.append({"url": url, "headers": headers or {}, "params": params or {}})

        payload = self.payload

        class _Reponse:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return payload

        return _Reponse()


@pytest.mark.asyncio
async def test_la_sonde_du_board_envoie_la_cle_en_entete(monkeypatch):
    from app.services import board as board_module

    monkeypatch.setattr(board_module, "_etat_catalogue", {})
    monkeypatch.setattr(board_module, "_date_derniere_sonde", None)
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy-CLE-SONDE")
    for var in ("ANTHROPIC_API_KEY", "XAI_API_KEY", "MISTRAL_API_KEY",
                "OPENAI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    client = _ClientSondeFactice({"models": [{"name": "models/gemini-3.7-flash"}]})
    await board_module.sonder_catalogue(client=client)

    assert len(client.appels) == 1, client.appels
    appel = client.appels[0]
    assert appel["headers"].get("x-goog-api-key") == "AIzaSy-CLE-SONDE"
    assert "key" not in appel["params"], appel["params"]
    assert "AIzaSy-CLE-SONDE" not in appel["url"]
    # La pagination large reste nécessaire (sinon fausse dérive, panel 0.48).
    assert appel["params"].get("pageSize") == 1000
