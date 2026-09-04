"""Moteur déterministe PERT/CPM de THÉRÈSE (P-039, lot A).

Ce module ne connaît ni SQLModel, ni FastAPI. Les mêmes entrées produisent le
même résultat ; le routeur se charge uniquement de lire et persister les
snapshots.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from fractions import Fraction
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ENGINE_VERSION = "pert-cpm-1"
MAX_LAG_MINUTES = 525_600
PlanningState = Literal["complete", "incomplete", "invalid"]
DependencyKind = Literal[
    "finish_start", "start_start", "finish_finish", "start_finish"
]
ConstraintType = Literal[
    "start_no_earlier", "finish_no_later", "fixed_start", "fixed_finish"
]


@dataclass(frozen=True, slots=True)
class PlanningTaskInput:
    id: str
    title: str
    duration_optimistic_minutes: int | None = None
    duration_likely_minutes: int | None = None
    duration_pessimistic_minutes: int | None = None
    constraint_type: str | None = None
    constraint_at: datetime | None = None
    progress_percent: int = 0
    is_milestone: bool = False
    billing_milestone: bool = False


@dataclass(frozen=True, slots=True)
class PlanningDependencyInput:
    predecessor_task_id: str
    successor_task_id: str
    kind: str = "finish_start"
    lag_minutes: int = 0


@dataclass(frozen=True, slots=True)
class PlanningTaskResult:
    task_id: str
    title: str
    expected_duration_minutes: float | None
    variance_minutes_squared: float | None
    earliest_start_offset_minutes: float | None = None
    earliest_finish_offset_minutes: float | None = None
    latest_start_offset_minutes: float | None = None
    latest_finish_offset_minutes: float | None = None
    total_float_minutes: float | None = None
    is_critical: bool = False
    earliest_start_at: datetime | None = None
    earliest_finish_at: datetime | None = None
    latest_start_at: datetime | None = None
    latest_finish_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PlanningForecast:
    standard_deviation_minutes: float
    lower_duration_minutes: float
    upper_duration_minutes: float
    expected_finish_at: datetime
    lower_finish_at: datetime
    upper_finish_at: datetime


@dataclass(frozen=True, slots=True)
class PlanningResult:
    engine_version: str
    timezone: str
    state: PlanningState
    tasks: tuple[PlanningTaskResult, ...]
    critical_path: tuple[str, ...]
    critical_tasks: tuple[str, ...]
    project_duration_minutes: float | None
    starts_at: datetime | None
    finishes_at: datetime | None
    forecast: PlanningForecast | None
    missing_fields: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


def planning_result_to_dict(result: PlanningResult) -> dict[str, object]:
    """Convertit le résultat en structure JSON/Pydantic sans perte de dates."""
    return asdict(result)


def planning_result_to_json(result: PlanningResult) -> str:
    """Sérialise un résultat pour un snapshot immuable."""

    def _default(value: object) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(f"Type non sérialisable : {type(value).__name__}")

    return json.dumps(
        planning_result_to_dict(result),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_default,
    )


def fingerprint_inputs(
    tasks: list[PlanningTaskInput],
    dependencies: list[PlanningDependencyInput],
    starts_at: datetime | None,
    timezone: str,
) -> str:
    """Empreinte stable des seules données qui influencent le calcul."""

    def _instant(value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.astimezone(UTC).isoformat()

    payload = {
        "engine_version": ENGINE_VERSION,
        "timezone": timezone,
        "starts_at": _instant(starts_at),
        "tasks": [
            {
                **asdict(task),
                "constraint_at": _instant(task.constraint_at),
            }
            for task in sorted(tasks, key=lambda item: item.id)
        ],
        "dependencies": [
            asdict(dependency)
            for dependency in sorted(
                dependencies,
                key=lambda item: (
                    item.predecessor_task_id,
                    item.successor_task_id,
                    item.kind,
                    item.lag_minutes,
                ),
            )
        ],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class WorkCalendar:
    """Calendrier ouvré V1 : lundi-vendredi, 09-12 et 14-18."""

    _intervals = ((time(9), time(12)), (time(14), time(18)))

    def __init__(self, timezone: str = "Europe/Paris") -> None:
        try:
            self.timezone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Fuseau horaire inconnu : {timezone}") from exc

    def _local(self, instant: datetime) -> datetime:
        if instant.tzinfo is None:
            raise ValueError("Les dates de planning doivent porter un fuseau horaire")
        return instant.astimezone(self.timezone)

    def _bounds(self, day: date) -> tuple[tuple[datetime, datetime], ...]:
        if day.weekday() >= 5:
            return ()
        return tuple(
            (
                datetime.combine(day, start, self.timezone),
                datetime.combine(day, end, self.timezone),
            )
            for start, end in self._intervals
        )

    def normalize_start(self, instant: datetime) -> datetime:
        """Avance un début hors plage vers le prochain instant ouvré."""
        current = self._local(instant)
        while True:
            for start, end in self._bounds(current.date()):
                if current < start:
                    return start
                if start <= current < end:
                    return current
            next_day = current.date() + timedelta(days=1)
            current = datetime.combine(next_day, time.min, self.timezone)

    def is_fixed_start(self, instant: datetime) -> bool:
        current = self._local(instant)
        return any(start <= current < end for start, end in self._bounds(current.date()))

    def is_fixed_finish(self, instant: datetime) -> bool:
        current = self._local(instant)
        return any(start < current <= end for start, end in self._bounds(current.date()))

    def working_minutes_between(self, start: datetime, end: datetime) -> Fraction:
        """Minutes ouvrées signées entre deux instants conscients."""
        left = self._local(start)
        right = self._local(end)
        sign = 1
        if right < left:
            left, right = right, left
            sign = -1
        total_seconds = 0
        day = left.date()
        while day <= right.date():
            for interval_start, interval_end in self._bounds(day):
                overlap_start = max(left, interval_start)
                overlap_end = min(right, interval_end)
                if overlap_end > overlap_start:
                    total_seconds += int(
                        (overlap_end - overlap_start).total_seconds()
                    )
            day += timedelta(days=1)
        return sign * Fraction(total_seconds, 60)

    def add_work_minutes(
        self, instant: datetime, minutes: Fraction | int | float
    ) -> datetime:
        """Ajoute une durée ouvrée positive en conservant les pauses."""
        remaining = Fraction(minutes)
        if remaining < 0:
            raise ValueError("Une durée ouvrée à ajouter ne peut pas être négative")
        current = self.normalize_start(instant)
        if remaining == 0:
            return current
        while remaining > 0:
            active_end: datetime | None = None
            for start, end in self._bounds(current.date()):
                if start <= current < end:
                    active_end = end
                    break
            if active_end is None:
                current = self.normalize_start(current)
                continue
            available = Fraction(
                int((active_end - current).total_seconds()), 60
            )
            if remaining <= available:
                seconds = remaining * 60
                return current + timedelta(
                    seconds=seconds.numerator / seconds.denominator
                )
            remaining -= available
            current = self.normalize_start(active_end)
        return current


def _minutes(value: Fraction) -> float:
    return round(float(value), 6)


def _duration(task: PlanningTaskInput) -> tuple[Fraction | None, Fraction | None]:
    if task.is_milestone:
        return Fraction(0), Fraction(0)
    values = (
        task.duration_optimistic_minutes,
        task.duration_likely_minutes,
        task.duration_pessimistic_minutes,
    )
    if any(value is None for value in values):
        return None, None
    optimistic, likely, pessimistic = values
    assert optimistic is not None and likely is not None and pessimistic is not None
    expected = Fraction(optimistic + 4 * likely + pessimistic, 6)
    variance = Fraction((pessimistic - optimistic) ** 2, 36)
    return expected, variance


def _blank_task_results(
    tasks: list[PlanningTaskInput],
    durations: dict[str, Fraction | None],
    variances: dict[str, Fraction | None],
) -> tuple[PlanningTaskResult, ...]:
    results = []
    for task in sorted(tasks, key=lambda item: item.id):
        duration = durations.get(task.id)
        variance = variances.get(task.id)
        results.append(
            PlanningTaskResult(
                task_id=task.id,
                title=task.title,
                expected_duration_minutes=(
                    _minutes(duration) if duration is not None else None
                ),
                variance_minutes_squared=(
                    _minutes(variance) if variance is not None else None
                ),
            )
        )
    return tuple(results)


def _cycle_path(adjacency: dict[str, list[str]]) -> list[str]:
    """Retourne un cycle déterministe sans récursion (grands graphes)."""
    state = {node: 0 for node in adjacency}
    parent: dict[str, str] = {}
    for root in sorted(adjacency):
        if state[root] != 0:
            continue
        state[root] = 1
        stack: list[tuple[str, int]] = [(root, 0)]
        while stack:
            node, index = stack[-1]
            neighbours = adjacency[node]
            if index >= len(neighbours):
                state[node] = 2
                stack.pop()
                continue
            neighbour = neighbours[index]
            stack[-1] = (node, index + 1)
            if state[neighbour] == 0:
                parent[neighbour] = node
                state[neighbour] = 1
                stack.append((neighbour, 0))
                continue
            if state[neighbour] == 1:
                path = [node]
                while path[-1] != neighbour:
                    path.append(parent[path[-1]])
                path.reverse()
                path.append(neighbour)
                return path
    return []


def _topological_order(
    task_ids: set[str], dependencies: list[PlanningDependencyInput]
) -> tuple[list[str], dict[str, list[PlanningDependencyInput]]]:
    outgoing: dict[str, list[PlanningDependencyInput]] = {
        task_id: [] for task_id in task_ids
    }
    indegree = {task_id: 0 for task_id in task_ids}
    for dependency in dependencies:
        outgoing[dependency.predecessor_task_id].append(dependency)
        indegree[dependency.successor_task_id] += 1
    for edges in outgoing.values():
        edges.sort(
            key=lambda edge: (
                edge.successor_task_id,
                edge.kind,
                edge.lag_minutes,
            )
        )
    ready = [task_id for task_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        task_id = heapq.heappop(ready)
        order.append(task_id)
        for edge in outgoing[task_id]:
            indegree[edge.successor_task_id] -= 1
            if indegree[edge.successor_task_id] == 0:
                heapq.heappush(ready, edge.successor_task_id)
    return order, outgoing


def _edge_weight(
    dependency: PlanningDependencyInput, durations: dict[str, Fraction]
) -> Fraction:
    predecessor_duration = durations[dependency.predecessor_task_id]
    successor_duration = durations[dependency.successor_task_id]
    lag = Fraction(dependency.lag_minutes)
    if dependency.kind == "finish_start":
        return predecessor_duration + lag
    if dependency.kind == "start_start":
        return lag
    if dependency.kind == "finish_finish":
        return predecessor_duration - successor_duration + lag
    return -successor_duration + lag


def calculate_schedule(
    tasks: list[PlanningTaskInput],
    dependencies: list[PlanningDependencyInput],
    *,
    starts_at: datetime | None,
    timezone: str = "Europe/Paris",
) -> PlanningResult:
    """Valide puis calcule PERT/CPM, sans accès réseau ni base de données."""
    tasks = sorted(tasks, key=lambda item: item.id)
    dependencies = sorted(
        dependencies,
        key=lambda item: (
            item.predecessor_task_id,
            item.successor_task_id,
            item.kind,
            item.lag_minutes,
        ),
    )
    errors: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    task_ids = [task.id for task in tasks]
    unique_ids = set(task_ids)
    if len(unique_ids) != len(task_ids):
        errors.append("Deux tâches portent le même identifiant")
    if not tasks:
        missing.append("project.tasks")

    try:
        calendar = WorkCalendar(timezone)
    except ValueError as exc:
        calendar = WorkCalendar()
        errors.append(str(exc))

    durations_nullable: dict[str, Fraction | None] = {}
    variances_nullable: dict[str, Fraction | None] = {}
    valid_constraints = {
        "start_no_earlier",
        "finish_no_later",
        "fixed_start",
        "fixed_finish",
    }
    for task in tasks:
        values = (
            task.duration_optimistic_minutes,
            task.duration_likely_minutes,
            task.duration_pessimistic_minutes,
        )
        if not 0 <= task.progress_percent <= 100:
            errors.append(f"Tâche {task.id} : progression hors de 0 à 100")
        if task.is_milestone:
            if any(value not in (None, 0) for value in values):
                errors.append(f"Tâche {task.id} : un jalon doit avoir une durée nulle")
        else:
            names = (
                "duration_optimistic_minutes",
                "duration_likely_minutes",
                "duration_pessimistic_minutes",
            )
            for name, value in zip(names, values, strict=True):
                if value is None:
                    missing.append(f"tasks.{task.id}.{name}")
                elif value <= 0:
                    errors.append(f"Tâche {task.id} : {name} doit être strictement positif")
            if all(value is not None for value in values):
                optimistic, likely, pessimistic = values
                assert optimistic is not None and likely is not None
                assert pessimistic is not None
                if not optimistic <= likely <= pessimistic:
                    errors.append(
                        f"Tâche {task.id} : les durées doivent vérifier "
                        "optimiste <= probable <= pessimiste"
                    )
        if (task.constraint_type is None) != (task.constraint_at is None):
            errors.append(
                f"Tâche {task.id} : le type et la date de contrainte sont indissociables"
            )
        if task.constraint_type is not None and task.constraint_type not in valid_constraints:
            errors.append(f"Tâche {task.id} : contrainte inconnue {task.constraint_type}")
        if task.constraint_at is not None and task.constraint_at.tzinfo is None:
            errors.append(f"Tâche {task.id} : la contrainte doit porter un fuseau horaire")
        duration, variance = _duration(task)
        durations_nullable[task.id] = duration
        variances_nullable[task.id] = variance

    edge_keys: set[tuple[str, str, str]] = set()
    valid_kinds = {"finish_start", "start_start", "finish_finish", "start_finish"}
    for dependency in dependencies:
        predecessor = dependency.predecessor_task_id
        successor = dependency.successor_task_id
        if predecessor not in unique_ids or successor not in unique_ids:
            errors.append(
                f"Dépendance {predecessor} -> {successor} : tâche absente ou hors projet"
            )
            continue
        if predecessor == successor:
            errors.append(f"Dépendance {predecessor} : une tâche ne peut pas se précéder")
        if dependency.kind not in valid_kinds:
            errors.append(
                f"Dépendance {predecessor} -> {successor} : type inconnu {dependency.kind}"
            )
        if abs(dependency.lag_minutes) > MAX_LAG_MINUTES:
            errors.append(
                f"Dépendance {predecessor} -> {successor} : décalage hors limite"
            )
        key = (predecessor, successor, dependency.kind)
        if key in edge_keys:
            errors.append(
                f"Dépendance {predecessor} -> {successor} ({dependency.kind}) dupliquée"
            )
        edge_keys.add(key)

    usable_dependencies = [
        dependency
        for dependency in dependencies
        if dependency.predecessor_task_id in unique_ids
        and dependency.successor_task_id in unique_ids
        and dependency.predecessor_task_id != dependency.successor_task_id
        and dependency.kind in valid_kinds
        and abs(dependency.lag_minutes) <= MAX_LAG_MINUTES
    ]
    order, outgoing = _topological_order(unique_ids, usable_dependencies)
    if len(order) != len(unique_ids):
        adjacency = {
            task_id: [edge.successor_task_id for edge in outgoing[task_id]]
            for task_id in unique_ids
        }
        cycle = _cycle_path(adjacency)
        errors.append("Cycle de dépendances : " + " -> ".join(cycle))

    if starts_at is None:
        missing.append("project.starts_at")
    elif starts_at.tzinfo is None:
        errors.append("Le début du projet doit porter un fuseau horaire")

    blank_tasks = _blank_task_results(tasks, durations_nullable, variances_nullable)
    if errors:
        return PlanningResult(
            engine_version=ENGINE_VERSION,
            timezone=timezone,
            state="invalid",
            tasks=blank_tasks,
            critical_path=(),
            critical_tasks=(),
            project_duration_minutes=None,
            starts_at=None,
            finishes_at=None,
            forecast=None,
            missing_fields=tuple(sorted(set(missing))),
            warnings=tuple(sorted(set(warnings))),
            errors=tuple(sorted(set(errors))),
        )
    if missing:
        return PlanningResult(
            engine_version=ENGINE_VERSION,
            timezone=timezone,
            state="incomplete",
            tasks=blank_tasks,
            critical_path=(),
            critical_tasks=(),
            project_duration_minutes=None,
            starts_at=None,
            finishes_at=None,
            forecast=None,
            missing_fields=tuple(sorted(set(missing))),
            warnings=tuple(sorted(set(warnings))),
            errors=(),
        )

    assert starts_at is not None
    durations = {
        task_id: value
        for task_id, value in durations_nullable.items()
        if value is not None
    }
    variances = {
        task_id: value
        for task_id, value in variances_nullable.items()
        if value is not None
    }
    project_start = calendar.normalize_start(starts_at)
    if project_start != starts_at.astimezone(calendar.timezone):
        warnings.append(
            "Le début du projet a été avancé au prochain instant ouvré"
        )

    lower_bounds = {task.id: Fraction(0) for task in tasks}
    upper_bounds: dict[str, Fraction | None] = {task.id: None for task in tasks}
    for task in tasks:
        if task.constraint_type is None or task.constraint_at is None:
            continue
        constraint_at = task.constraint_at.astimezone(calendar.timezone)
        if task.constraint_type == "fixed_start" and not calendar.is_fixed_start(
            constraint_at
        ):
            errors.append(
                f"Tâche {task.id} : le début fixe est hors horaires ouvrés"
            )
            continue
        if task.constraint_type == "fixed_finish" and not calendar.is_fixed_finish(
            constraint_at
        ):
            errors.append(
                f"Tâche {task.id} : la fin fixe est hors horaires ouvrés"
            )
            continue
        offset = calendar.working_minutes_between(project_start, constraint_at)
        if task.constraint_type == "start_no_earlier":
            lower_bounds[task.id] = max(Fraction(0), offset)
        elif task.constraint_type == "finish_no_later":
            upper_bounds[task.id] = offset - durations[task.id]
        elif task.constraint_type == "fixed_start":
            lower_bounds[task.id] = offset
            upper_bounds[task.id] = offset
        else:
            fixed_start = offset - durations[task.id]
            lower_bounds[task.id] = fixed_start
            upper_bounds[task.id] = fixed_start

    if errors:
        return PlanningResult(
            engine_version=ENGINE_VERSION,
            timezone=timezone,
            state="invalid",
            tasks=blank_tasks,
            critical_path=(),
            critical_tasks=(),
            project_duration_minutes=None,
            starts_at=project_start,
            finishes_at=None,
            forecast=None,
            missing_fields=(),
            warnings=tuple(sorted(set(warnings))),
            errors=tuple(sorted(set(errors))),
        )

    incoming: dict[str, list[PlanningDependencyInput]] = {
        task.id: [] for task in tasks
    }
    for dependency in usable_dependencies:
        incoming[dependency.successor_task_id].append(dependency)
    for edges in incoming.values():
        edges.sort(key=lambda edge: (edge.predecessor_task_id, edge.kind))

    earliest: dict[str, Fraction] = {}
    chosen_predecessor: dict[str, str | None] = {}
    for task_id in order:
        best = lower_bounds[task_id]
        chosen: str | None = None
        for dependency in incoming[task_id]:
            candidate = earliest[dependency.predecessor_task_id] + _edge_weight(
                dependency, durations
            )
            if candidate > best or (
                candidate == best
                and (
                    chosen is None
                    or dependency.predecessor_task_id < chosen
                )
            ):
                best = candidate
                chosen = dependency.predecessor_task_id
        earliest[task_id] = max(Fraction(0), best)
        chosen_predecessor[task_id] = chosen
        upper = upper_bounds[task_id]
        if upper is not None and earliest[task_id] > upper:
            errors.append(
                f"Tâche {task_id} : contrainte incompatible avec ses dépendances"
            )

    if errors:
        return PlanningResult(
            engine_version=ENGINE_VERSION,
            timezone=timezone,
            state="invalid",
            tasks=blank_tasks,
            critical_path=(),
            critical_tasks=(),
            project_duration_minutes=None,
            starts_at=project_start,
            finishes_at=None,
            forecast=None,
            missing_fields=(),
            warnings=tuple(sorted(set(warnings))),
            errors=tuple(sorted(set(errors))),
        )

    project_duration = max(
        (earliest[task.id] + durations[task.id] for task in tasks),
        default=Fraction(0),
    )
    latest = {
        task.id: project_duration - durations[task.id]
        for task in tasks
    }
    for task_id, upper in upper_bounds.items():
        if upper is not None:
            latest[task_id] = min(latest[task_id], upper)
    for task_id in reversed(order):
        for dependency in outgoing[task_id]:
            latest[task_id] = min(
                latest[task_id],
                latest[dependency.successor_task_id]
                - _edge_weight(dependency, durations),
            )
        if latest[task_id] < earliest[task_id]:
            errors.append(
                f"Tâche {task_id} : aucune date ne satisfait toutes les contraintes"
            )

    if errors:
        return PlanningResult(
            engine_version=ENGINE_VERSION,
            timezone=timezone,
            state="invalid",
            tasks=blank_tasks,
            critical_path=(),
            critical_tasks=(),
            project_duration_minutes=None,
            starts_at=project_start,
            finishes_at=None,
            forecast=None,
            missing_fields=(),
            warnings=tuple(sorted(set(warnings))),
            errors=tuple(sorted(set(errors))),
        )

    critical_tasks = tuple(
        task_id for task_id in order if latest[task_id] == earliest[task_id]
    )
    end_task = min(
        (
            task.id
            for task in tasks
            if earliest[task.id] + durations[task.id] == project_duration
        ),
        default=None,
    )
    path: list[str] = []
    cursor = end_task
    while cursor is not None:
        path.append(cursor)
        cursor = chosen_predecessor[cursor]
    path.reverse()

    offsets = {Fraction(0), project_duration}
    for task in tasks:
        task_id = task.id
        offsets.update(
            {
                earliest[task_id],
                earliest[task_id] + durations[task_id],
                latest[task_id],
                latest[task_id] + durations[task_id],
            }
        )
    variance_path = sum((variances[task_id] for task_id in path), Fraction(0))
    standard_deviation = math.sqrt(float(variance_path))
    lower_duration = max(0.0, float(project_duration) - 1.645 * standard_deviation)
    upper_duration = float(project_duration) + 1.645 * standard_deviation
    lower_fraction = Fraction(str(round(lower_duration, 6)))
    upper_fraction = Fraction(str(round(upper_duration, 6)))
    offsets.update({lower_fraction, upper_fraction})

    dates: dict[Fraction, datetime] = {}
    cursor_offset = Fraction(0)
    cursor_date = project_start
    for offset in sorted(offsets):
        cursor_date = calendar.add_work_minutes(cursor_date, offset - cursor_offset)
        dates[offset] = cursor_date
        cursor_offset = offset

    task_by_id = {task.id: task for task in tasks}
    task_results = tuple(
        PlanningTaskResult(
            task_id=task_id,
            title=task_by_id[task_id].title,
            expected_duration_minutes=_minutes(durations[task_id]),
            variance_minutes_squared=_minutes(variances[task_id]),
            earliest_start_offset_minutes=_minutes(earliest[task_id]),
            earliest_finish_offset_minutes=_minutes(
                earliest[task_id] + durations[task_id]
            ),
            latest_start_offset_minutes=_minutes(latest[task_id]),
            latest_finish_offset_minutes=_minutes(
                latest[task_id] + durations[task_id]
            ),
            total_float_minutes=_minutes(latest[task_id] - earliest[task_id]),
            is_critical=latest[task_id] == earliest[task_id],
            earliest_start_at=dates[earliest[task_id]],
            earliest_finish_at=dates[earliest[task_id] + durations[task_id]],
            latest_start_at=dates[latest[task_id]],
            latest_finish_at=dates[latest[task_id] + durations[task_id]],
        )
        for task_id in order
    )
    forecast = PlanningForecast(
        standard_deviation_minutes=round(standard_deviation, 6),
        lower_duration_minutes=round(lower_duration, 6),
        upper_duration_minutes=round(upper_duration, 6),
        expected_finish_at=dates[project_duration],
        lower_finish_at=dates[lower_fraction],
        upper_finish_at=dates[upper_fraction],
    )
    return PlanningResult(
        engine_version=ENGINE_VERSION,
        timezone=timezone,
        state="complete",
        tasks=task_results,
        critical_path=tuple(path),
        critical_tasks=critical_tasks,
        project_duration_minutes=_minutes(project_duration),
        starts_at=project_start,
        finishes_at=dates[project_duration],
        forecast=forecast,
        missing_fields=(),
        warnings=tuple(sorted(set(warnings))),
        errors=(),
    )
