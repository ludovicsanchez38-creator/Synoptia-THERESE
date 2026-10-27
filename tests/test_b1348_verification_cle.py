"""B-1348 (boucle DQ) : une clé d'IA fausse n'est plus annoncée « configurée ».

Audit bêta du 27/10/2026 (A2-23, A2-42) : la mise en route ne contrôlait que le
préfixe ; « Clé API configurée » s'affichait pour n'importe quelle clé au bon
format, et l'échec n'arrivait qu'au premier message. La clé est maintenant
vérifiée auprès du fournisseur (liste des modèles) juste après l'enregistrement.
"""
import json

import httpx
import pytest
from app.services import verification_cle
from app.services.verification_cle import message_verification, verifier_cle

CLE = "sk-ant-api03-cle-de-test-0123456789"


def _client(code: int, corps=b"{}", vu: list | None = None, panne: Exception | None = None):
    def repondre(requete: httpx.Request) -> httpx.Response:
        if vu is not None:
            vu.append(requete)
        if panne:
            raise panne
        contenu = corps if isinstance(corps, bytes) else json.dumps(corps).encode()
        return httpx.Response(code, content=contenu)

    return httpx.AsyncClient(transport=httpx.MockTransport(repondre))


@pytest.mark.asyncio
@pytest.mark.parametrize("fournisseur,code,corps,attendu", [
    ("anthropic", 200, {"data": []}, "acceptee"),
    ("anthropic", 401, {"error": {"type": "authentication_error"}}, "refusee"),
    ("openai", 401, {}, "refusee"),
    ("mistral", 403, {}, "refusee"),
    ("anthropic", 400, {"error": {"type": "invalid_request_error", "message": "This API key is not scoped to a workspace, so…"}}, "non_rattachee"),
    ("gemini", 400, {"error": {"status": "INVALID_ARGUMENT", "details": [{"reason": "API_KEY_INVALID"}]}}, "refusee"),
    ("gemini", 200, {"models": []}, "acceptee"),
    ("anthropic", 402, {"error": {"type": "billing_error"}}, "paiement"),
    ("grok", 429, {}, "limite"),
    ("anthropic", 500, {}, "incertaine"),
    ("openai", 400, b"pas du json", "incertaine"),
])
async def test_les_reponses_du_fournisseur_sont_classees(fournisseur, code, corps, attendu):
    assert await verifier_cle(fournisseur, CLE, _client(code, corps)) == attendu


@pytest.mark.asyncio
async def test_la_requete_ne_genere_rien_et_porte_la_cle_dans_l_en_tete():
    vu: list = []
    await verifier_cle("anthropic", CLE, _client(200, vu=vu))
    (requete,) = vu
    assert requete.method == "GET" and requete.url.path == "/v1/models"
    assert requete.headers["x-api-key"] == CLE and CLE not in str(requete.url)


@pytest.mark.asyncio
async def test_un_fournisseur_injoignable_ne_fait_pas_echouer_l_enregistrement():
    panne = httpx.ConnectError("réseau coupé")
    assert await verifier_cle("openai", CLE, _client(200, panne=panne)) == "injoignable"


@pytest.mark.asyncio
@pytest.mark.parametrize("fournisseur,cle", [("deepseek", CLE), ("ollama", CLE), ("anthropic", None), ("anthropic", "")])
async def test_sans_sonde_ou_sans_cle_rien_n_est_affirme(fournisseur, cle):
    vu: list = []
    assert await verifier_cle(fournisseur, cle, _client(200, vu=vu)) == "non_verifiable"
    assert vu == []


def test_chaque_etat_a_une_phrase_sans_la_cle():
    for etat in verification_cle.ETATS:
        phrase = message_verification(etat, "Anthropic")
        assert phrase and CLE not in phrase and "sk-ant" not in phrase
    assert "copié toute la clé" in message_verification("refusee", "Anthropic")
    assert "espace de travail" in message_verification("non_rattachee", "Anthropic")


@pytest.mark.asyncio
async def test_la_route_verifie_la_cle_enregistree_sans_la_renvoyer(client, monkeypatch):
    import app.services.llm as llm

    monkeypatch.setattr(llm, "_get_api_key_from_db", lambda fournisseur: CLE if fournisseur == "anthropic" else None)
    monkeypatch.setattr(verification_cle, "creer_client", lambda: _client(401))

    reponse = await client.post("/api/config/api-key/verifier", json={"provider": "anthropic"})

    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["etat"] == "refusee" and "Anthropic refuse cette clé" in donnees["message"]
    assert CLE not in reponse.text


@pytest.mark.asyncio
async def test_la_route_refuse_un_fournisseur_inconnu(client):
    reponse = await client.post("/api/config/api-key/verifier", json={"provider": "inconnu"})
    assert reponse.status_code == 400
