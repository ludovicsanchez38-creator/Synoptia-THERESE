"""THÉRÈSE v2 — Fournisseur Qwen (Alibaba Model Studio).

Model Studio expose une interface compatible OpenAI pour les modèles Qwen.

PARTICULARITÉ DÉCISIVE : l'adresse contient l'identifiant d'espace de travail
du compte, et diffère selon la région :

    https://{EspaceDeTravail}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
    https://{EspaceDeTravail}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1

Écrire cette adresse en dur ferait fonctionner le fournisseur pour un seul
compte au monde. Elle doit donc rester configurable, et c'est la raison d'être
de `url_effective()` : la configuration l'emporte, le défaut ne sert que de
repère lisible.

Relevé le 24/08/2026 sur alibabacloud.com/help/en/model-studio, page
« compatibility-of-openai-with-dashscope ».
"""

import logging
from typing import Any

from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

# Défaut Singapour, avec le marqueur d'espace de travail bien visible : il
# signale que cette adresse DOIT être personnalisée pour fonctionner.
QWEN_API_URL = (
    "https://{EspaceDeTravail}.ap-southeast-1.maas.aliyuncs.com"
    "/compatible-mode/v1/chat/completions"
)


class QwenProvider(OpenAIProvider):
    """Fournisseur Qwen d'Alibaba, compatible OpenAI, outils inclus.

    `url_effective()` vit désormais sur OpenAIProvider (dette 0.43.4) : ici,
    seul le défaut change - et il est inutilisable tel quel, à dessein.
    """

    API_URL = QWEN_API_URL

    def _utilise_max_completion_tokens(self) -> bool:
        return self.config.model == "qwen4-max" or super()._utilise_max_completion_tokens()

    def _champ_raisonnement_a_rejouer(self) -> str | None:
        return "encrypted_content" if self.config.model == "qwen4-max" else None

    def _build_request_body(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        corps = super()._build_request_body(messages, tools)
        if self.config.model == "qwen4-max":
            # https://www.alibabacloud.com/help/en/model-studio/cot-summary
            corps.update(
                enable_thinking=True, thinking_display="summarized", preserve_thinking=True,
            )
        return corps
