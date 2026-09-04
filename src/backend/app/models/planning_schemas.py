"""Contrats HTTP du planning PERT/CPM (P-039)."""

from datetime import datetime
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CalculateScheduleRequest(BaseModel):
    """Paramètres explicites d'un calcul ; aucune date n'est inventée."""

    model_config = ConfigDict(extra="forbid")

    starts_at: datetime | None = None
    timezone: str = "Europe/Paris"

    @model_validator(mode="after")
    def _validate_calendar(self) -> Self:
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Fuseau horaire IANA invalide") from exc
        if self.starts_at is not None and self.starts_at.tzinfo is None:
            raise ValueError("starts_at doit porter un fuseau horaire")
        return self


class PlanningTaskResponse(BaseModel):
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


class PlanningForecastResponse(BaseModel):
    standard_deviation_minutes: float
    lower_duration_minutes: float
    upper_duration_minutes: float
    expected_finish_at: datetime
    lower_finish_at: datetime
    upper_finish_at: datetime


class ProjectScheduleResponse(BaseModel):
    snapshot_id: str
    project_id: str
    engine_version: str
    timezone: str
    input_hash: str = Field(min_length=64, max_length=64)
    calculated_at: datetime
    state: Literal["complete", "incomplete", "invalid"]
    tasks: list[PlanningTaskResponse]
    critical_path: list[str]
    critical_tasks: list[str]
    project_duration_minutes: float | None
    starts_at: datetime | None
    finishes_at: datetime | None
    forecast: PlanningForecastResponse | None
    missing_fields: list[str]
    warnings: list[str]
    errors: list[str]
    reused_snapshot: bool = False
