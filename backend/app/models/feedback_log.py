"""FeedbackLog model storing user review feedback and synthesized prompt weights."""

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class FeedbackLog(Base, UUIDMixin, TimestampMixin):
    """Stores user reviews and Reflector agent synthesized prompt weight adjustments."""

    __tablename__ = "feedback_log"

    thread_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_weight_adjustments: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
