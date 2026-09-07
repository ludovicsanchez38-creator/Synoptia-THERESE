"""Cycle 4, lot 3 backend : décisions du portail humain du 05/09/2026.

B-530 : la clé Brave saisie dans Paramètres l'emporte sur celle de l'environnement.
B-544 : la validation du code sandbox lit l'arbre, pas le texte des chaînes et commentaires.
B-520 : sur DeepSeek, un fragment qui porte raisonnement ET texte garde le texte.
"""

from __future__ import annotations

import pytest


class TestB530LaCleSaisieLEmporteSurLEnvironnement:
    def test_la_cle_des_parametres_gagne(self, monkeypatch):
        from app.services import web_search

        monkeypatch.setenv("BRAVE_API_KEY", "cle-environnement")
        monkeypatch.setattr(web_search, "_brave_search_service", None)
        monkeypatch.setattr(web_search, "_brave_api_key_cache", None)
        web_search.set_brave_api_key("cle-parametres")
        try:
            assert web_search._get_brave_api_key() == "cle-parametres", (
                "changer la clé dans Paramètres restait sans effet tant que l'environnement en portait une"
            )
        finally:
            web_search.set_brave_api_key(None)

    def test_l_environnement_reste_un_repli(self, monkeypatch):
        from app.services import web_search

        monkeypatch.setenv("BRAVE_API_KEY", "cle-environnement")
        monkeypatch.setattr(web_search, "_brave_search_service", None)
        monkeypatch.setattr(web_search, "_brave_api_key_cache", None)
        assert web_search._get_brave_api_key() == "cle-environnement"


class TestB544LaValidationLitLArbrePasLeTexte:
    def test_un_document_qui_parle_d_informatique_est_accepte(self):
        from app.services.skills.code_executor import validate_code

        code = (
            "from docx import Document\n"
            "doc = Document()\n"
            "# le paragraphe cite subprocess et os.system, ce sont des mots\n"
            "doc.add_paragraph('Le module os. et sys. sont cités ; eval( est un mot')\n"
            "doc.add_paragraph(f\"Ligne {1 + 1} : requests et urllib sont des noms\")\n"
            "doc.save(output_path)\n"
        )
        valide, message = validate_code(code)
        assert valide, message

    def test_un_appel_reel_reste_refuse(self):
        from app.services.skills.code_executor import validate_code

        for code in (
            "import os\nos.system('rm -rf /')\n",
            "x = __import__('os')\n",
            "eval('1+1')\n",
            "f\"{__import__('os').getcwd()}\"\n",
        ):
            valide, _ = validate_code(code)
            assert not valide, code


class TestB520DeepSeekGardeLeTexteAvecLeRaisonnement:
    @pytest.mark.asyncio
    async def test_un_delta_mixte_emet_le_texte_visible(self, monkeypatch):
        from app.services.providers import deepseek as module
        from app.services.providers.base import LLMConfig, LLMProvider

        lignes = [
            'data: {"choices":[{"delta":{"reasoning_content":"je réfléchis","content":"Bonjour"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"content":" Marie"},"finish_reason":"stop"}]}',
            "data: [DONE]",
        ]

        class FauxResponse:
            status_code = 200

            async def aiter_lines(self):
                for ligne in lignes:
                    yield ligne

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                return False

            async def aread(self):
                return b""

            def raise_for_status(self):
                return None

        class FauxClient:
            def stream(self, *args, **kwargs):
                return FauxResponse()

        config = LLMConfig(LLMProvider.DEEPSEEK, "deepseek-chat", api_key="x")
        provider = module.DeepSeekProvider(config, FauxClient())
        textes = []
        async for evenement in provider.stream(None, [{"role": "user", "content": "Salut"}], None):
            if evenement.type == "text" and evenement.content:
                textes.append(evenement.content)
        assert "".join(textes) == "Bonjour Marie", textes
