"""
Les échéances déduites d'une prestation.

Une seule règle pour l'instant : le suivi après la fin.

**Pourquoi ce nom-là.** Pour Ludo, formateur certifié Qualiopi, c'est le
« questionnaire à froid J+90 », un indicateur réglementaire. Mais THÉRÈSE est
une application publique : un garagiste rappelle peut-être à 30 jours, un
architecte à un an, un dentiste à six mois. Le besoin — reprendre contact un
certain temps après la fin — est commun ; le délai et le mot ne le sont pas.

D'où : un nom neutre, un délai réglable, et 90 jours par défaut parce qu'il
faut bien une valeur.
"""

from datetime import date, timedelta

# 90 jours : le J+90 des organismes de formation. C'est un DÉFAUT, pas une loi.
DELAI_PAR_DEFAUT_JOURS = 90


def echeance_de_suivi(
    fin_de_prestation: date | None,
    jours: int = DELAI_PAR_DEFAUT_JOURS,
) -> date | None:
    """L'échéance, ou rien.

    Sans date de fin, on ne calcule pas : deviner une échéance, ce serait
    l'inventer, et pour un organisme de formation c'est un indicateur
    réglementaire — une date fausse y est pire qu'une date absente.
    """
    if jours < 1:
        raise ValueError("Un délai de suivi doit valoir au moins un jour")
    if fin_de_prestation is None:
        return None
    return fin_de_prestation + timedelta(days=jours)
