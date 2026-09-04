"""P-039 : preuves du moteur PERT/CPM pur et déterministe."""

from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

import pytest
from app.services.planning import (
    PlanningDependencyInput,
    PlanningTaskInput,
    calculate_schedule,
    fingerprint_inputs,
    planning_result_to_json,
)

PARIS = ZoneInfo("Europe/Paris")
MONDAY_9 = datetime(2026, 9, 7, 9, 0, tzinfo=PARIS)


def task(
    task_id: str,
    duration: int | None = 60,
    *,
    estimates: tuple[int | None, int | None, int | None] | None = None,
    milestone: bool = False,
    constraint_type: str | None = None,
    constraint_at: datetime | None = None,
) -> PlanningTaskInput:
    if estimates is None:
        estimates = (duration, duration, duration)
    return PlanningTaskInput(
        id=task_id,
        title=f"Tâche {task_id}",
        duration_optimistic_minutes=estimates[0],
        duration_likely_minutes=estimates[1],
        duration_pessimistic_minutes=estimates[2],
        is_milestone=milestone,
        constraint_type=constraint_type,
        constraint_at=constraint_at,
    )


def edge(
    predecessor: str,
    successor: str,
    *,
    kind: str = "finish_start",
    lag: int = 0,
) -> PlanningDependencyInput:
    return PlanningDependencyInput(
        predecessor_task_id=predecessor,
        successor_task_id=successor,
        kind=kind,
        lag_minutes=lag,
    )


def by_id(result) -> dict:
    return {item.task_id: item for item in result.tasks}


def test_chaine_pert_et_chemin_critique():
    result = calculate_schedule(
        [task("A", 60), task("B", 120)],
        [edge("A", "B")],
        starts_at=MONDAY_9,
    )

    assert result.state == "complete"
    assert result.project_duration_minutes == 180
    assert result.critical_path == ("A", "B")
    assert result.critical_tasks == ("A", "B")
    assert result.finishes_at == datetime(2026, 9, 7, 12, 0, tzinfo=PARIS)
    assert by_id(result)["B"].earliest_start_offset_minutes == 60


def test_branches_paralleles_et_marge_totale():
    result = calculate_schedule(
        [task("A", 120), task("B", 60), task("C", 60)],
        [edge("A", "C"), edge("B", "C")],
        starts_at=MONDAY_9,
    )

    assert result.critical_path == ("A", "C")
    assert result.critical_tasks == ("A", "C")
    assert by_id(result)["B"].total_float_minutes == 60
    assert result.project_duration_minutes == 180


@pytest.mark.parametrize(
    ("kind", "lag", "expected_start"),
    [
        ("finish_start", 15, 75),
        ("start_start", 15, 15),
        ("finish_finish", 15, 45),
        ("start_finish", 45, 15),
    ],
)
def test_les_quatre_types_de_dependances(
    kind: str, lag: int, expected_start: int
):
    result = calculate_schedule(
        [task("A", 60), task("B", 30)],
        [edge("A", "B", kind=kind, lag=lag)],
        starts_at=MONDAY_9,
    )

    assert result.state == "complete"
    assert by_id(result)["B"].earliest_start_offset_minutes == expected_start


def test_jalon_impose_une_duree_nulle():
    result = calculate_schedule(
        [task("A", None, estimates=(None, None, None), milestone=True), task("B", 30)],
        [edge("A", "B")],
        starts_at=MONDAY_9,
    )

    assert result.state == "complete"
    assert result.critical_path == ("A", "B")
    assert by_id(result)["A"].expected_duration_minutes == 0
    assert result.project_duration_minutes == 30


def test_cycle_nomme_la_chaine_complete():
    result = calculate_schedule(
        [task("A"), task("B"), task("C")],
        [edge("A", "B"), edge("B", "C"), edge("C", "A")],
        starts_at=MONDAY_9,
    )

    assert result.state == "invalid"
    assert "Cycle de dépendances : A -> B -> C -> A" in result.errors
    assert result.critical_path == ()


def test_entrees_manquantes_sont_nommees_sans_duree_inventee():
    result = calculate_schedule(
        [task("A", estimates=(30, None, 90))],
        [],
        starts_at=None,
    )

    assert result.state == "incomplete"
    assert result.missing_fields == (
        "project.starts_at",
        "tasks.A.duration_likely_minutes",
    )
    assert result.tasks[0].expected_duration_minutes is None
    assert result.finishes_at is None


def test_estimations_desordonnees_sont_invalides():
    result = calculate_schedule(
        [task("A", estimates=(90, 60, 120))],
        [],
        starts_at=MONDAY_9,
    )

    assert result.state == "invalid"
    assert any("optimiste <= probable <= pessimiste" in error for error in result.errors)


def test_contrainte_fixe_incompatible_avec_les_dependances():
    result = calculate_schedule(
        [
            task("A", 120),
            task(
                "B",
                60,
                constraint_type="fixed_start",
                constraint_at=datetime(2026, 9, 7, 10, 0, tzinfo=PARIS),
            ),
        ],
        [edge("A", "B")],
        starts_at=MONDAY_9,
    )

    assert result.state == "invalid"
    assert any("contrainte incompatible" in error for error in result.errors)


def test_calendrier_respecte_pause_et_week_end():
    friday_16 = datetime(2026, 9, 11, 16, 0, tzinfo=PARIS)
    result = calculate_schedule([task("A", 240)], [], starts_at=friday_16)

    assert result.state == "complete"
    assert result.finishes_at == datetime(2026, 9, 14, 11, 0, tzinfo=PARIS)


def test_empreinte_ne_depend_pas_de_l_ordre_des_entrees():
    tasks = [task("B", 90), task("A", 60)]
    dependencies = [edge("A", "B")]

    first = fingerprint_inputs(tasks, dependencies, MONDAY_9, "Europe/Paris")
    second = fingerprint_inputs(
        list(reversed(tasks)),
        list(reversed(dependencies)),
        MONDAY_9,
        "Europe/Paris",
    )

    assert first == second
    assert len(first) == 64


def test_resultat_ne_depend_pas_de_l_ordre_des_entrees():
    tasks = [task("B", estimates=(30, 60, 90)), task("A", 60)]
    dependencies = [edge("A", "B", lag=15)]

    first = calculate_schedule(tasks, dependencies, starts_at=MONDAY_9)
    second = calculate_schedule(
        list(reversed(tasks)),
        list(reversed(dependencies)),
        starts_at=MONDAY_9,
    )

    assert planning_result_to_json(first) == planning_result_to_json(second)
    assert first.forecast is not None
    assert first.forecast.standard_deviation_minutes == 10


def test_1000_taches_et_5000_dependances_restent_sous_une_seconde():
    tasks = [task(f"T{index:04d}", 1) for index in range(1000)]
    dependencies = [
        edge(f"T{index:04d}", f"T{index + step:04d}")
        for index in range(1000)
        for step in range(1, 6)
        if index + step < 1000
    ]

    started = perf_counter()
    result = calculate_schedule(tasks, dependencies, starts_at=MONDAY_9)
    elapsed = perf_counter() - started

    assert len(dependencies) == 4985
    assert result.state == "complete"
    assert result.project_duration_minutes == 1000
    assert elapsed < 1.0, f"calcul en {elapsed:.3f} s"
