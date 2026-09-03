"""
La détection du modèle Ollama par défaut interroge l'adresse configurée.

**B-268.** `detect_default_ollama_model` (services/llm.py) portait
`http://localhost:11434` comme valeur par défaut de son paramètre, et tous ses
appelants l'appellent sans argument. Un backend configuré sur un autre serveur
Ollama - `OLLAMA_BASE_URL`, ou simplement un poste où l'on ne veut PAS
qu'Ollama soit interrogé - allait quand même lire les modèles installés
localement. `GET /api/config/llm` rendait alors le nom d'un modèle du poste
(mesuré : `gemma4-tia:latest`) sur un backend censé être sourd à Ollama, avec
`available: false` juste à côté.

Le nom d'un modèle installé n'est pas anodin : il dit ce que la personne fait
tourner sur sa machine, et il apparaît dans une réponse d'API.
"""

import httpx
import pytest

MODELE_DU_POSTE = "gemma4-tia:latest"


def _repondeur(hote_qui_repond: str):
    """Un Ollama qui ne répond QUE sur l'adresse donnée.

    Ailleurs, connexion refusée - exactement ce que fait un port fermé.
    """

    def _get(url, **_kwargs):
        if hote_qui_repond not in url:
            raise httpx.ConnectError(f"connexion refusée : {url}")
        return httpx.Response(
            200,
            json={"models": [{"name": MODELE_DU_POSTE}]},
            request=httpx.Request("GET", url),
        )

    return _get


def test_la_detection_interroge_l_adresse_configuree(monkeypatch):
    from app.config import settings
    from app.services import llm as service_llm

    interrogees: list[str] = []

    def _get(url, **_kwargs):
        interrogees.append(url)
        raise httpx.ConnectError("port fermé")

    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9")
    monkeypatch.setattr(httpx, "get", _get)

    assert (
        service_llm.detect_default_ollama_model(fallback="mistral-nemo")
        == "mistral-nemo"
    )
    assert interrogees == ["http://127.0.0.1:9/api/tags"], (
        "la détection est allée voir ailleurs que l'adresse configurée : "
        f"{interrogees}"
    )


def test_aucun_modele_du_poste_ne_remonte_quand_l_adresse_est_ailleurs(monkeypatch):
    """Le cas mesuré : Ollama tourne bien sur le poste (11434), mais le backend
    est configuré sur un port fermé. Le nom du modèle local ne doit pas
    ressortir."""
    from app.config import settings
    from app.services import llm as service_llm

    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9")
    monkeypatch.setattr(httpx, "get", _repondeur("11434"))

    detecte = service_llm.detect_default_ollama_model(fallback="mistral-nemo")
    assert detecte != MODELE_DU_POSTE, (
        "le nom d'un modèle du poste remonte alors que le backend est "
        "configuré ailleurs"
    )
    assert detecte == "mistral-nemo"


def test_l_adresse_passee_en_argument_reste_prioritaire(monkeypatch):
    """Le paramètre existe et doit garder la main : c'est ce qui permet de
    sonder un serveur donné sans toucher aux réglages."""
    from app.config import settings
    from app.services import llm as service_llm

    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9")
    monkeypatch.setattr(httpx, "get", _repondeur("10.0.0.7:11434"))

    assert (
        service_llm.detect_default_ollama_model(base_url="http://10.0.0.7:11434")
        == MODELE_DU_POSTE
    )


@pytest.mark.asyncio
async def test_la_route_de_configuration_ne_nomme_pas_un_modele_du_poste(
    client, monkeypatch
):
    """Le constat d'origine, sur la route que l'écran appelle."""
    from app.config import settings

    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9")
    monkeypatch.setattr(httpx, "get", _repondeur("11434"))

    await client.post(
        "/api/config/preferences",
        json={"key": "llm_provider", "value": "ollama", "category": "llm"},
    )

    reponse = await client.get("/api/config/llm")
    assert reponse.status_code == 200, reponse.text
    assert MODELE_DU_POSTE not in reponse.text, (
        "le nom d'un modèle installé sur le poste part dans la réponse d'API : "
        f"{reponse.text[:300]}"
    )
