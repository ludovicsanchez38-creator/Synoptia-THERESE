"""Observer des payloads synthétiques, sans client HTTP ni appel fournisseur.

Ce contrôle du code existant n'est ni un test API, ni une qualification UI,
ni une intégration des modèles. Les anomalies attendues restent explicites.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


REPO = Path("/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex")
SOURCES = (
    "src/backend/app/services/providers/base.py",
    "src/backend/app/services/providers/anthropic.py",
    "src/backend/app/services/providers/openai.py",
    "src/backend/app/services/modeles_catalogue.py",
)


def empreintes() -> dict[str, str]:
    return {
        nom: hashlib.sha256((REPO / nom).read_bytes()).hexdigest()
        for nom in SOURCES
    }


def interdire_effets(event: str, args: tuple) -> None:
    if event.startswith("socket.") or event in {
        "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec",
    }:
        raise RuntimeError(f"Effet externe interdit : {event}")
    if event == "open":
        mode = args[1]
        flags = args[2]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & 3
        ):
            raise RuntimeError("Écriture de fichier interdite")


def main() -> None:
    avant = empreintes()
    sys.addaudithook(interdire_effets)
    sys.path.insert(0, str(REPO / "src/backend"))
    from app.services.providers.anthropic import AnthropicProvider
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.openai import OpenAIProvider

    message = [{"role": "user", "content": "Témoin synthétique"}]
    outils = [{"type": "function", "function": {
        "name": "temoin", "description": "Sans exécution",
        "parameters": {"type": "object", "properties": {}},
    }}]
    haiku = AnthropicProvider(
        LLMConfig(LLMProvider.ANTHROPIC, "claude-haiku-5-5"), None,
    )._build_request_body(None, message, None)
    sonnet = AnthropicProvider(
        LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-5-5"), None,
    )._build_request_body(None, message, None)
    gpt_provider = OpenAIProvider(
        LLMConfig(LLMProvider.OPENAI, "gpt-6.1-sol", effort="high"), None,
    )
    gpt = gpt_provider._build_request_body(message, outils)
    classique = OpenAIProvider(
        LLMConfig(LLMProvider.OPENAI, "gpt-4o"), None,
    )._build_request_body(message, None)
    assert haiku["temperature"] == 0.7
    assert "temperature" not in sonnet
    assert gpt["reasoning_effort"] == "none" and gpt["tools"] == outils
    assert gpt_provider.url_effective().endswith("/chat/completions")
    assert classique["temperature"] == 0.7
    apres = empreintes()
    assert avant == apres
    print(json.dumps({
        "scope": "construction_payloads_synthetiques_uniquement",
        "network_or_provider_calls": 0,
        "http_client_created": False,
        "source_sha256": avant,
        "sources_unchanged": True,
        "observations": {
            "haiku_5_5_temperature": haiku["temperature"],
            "sonnet_5_5_temperature_absente": "temperature" not in sonnet,
            "gpt_6_1_sol_tools_effort": gpt["reasoning_effort"],
            "gpt_6_1_sol_endpoint": gpt_provider.url_effective(),
            "gpt_4o_temperature_temoin": classique["temperature"],
        },
        "api_compatibility_verified": False,
        "native_or_release_qualified": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
