"""B-1428 (revue de la RFC P-121, décision du 25/09) : l'arrondi d'une ligne
au demi-centime différait entre l'écran (Math.round, 3,13) et le moteur
(round de Python, au pair sur le binaire, 3,12) pour 2,5 × 1,25 €. Règle
retenue : arrondi commercial au demi-centime supérieur (en valeur absolue),
partout."""

from types import SimpleNamespace

import pytest
from app.routers.invoices import _montants_de_ligne


@pytest.mark.parametrize(("quantite", "prix", "attendu"), [
    (2.5, 1.25, 3.13),     # 3,125 : le serveur disait 3,12
    (1, 1.005, 1.01),      # 1,005 n'est pas représentable en binaire
    (1, 2.675, 2.68),
    (1, -3.125, -3.13),    # un avoir s'arrondit symétriquement
    (3, 33.33, 99.99),
])
def test_une_ligne_s_arrondit_au_demi_centime_superieur(quantite, prix, attendu):
    ligne = SimpleNamespace(quantity=quantite, unit_price_ht=prix, tva_rate=0.0)
    total_ht, total_ttc = _montants_de_ligne(ligne, tva_applicable=False)
    assert (total_ht, total_ttc) == (attendu, attendu)


def test_la_tva_s_arrondit_de_meme():
    ligne = SimpleNamespace(quantity=1, unit_price_ht=10.625, tva_rate=20.0)
    total_ht, total_ttc = _montants_de_ligne(ligne, tva_applicable=True)
    assert total_ht == 10.63 and total_ttc == 12.76  # 10,63 × 1,2 = 12,756
