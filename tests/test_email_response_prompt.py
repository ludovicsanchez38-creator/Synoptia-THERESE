"""US-003 (RGPD-3 / IA Act art. 50) : le générateur de réponses email ne doit
plus instruire l'IA de dissimuler sa nature. La signature au nom de
l'utilisateur reste, mais la consigne « ne mentionne jamais que tu es une IA »
est retirée (indéfendable, et risquée si un envoi automatique apparaissait)."""
from app.services.email_response_generator import build_email_system_prompt


def test_prompt_ne_dissimule_pas_l_ia():
    prompt = build_email_system_prompt("Ludo", "Consultant IA", "Synoptïa")
    assert "Ne mentionne jamais que tu es une IA" not in prompt
    assert "tu es une IA" not in prompt


def test_prompt_conserve_la_signature_au_nom_de_l_utilisateur():
    prompt = build_email_system_prompt("Ludo", "Consultant IA", "Synoptïa")
    assert "Signe toujours avec le nom de Ludo" in prompt


def test_prompt_protege_toujours_les_donnees_crm():
    prompt = build_email_system_prompt("Ludo", "Consultant IA", "Synoptïa")
    assert "score CRM" in prompt
