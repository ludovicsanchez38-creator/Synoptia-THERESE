"""B-1907 : un brouillon ne doit pas inventer l'identité de l'utilisateur."""
from types import SimpleNamespace

from app.services import email_response_generator as module


async def test_sans_profil_brouillon_ne_fabrique_pas_identite_ni_signature(monkeypatch):
    class ModeleFictif:
        config = SimpleNamespace(provider=SimpleNamespace(value="ollama"), model="fictif")
        system_prompt = ""

        async def generate_content(self, prompt, system_prompt):
            self.system_prompt = system_prompt
            return "Bonjour, merci pour ton message."

    modele = ModeleFictif()
    monkeypatch.setattr(module, "get_cached_profile", lambda: None)
    monkeypatch.setattr(module, "get_llm_service", lambda: modele)
    resultat = await module.EmailResponseGenerator.generate_response(
        subject="Devis", from_name="Camille", from_email="camille@example.test", body="Bonjour"
    )
    assert "Ludo" not in modele.system_prompt
    assert "Synoptïa" not in modele.system_prompt
    assert resultat == "Bonjour, merci pour ton message."
