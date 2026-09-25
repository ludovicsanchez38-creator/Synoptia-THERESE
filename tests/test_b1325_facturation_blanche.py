"""B-1325 : un SIRET, une adresse ou une raison sociale faits d'espaces
comptaient comme complets pour une facture conforme (ni
missing_billing_fields ni is_billing_complete ne retiraient les espaces).
Lecteur δ, passe 7."""


def test_des_champs_blancs_manquent_a_la_facture():
    from app.services.user_profile import UserProfile

    profil = UserProfile(name="Marie", company="  ", siret="   ", address=" \t ")
    manquants = profil.missing_billing_fields()
    assert "SIRET" in manquants and "adresse" in manquants, manquants
    assert profil.is_billing_complete() is False


def test_des_champs_remplis_ne_manquent_pas():
    from app.services.user_profile import UserProfile

    profil = UserProfile(name="Marie", siret="12345678900010", address="12 rue X")
    assert profil.missing_billing_fields() == [] and profil.is_billing_complete() is True
