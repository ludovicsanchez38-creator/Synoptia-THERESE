"""
Les échéances déduites d'une prestation (tranche E3 du 29/08).

Une seule règle pour l'instant : le questionnaire à froid.
"""

from datetime import date, timedelta

# Indicateur Qualiopi : le questionnaire se déclenche 90 jours après la FIN de
# la formation, pas après le test de sortie ni après la signature.
JOURS_AVANT_QUESTIONNAIRE_A_FROID = 90


def echeance_du_questionnaire_a_froid(fin_de_formation: date | None) -> date | None:
    """L'échéance, ou rien.

    Sans date de fin, on ne calcule pas : deviner une échéance réglementaire,
    ce serait l'inventer, et une date fausse est pire qu'une date absente.
    """
    if fin_de_formation is None:
        return None
    return fin_de_formation + timedelta(days=JOURS_AVANT_QUESTIONNAIRE_A_FROID)
