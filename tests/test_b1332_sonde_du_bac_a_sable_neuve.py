"""B-1332 : résidu de B-1324. Le conftest remettait à neuf le verrou de sonde
du bac à sable mais pas son résultat mémorisé : un test qui faisait échouer la
sonde laissait « confinement indisponible » à tous les suivants. Les deux
tests se suivent à dessein. Lecteur ζ, passe 8."""


def test_1_un_test_memorise_une_sonde_en_echec():
    from app.services.agents import bac_a_sable

    bac_a_sable._SONDE_RESULTAT = (False, "sonde en échec pour ce test")


def test_2_le_test_suivant_repart_d_une_sonde_neuve():
    from app.services.agents import bac_a_sable

    assert bac_a_sable._SONDE_RESULTAT is None
