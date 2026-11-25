"""Continuité du chat DeepSeek quand la base ne garde que le texte."""

import json

import httpx
import pytest


def _charges_sse(reponse):
    return [
        json.loads(ligne.removeprefix("data: "))
        for ligne in reponse.text.splitlines()
        if ligne.startswith("data: ")
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("modele", ["deepseek-v4-pro", "deepseek-flash"])
async def test_deepseek_conserve_historique_et_outils_sans_raisonnement_rejouable(
    client, monkeypatch, modele,
):
    from app.services import http_client, llm

    from tests.test_routers_invoices import _create_contact, _create_invoice

    facture = await _create_invoice(client, await _create_contact(client))
    reference = facture["invoice_number"]
    texte_initial = "Première réponse de contrôle."
    trace = "Raisonnement de contrôle."
    suite = "Recherche terminée."
    appels = []

    def transmettre(requete):
        if requete.url.path == "/api/tags":
            return httpx.Response(503)
        assert str(requete.url) == "https://api.deepseek.com/chat/completions"
        corps = json.loads(requete.content)
        if not corps.get("tools"):
            delta, fin = {"content": "Titre de contrôle"}, "stop"
        else:
            appels.append(corps)
            messages = corps["messages"]
            sans_reflexion = corps.get("thinking") == {"type": "disabled"}
            if not sans_reflexion and any(
                m["role"] == "assistant" and not m.get("reasoning_content") for m in messages
            ):
                return httpx.Response(400)
            if any(m["role"] == "tool" for m in messages):
                delta, fin = {"content": suite}, "stop"
            elif any(m["role"] == "assistant" for m in messages):
                assert "search_invoices" in {t["function"]["name"] for t in corps["tools"]}
                delta = {"tool_calls": [{
                    "index": 0, "id": "recherche_fictive", "type": "function",
                    "function": {"name": "search_invoices", "arguments": json.dumps({"query": reference})},
                }]}
                fin = "tool_calls"
            else:
                delta, fin = {"reasoning_content": trace, "content": texte_initial}, "stop"

        ligne = json.dumps({"choices": [{"delta": delta, "finish_reason": fin}]})
        return httpx.Response(200, text=f"data: {ligne}\n\ndata: [DONE]\n\n")

    async with httpx.AsyncClient(transport=httpx.MockTransport(transmettre)) as fournisseur:
        async def get_client():
            return fournisseur

        monkeypatch.setattr(llm, "_llm_service", None)
        monkeypatch.setattr(http_client, "get_http_client", get_client)
        assert (await client.post("/api/config/api-key", json={
            "provider": "deepseek", "api_key": "valeur-fictive-de-test",
        })).status_code == 200
        assert (await client.post("/api/config/llm", json={
            "provider": "deepseek", "model": modele, "effort": "max",
        })).status_code == 200
        assert (await client.post("/api/consents", json={
            "purpose": "documents", "provider": "deepseek", "granted": True, "text_version": "3",
        })).status_code == 200

        premier = await client.post("/api/chat/send", json={"message": "Première question.", "stream": True})
        assert premier.status_code == 200
        evenements_initiaux = _charges_sse(premier)
        assert any(e["type"] == "text" and e["content"] == texte_initial for e in evenements_initiaux)
        assert trace not in json.dumps(evenements_initiaux, ensure_ascii=False)
        conversation_id = next(e["conversation_id"] for e in evenements_initiaux if e.get("conversation_id"))

        suivant = await client.post("/api/chat/send", json={
            "message": "Cherche dans mes factures.", "conversation_id": conversation_id, "stream": True,
        })
        assert suivant.status_code == 200
        evenements = _charges_sse(suivant)
        assert not [e["content"] for e in evenements if e["type"] == "error"]
        assert [e["content"] for e in evenements if e["type"] == "notice" and "DeepSeek" in e["content"]] == [
            "DeepSeek utilise les outils sans réflexion pour cet échange, car l’historique est incomplet.",
        ]
        visibles = [(e["type"], e.get("content")) for e in evenements]
        assert ("text", suite) in visibles, visibles

        premier_appel, second_appel, continuation = appels
        assert premier_appel["reasoning_effort"] == "max"
        assert "thinking" not in premier_appel
        for appel in (second_appel, continuation):
            assert {"role": "assistant", "content": texte_initial} in appel["messages"]
            assert appel["thinking"] == {"type": "disabled"}
            assert "reasoning_effort" not in appel
        assert any(
            m["role"] == "tool" and m["tool_call_id"] == "recherche_fictive"
            and reference in m["content"]
            for m in continuation["messages"]
        )
        assert (await client.get("/api/config/llm")).json()["effort"] == "max"
