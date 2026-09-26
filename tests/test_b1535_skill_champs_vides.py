"""B-1535 : le skill de proposition et le skill e-mail écrivaient « None »
pour une entreprise, une adresse ou des notes vides.

`contact_pour_un_skill` donne toujours ces clés, parfois à None ; or
`contact.get('company', 'Non renseignée')` ne retombe sur le défaut que si la
clé MANQUE. Le modèle recevait « Entreprise : None » et pouvait le recopier.
"""

import pytest
from app.models.entities import Contact


@pytest.mark.parametrize(
    ("classe", "entree", "cle"),
    [("ProposalSkill", "client_name", "client_context"), ("EmailProSkill", "recipient", "recipient_context")],
)
def test_un_champ_vide_se_dit_non_renseigne(tmp_path, classe, entree, cle):
    from app.routers.skills import contact_pour_un_skill
    from app.services.skills import text_skills

    fiche = contact_pour_un_skill(Contact(first_name="Karim", last_name="Benali"))
    skill = getattr(text_skills, classe)(tmp_path)
    contexte = skill.get_enrichment_context({}, {"inputs": {entree: "Benali"}, "contacts": [fiche]})[cle]

    assert "None" not in contexte
    assert "Entreprise : Non renseignée" in contexte
    assert "Email : Non renseigné" in contexte
    assert "Notes : Aucune note" in contexte
