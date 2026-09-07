"""B-632 (persona Sophie, c4) : deux générations réelles de l'atelier ne
laissaient aucune trace dans le suivi de consommation. L'atelier (trame,
résumé, rédaction) et les skills comptent désormais leurs appels au modèle,
avec l'usage réel du fournisseur quand il est fourni."""

from __future__ import annotations

import pytest


class FauxServiceLlm:
    modele_effectif = "gemma-test"
    fournisseur_effectif = "ollama"

    def __init__(self, reponse: str = "1. Introduction\n2. Développement\n3. Conclusion"):
        self.reponse = reponse
        self.appels = 0

    async def generate_content(self, prompt, context=None, system_prompt=None, max_tokens=None, usage_sink=None):
        self.appels += 1
        if usage_sink is not None:
            usage_sink["input_tokens"] = 321
            usage_sink["output_tokens"] = 123
        return self.reponse

    def prepare_context(self, *args, **kwargs):
        return None

    async def stream_response(self, context, raise_on_error=False, usage_sink=None, **kwargs):
        self.appels += 1
        if usage_sink is not None:
            usage_sink["input_tokens"] = 50
            usage_sink["output_tokens"] = 70
        yield "Texte rédigé par le faux modèle."


def _compte(tracker) -> tuple[int, int]:
    usage = tracker.get_daily_usage()
    return int(usage.get("input_tokens") or usage.get("today_input") or 0), int(usage.get("output_tokens") or usage.get("today_output") or 0)


@pytest.mark.asyncio
async def test_la_trame_de_l_atelier_est_comptee_avec_l_usage_reel(client, monkeypatch):
    from app.routers import documents as module
    from app.services.token_tracker import get_token_tracker

    faux = FauxServiceLlm()
    monkeypatch.setattr(module, "get_llm_service", lambda: faux)
    tracker = get_token_tracker()
    avant = _compte(tracker)

    creation = await client.post("/api/documents", json={"title": "Programme", "brief": "Formation IA 2h30"})
    assert creation.status_code in (200, 201), creation.text
    trame = await client.post(f"/api/documents/{creation.json()['id']}/outline")
    # Une trame inexploitable (502) a quand même coûté des jetons : elle est comptée.
    assert trame.status_code in (200, 502), trame.text

    apres = _compte(tracker)
    assert faux.appels >= 1
    assert apres[0] - avant[0] >= 321 and apres[1] - avant[1] >= 123, (avant, apres)


def test_l_aide_estime_quand_le_fournisseur_ne_dit_rien(monkeypatch):
    from app.services import token_tracker as module

    enregistres = []
    monkeypatch.setattr(module, "get_token_tracker", lambda: type("T", (), {"record_usage": lambda self, **kw: enregistres.append(kw) or kw})())
    module.enregistrer_usage_llm(FauxServiceLlm(), {}, "skill:docx", "un deux trois", "quatre cinq")
    assert enregistres[0]["input_tokens"] == 6 and enregistres[0]["output_tokens"] == 4
    assert enregistres[0]["model"] == "gemma-test" and enregistres[0]["provider"] == "ollama"
