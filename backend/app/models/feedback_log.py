"""
FeedbackLog model storing user review feedback and synthesized prompt weights.

This table records candidate critiques, suggestions, and corrections submitted
following mock interviews or CV reviews. It provides an audit trail of how user
feedback was translated into quantitative prompt weights (such as technical_depth
or brevity) by the Reflector agent.

Thread Linkage:
The ``thread_id`` column links each log entry directly to the LangGraph
execution thread saved in ``PostgresSaver``, allowing analysts or developers to
retrace the exact conversational turns that led to specific user feedback.
"""

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class FeedbackLog(Base, UUIDMixin, TimestampMixin):
    """
    Stores user reviews and Reflector agent synthesized prompt weight adjustments.

    Attributes:
        thread_id: Conversational thread session where feedback was submitted.
        user_feedback: Raw critique or guidance text from the candidate.
        prompt_weight_adjustments: JSON dictionary of adjusted directive parameters.
    """

    __tablename__ = "feedback_log"

    thread_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    user_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_weight_adjustments: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
