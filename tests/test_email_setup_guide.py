"""B-375 (05/09/2026) : le guide embarqué de configuration Google disait
encore « Application de bureau » et « Active l'API Gmail » seulement, quand
la correction de juillet (USER_GUIDE_ALPHA.md:438, CHANGELOG) impose un
client « Application Web » et l'activation des API Gmail ET Calendar. Le
guide corrigé et l'assistant se contredisaient mot pour mot pendant la
configuration.
"""

from __future__ import annotations

import pytest
from app.services.email_setup_assistant import EmailSetupAssistant


@pytest.mark.asyncio
@pytest.mark.parametrize("has_project", [True, False])
async def test_le_guide_gmail_dit_application_web_et_les_deux_api(has_project: bool):
    texte = await EmailSetupAssistant.generate_guide_message("gmail", has_project)

    assert "Application de bureau" not in texte
    assert "Application Web" in texte
    if not has_project:
        assert "Calendar" in texte, "l'API Google Calendar doit être activée aussi"
