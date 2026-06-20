"""
apps/api/models/db_models.py
SQLAlchemy models matching the database schema.
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

# ── Enumerations (Python equivalents) ─────────────────────────────────────────

class AuthProviderType(str, enum.Enum):
    email = "email"
    google = "google"
    apple = "apple"


class ChallengeStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    failed = "failed"


class ChallengeDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class NotificationType(str, enum.Enum):
    reminder = "reminder"
    streak_warning = "streak_warning"
    achievement = "achievement"
    weekly_digest = "weekly_digest"
    challenge_update = "challenge_update"


class NotificationChannel(str, enum.Enum):
    push = "push"
    email = "email"
    in_app = "in_app"


class OrgRole(str, enum.Enum):
    admin = "admin"
    member = "member"


# ── Database Models ────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[AuthProviderType] = mapped_column(
        ENUM(AuthProviderType, name="auth_provider_type", create_type=False),
        default=AuthProviderType.email,
        server_default="email"
    )
    provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    region_code: Mapped[str] = mapped_column(String(10), default="GLOBAL", server_default="GLOBAL")
    current_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    highest_streak: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    # Relationships
    baselines: Mapped[list["Baseline"]] = relationship("Baseline", back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["UserGoal"]] = relationship("UserGoal", back_populates="user", cascade="all, delete-orphan")
    logs: Mapped[list["DailyLog"]] = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")
    challenges: Mapped[list["UserChallenge"]] = relationship("UserChallenge", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    co2e_per_unit: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    region_code: Mapped[str] = mapped_column(String(10), default="GLOBAL", server_default="GLOBAL")
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        UniqueConstraint("activity_type", "region_code", name="unique_activity_region"),
    )


class Baseline(Base):
    __tablename__ = "baselines"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_co2e: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    housing_co2e: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    transport_co2e: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    diet_co2e: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    consumption_co2e: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    quiz_responses: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, server_default="TRUE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="baselines")


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    baseline_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("baselines.id"), nullable=True)
    target_co2e: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    reduction_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="TRUE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    emission_factor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("emission_factors.id"), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_co2e: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="FALSE")
    log_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="logs")

    __table_args__ = (
        UniqueConstraint("user_id", "log_date", "activity_type", name="unique_user_date_activity"),
    )


class EcoChallenge(Base):
    __tablename__ = "eco_challenges"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[ChallengeDifficulty] = mapped_column(
        ENUM(ChallengeDifficulty, name="challenge_difficulty", create_type=False),
        default=ChallengeDifficulty.medium,
        server_default="medium"
    )
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    co2e_reward: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="TRUE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    user_enrolments: Mapped[list["UserChallenge"]] = relationship("UserChallenge", back_populates="challenge", cascade="all, delete-orphan")


class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    challenge_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("eco_challenges.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ChallengeStatus] = mapped_column(
        ENUM(ChallengeStatus, name="challenge_status", create_type=False),
        default=ChallengeStatus.active,
        server_default="active"
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="challenges")
    challenge: Mapped["EcoChallenge"] = relationship("EcoChallenge", back_populates="user_enrolments")

    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="unique_user_challenge"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        ENUM(NotificationType, name="notification_type", create_type=False),
        nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        ENUM(NotificationChannel, name="notification_channel", create_type=False),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(String, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

