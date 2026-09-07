"""B-475 (cycle 4) : le calendrier ouvré parcourait les jours un par un. Une
contrainte datée d'une faute de frappe (année 9999) faisait tourner le calcul
plusieurs secondes : le coût suivait l'écart de dates, pas la taille du
projet. Le motif hebdomadaire étant fixe, les journées entières se comptent
d'un trait ; le résultat reste identique au parcours jour par jour."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from fractions import Fraction
from time import perf_counter
from zoneinfo import ZoneInfo

import pytest

PARIS = ZoneInfo("Europe/Paris")


def _minutes_de_reference(calendar, start, end):
    """Le parcours jour par jour d'origine, gardé comme oracle."""
    left = start.astimezone(calendar.timezone)
    right = end.astimezone(calendar.timezone)
    sign = 1
    if right < left:
        left, right = right, left
        sign = -1
    total = 0
    day = left.date()
    while day <= right.date():
        for i_start, i_end in calendar._bounds(day):
            o_start, o_end = max(left, i_start), min(right, i_end)
            if o_end > o_start:
                total += int((o_end - o_start).total_seconds())
        day += timedelta(days=1)
    return sign * Fraction(total, 60)


def _ajout_de_reference(calendar, instant, minutes):
    remaining = Fraction(minutes)
    current = calendar.normalize_start(instant)
    while remaining > 0:
        active_end = None
        for s, e in calendar._bounds(current.date()):
            if s <= current < e:
                active_end = e
                break
        if active_end is None:
            current = calendar.normalize_start(current)
            continue
        available = Fraction(int((active_end - current).total_seconds()), 60)
        if remaining <= available:
            seconds = remaining * 60
            return current + timedelta(seconds=seconds.numerator / seconds.denominator)
        remaining -= available
        current = calendar.normalize_start(active_end)
    return current


@pytest.fixture
def calendrier():
    from app.services.planning import WorkCalendar

    return WorkCalendar()


def test_une_faute_de_frappe_sur_l_annee_ne_coute_plus_des_secondes(calendrier):
    debut = datetime(2026, 1, 5, 9, 0, tzinfo=PARIS)
    faute_de_frappe = datetime(9999, 12, 31, 18, 0, tzinfo=PARIS)

    top = perf_counter()
    calendrier.working_minutes_between(debut, faute_de_frappe)
    duree_entre = perf_counter() - top

    top = perf_counter()
    calendrier.add_work_minutes(debut, Fraction(2100 * 52 * 5000))
    duree_ajout = perf_counter() - top

    assert duree_entre < 0.2, f"working_minutes_between a mis {duree_entre:.2f} s"
    assert duree_ajout < 0.2, f"add_work_minutes a mis {duree_ajout:.2f} s"


@pytest.mark.parametrize(
    ("debut", "fin"),
    [
        # Même journée, en plein travail.
        (datetime(2026, 3, 3, 10, 0, tzinfo=PARIS), datetime(2026, 3, 3, 16, 30, tzinfo=PARIS)),
        # Deux journées consécutives.
        (datetime(2026, 3, 3, 10, 0, tzinfo=PARIS), datetime(2026, 3, 4, 11, 0, tzinfo=PARIS)),
        # Par-dessus un week-end.
        (datetime(2026, 3, 6, 15, 0, tzinfo=PARIS), datetime(2026, 3, 9, 9, 30, tzinfo=PARIS)),
        # Départ un samedi, arrivée un dimanche.
        (datetime(2026, 3, 7, 12, 0, tzinfo=PARIS), datetime(2026, 3, 15, 8, 0, tzinfo=PARIS)),
        # Changement d'heure de mars et d'octobre 2026, plusieurs semaines.
        (datetime(2026, 3, 20, 9, 0, tzinfo=PARIS), datetime(2026, 4, 10, 18, 0, tzinfo=PARIS)),
        (datetime(2026, 10, 1, 14, 0, tzinfo=PARIS), datetime(2026, 11, 30, 12, 0, tzinfo=PARIS)),
        # Bornes hors plage et ordre inversé.
        (datetime(2026, 5, 4, 6, 0, tzinfo=PARIS), datetime(2026, 5, 22, 23, 0, tzinfo=PARIS)),
        (datetime(2026, 6, 30, 17, 0, tzinfo=PARIS), datetime(2026, 6, 1, 9, 15, tzinfo=PARIS)),
        # Une autre zone en entrée.
        (datetime(2026, 7, 1, 7, 0, tzinfo=ZoneInfo("UTC")), datetime(2026, 8, 31, 16, 0, tzinfo=ZoneInfo("UTC"))),
    ],
)
def test_le_compte_d_un_trait_egale_le_parcours_jour_par_jour(calendrier, debut, fin):
    assert calendrier.working_minutes_between(debut, fin) == _minutes_de_reference(calendrier, debut, fin)


@pytest.mark.parametrize(
    ("depart", "minutes"),
    [
        (datetime(2026, 3, 3, 10, 0, tzinfo=PARIS), 90),
        (datetime(2026, 3, 3, 10, 0, tzinfo=PARIS), 420),
        (datetime(2026, 3, 3, 9, 0, tzinfo=PARIS), 2100),
        (datetime(2026, 3, 3, 9, 0, tzinfo=PARIS), 2100 * 3 + 500),
        (datetime(2026, 3, 6, 17, 30, tzinfo=PARIS), 2100 * 2 + 45),
        (datetime(2026, 3, 7, 12, 0, tzinfo=PARIS), 2100 * 4),
        (datetime(2026, 3, 20, 9, 0, tzinfo=PARIS), 2100 * 6 + 1000),
        (datetime(2026, 10, 20, 11, 0, tzinfo=PARIS), Fraction(2100 * 5 * 7, 3)),
    ],
)
def test_l_ajout_d_un_trait_egale_le_parcours_jour_par_jour(calendrier, depart, minutes):
    attendu = _ajout_de_reference(calendrier, depart, minutes)
    obtenu = calendrier.add_work_minutes(depart, minutes)
    assert obtenu == attendu
    # Et l'aller-retour reste exact.
    assert calendrier.working_minutes_between(calendrier.normalize_start(depart), obtenu) == Fraction(minutes)


def test_les_jours_ouvres_d_un_intervalle_se_comptent_sans_parcours():
    from app.services.planning import WorkCalendar

    def reference(a: date, b: date) -> int:
        return sum(1 for n in range((b - a).days + 1) if (a + timedelta(days=n)).weekday() < 5)

    for depart in (date(2026, 3, 2), date(2026, 3, 4), date(2026, 3, 7), date(2026, 3, 8)):
        for longueur in range(0, 24):
            fin = depart + timedelta(days=longueur)
            assert WorkCalendar._weekdays_in(depart, fin) == reference(depart, fin), (depart, fin)
    assert WorkCalendar._weekdays_in(date(2026, 3, 9), date(2026, 3, 8)) == 0
    assert time(9) == WorkCalendar._intervals[0][0]
