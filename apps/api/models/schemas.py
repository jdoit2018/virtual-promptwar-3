"""
apps/api/models/schemas.py
Pydantic validation schemas for API inputs and outputs.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from models.db_models import (
    ChallengeDifficulty,
    ChallengeStatus,
    NotificationChannel,
    NotificationType,
)

# ── Common Config ────────────────────────────────────────────────────────────

class OurBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── User Schemas ──────────────────────────────────────────────────────────────

class UserBase(OurBaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    region_code: str = "GLOBAL"


class UserResponse(UserBase):
    id: UUID
    current_streak: int
    highest_streak: int
    created_at: datetime
    updated_at: datetime


# ── Baseline Schemas ──────────────────────────────────────────────────────────

class QuizResponses(OurBaseModel):
    # Part 1: Housing & Energy
    property_type: str = "apartment"  # 'detached', 'townhouse', 'apartment'
    heating_type: str = "electricity_heat_pump"  # 'gas_oil', 'electricity_heat_pump', 'renewables_solar'
    household_size: int = 1  # 1, 2, 3, 4 (representing 4+)

    # Part 2: Transportation
    transport_mode: str = "pedestrian_bicycle"  # 'gas_car', 'ev', 'public_transit', 'pedestrian_bicycle'
    weekly_mileage: str = "low"  # 'low', 'medium', 'high'
    flights_profile: str = "none"  # 'none', 'short_haul', 'long_haul', 'frequent'

    # Part 3: Diet
    diet_type: str = "omnivore"  # 'heavy_meat', 'omnivore', 'poultry_pescatarian', 'vegetarian', 'vegan'

    # Part 4: Consumption
    fashion_frequency: str = "rarely"  # 'rarely', 'occasionally', 'frequently'
    electronics_frequency: str = "none"  # 'none', 'one', 'two_or_more'


class BaselineCreate(OurBaseModel):
    quiz_responses: QuizResponses


class BaselineResponse(OurBaseModel):
    id: UUID
    user_id: UUID
    total_co2e: float
    housing_co2e: float | None
    transport_co2e: float | None
    diet_co2e: float | None
    consumption_co2e: float | None
    quiz_responses: dict[str, Any] | None
    is_current: bool
    created_at: datetime


# ── Goal Schemas ──────────────────────────────────────────────────────────────

class GoalCreate(OurBaseModel):
    target_co2e: float
    target_year: int
    reduction_pct: float | None = None


class GoalResponse(OurBaseModel):
    id: UUID
    user_id: UUID
    baseline_id: UUID | None
    target_co2e: float
    reduction_pct: float | None
    target_year: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Daily Log Schemas ─────────────────────────────────────────────────────────

class LogCreate(OurBaseModel):
    log_date: date
    category: str
    activity_type: str
    quantity: float
    log_metadata: dict[str, Any] | None = Field(None, alias="metadata")


class LogResponse(OurBaseModel):
    id: UUID
    user_id: UUID
    log_date: date
    category: str
    activity_type: str
    emission_factor_id: int | None
    quantity: float
    total_co2e: float | None
    is_estimated: bool
    log_metadata: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def from_orm_custom(cls, data: Any) -> Any:
        if not isinstance(data, dict) and hasattr(data, "log_metadata"):
            return {
                "id": data.id,
                "user_id": data.user_id,
                "log_date": data.log_date,
                "category": data.category,
                "activity_type": data.activity_type,
                "emission_factor_id": data.emission_factor_id,
                "quantity": data.quantity,
                "total_co2e": data.total_co2e,
                "is_estimated": data.is_estimated,
                "metadata": data.log_metadata,
                "created_at": data.created_at
            }
        return data



class LogsSummaryWeekly(OurBaseModel):
    week_start: date
    week_end: date
    total_co2e: float
    breakdown: dict[str, float]  # category -> total_co2e


# ── Challenge Schemas ─────────────────────────────────────────────────────────

class EcoChallengeResponse(OurBaseModel):
    id: UUID
    title: str
    description: str
    category: str
    difficulty: ChallengeDifficulty
    target_value: int
    metric_type: str
    co2e_reward: float | None
    is_active: bool
    created_at: datetime


class UserChallengeResponse(OurBaseModel):
    id: UUID
    user_id: UUID
    challenge_id: UUID
    status: ChallengeStatus
    progress: int
    started_at: datetime
    completed_at: datetime | None
    failed_at: datetime | None
    challenge: EcoChallengeResponse | None = None


# ── Notification / Register token Schemas ─────────────────────────────────────

class FCMTokenRegister(OurBaseModel):
    token: str


class NotificationResponse(OurBaseModel):
    id: UUID
    user_id: UUID
    type: NotificationType
    channel: NotificationChannel
    title: str
    body: str | None = None
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    read_at: datetime | None = None
    notification_metadata: dict[str, Any] | None = Field(None, alias="metadata")
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def from_orm_custom(cls, data: Any) -> Any:
        if not isinstance(data, dict) and hasattr(data, "notification_metadata"):
            return {
                "id": data.id,
                "user_id": data.user_id,
                "type": data.type,
                "channel": data.channel,
                "title": data.title,
                "body": data.body,
                "scheduled_at": data.scheduled_at,
                "sent_at": data.sent_at,
                "read_at": data.read_at,
                "metadata": data.notification_metadata,
                "created_at": data.created_at
            }
        return data
