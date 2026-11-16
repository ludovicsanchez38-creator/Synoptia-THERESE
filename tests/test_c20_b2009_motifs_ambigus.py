"""Un refus prudent n'attribue pas une opinion à une formule ambiguë."""

import pytest
from app.services.memory_card_security import message_refus, motif_sensible


@pytest.mark.parametrize(('texte', 'motif_inexact'), [
    ('Consulter la politique de confidentialité du site', 'opinion politique'),
    ('Contacter le syndic de copropriété', 'appartenance syndicale'),
])
def test_refus_ambigu_sans_attribution_inexacte(texte, motif_inexact):
    assert motif_sensible(texte) is not None
    message = message_refus(texte)
    assert message is not None
    assert motif_inexact not in message
    assert texte not in message
    assert message_refus(['Organisation', texte]) == message
