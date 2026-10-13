"""
FeedbackLog model storing user review feedback and synthesized prompt weights.

This table records candidate critiques, suggestions, and corrections submitted
following mock interviews or CV reviews. It provides an audit trail of how user
feedback was translated into quantitative prompt weights (such as technical_depth
or brevity) by the Reflector agent.

Thread & User Linkage:
The ``thread_id`` column links each log entry directly to the LangGraph
execution thread saved in ``PostgresSaver``.
The ``user_profile_id`` foreign key links feedback directly to the candidate entity.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class FeedbackLog(Base, UUIDMixin, TimestampMixin):
    """
    Stores user reviews and Reflector agent synthesized prompt weight adjustments.

    Attributes:
        user_profile_id: Optional foreign key to candidate UserProfile.
        thread_id: Conversational thread session where feedback was submitted.
        user_feedback: Raw critique or guidance text from the candidate.
        prompt_weight_adjustments: JSON dictionary of adjusted directive parameters.
        user_profile: Relationship to candidate entity.
    """

    __tablename__ = "feedback_log"

    user_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profile.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    thread_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_weight_adjustments: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationship
    user_profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile",
        back_populates="feedback_logs",
    )
