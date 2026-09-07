"""B-444 (cycle 4) : un changement de gabarit DuckDuckGo rendait zéro résultat
sans erreur, indiscernable d'une recherche vide : l'assistante concluait « Aucun
résultat » là où la recherche était cassée. Une page sans le moindre marqueur
de résultat ni de « pas de résultat » est une recherche INDISPONIBLE, et le
texte remis au modèle le dit."""

from __future__ import annotations

import httpx
import pytest


class FausseReponse:
    def __init__(self, texte: str, statut: int = 200):
        self.text = texte
        self.status_code = statut

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=httpx.Request("POST", "https://x"), response=httpx.Response(self.status_code))


class FauxClient:
    def __init__(self, reponse):
        self.reponse = reponse

    async def post(self, *args, **kwargs):
        return self.reponse


@pytest.fixture
def service(monkeypatch):
    from app.services import web_search

    monkeypatch.setattr(web_search, "verifier_autorisation_recherche", lambda: None)
    svc = web_search.WebSearchService()
    return web_search, svc


@pytest.mark.asyncio
async def test_une_page_sans_marqueur_est_une_recherche_indisponible(service, monkeypatch):
    web_search, svc = service
    html_nouveau_gabarit = "<html><body><div class='react-results--main'>...</div></body></html>"

    async def client():
        return FauxClient(FausseReponse(html_nouveau_gabarit))

    monkeypatch.setattr(svc, "_get_client", client)
    reponse = await svc.search("plombier manosque")

    assert reponse.results == []
    assert reponse.indisponible is True, "une page inconnue passait pour une recherche vide"
    texte = web_search.formater_resultats_pour_llm(reponse)
    assert "indisponible" in texte.lower()
    assert "Aucun résultat" not in texte


@pytest.mark.asyncio
async def test_une_vraie_absence_de_resultat_reste_une_absence(service, monkeypatch):
    web_search, svc = service
    html_sans_resultat = "<html><body><div class='no-results'>No results.</div></body></html>"

    async def client():
        return FauxClient(FausseReponse(html_sans_resultat))

    monkeypatch.setattr(svc, "_get_client", client)
    reponse = await svc.search("zzzz-introuvable")

    assert reponse.results == []
    assert reponse.indisponible is False
    assert "Aucun résultat" in web_search.formater_resultats_pour_llm(reponse)


@pytest.mark.asyncio
async def test_une_erreur_http_est_aussi_indisponible(service, monkeypatch):
    web_search, svc = service

    async def client():
        return FauxClient(FausseReponse("", statut=503))

    monkeypatch.setattr(svc, "_get_client", client)
    reponse = await svc.search("plombier manosque")

    assert reponse.indisponible is True
    assert "indisponible" in web_search.formater_resultats_pour_llm(reponse).lower()
